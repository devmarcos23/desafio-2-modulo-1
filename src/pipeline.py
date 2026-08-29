"""Orquestração ponta a ponta do processamento dos documentos oficiais."""
from __future__ import annotations

from hashlib import sha256
import json
import logging
from pathlib import Path
import shutil
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .analytics import export_results, generate_charts
from .cep_client import lookup_cep
from .config import resolve
from .database import create_session_factory, find_by_protocol, session_scope
from .models import Atendimento, Chunk, Documento, ErroProcessamento, RegistroProcessado
from .ocr_processor import OCRProcessingError, ocr_page
from .pdf_processor import PDFProcessingError, extract_pdf_pages
from .text_processor import metadata_json, preprocess, split_chunks
from .validation import extract_fields, is_valid_protocol, split_records, validate_record

LOGGER = logging.getLogger(__name__)


def configure_logging(path: Path) -> None:
    """Configura log em arquivo UTF-8 e console sem duplicar handlers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in list(root_logger.handlers):
        if getattr(handler, "_ficdev_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler._ficdev_handler = True  # type: ignore[attr-defined]
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler._ficdev_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def _database_url(cfg: dict[str, Any]) -> str:
    root = Path(cfg["_root"])
    url = str(cfg["banco"]["url"])
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative = url[len("sqlite:///") :]
        return f"sqlite:///{root / relative}"
    return url


def _database_file_from_url(url: str) -> Path | None:
    if not url.startswith("sqlite:///") or url == "sqlite:///:memory:":
        return None
    return Path(url[len("sqlite:///") :])


def reset_generated_storage(cfg: dict[str, Any], include_chroma: bool = True) -> None:
    """Remove banco/índice gerados para uma reconstrução explícita e previsível."""
    db_file = _database_file_from_url(_database_url(cfg))
    if db_file and db_file.exists():
        db_file.unlink()
    if include_chroma:
        chroma = resolve(cfg["_root"], cfg["chromadb"]["diretorio"])
        if chroma.exists():
            shutil.rmtree(chroma)


def _load_categories(cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(cfg["_root"])
    configured = cfg.get("entrada", {}).get("arquivo_categorias")
    candidates = [
        (
            resolve(root, configured)
            if configured
            else root / "data" / "auxiliares" / "categorias.json"
        ),
        root / "data" / "auxiliares_categorias.json",
    ]
    for path in candidates:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    raise FileNotFoundError("Arquivo de categorias não encontrado")


def _document_method(methods: list[str]) -> str:
    unique = set(methods)
    if unique == {"ocr"}:
        return "ocr"
    if unique == {"extracao_direta"}:
        return "extracao_direta"
    return "misto"


def _synthetic_protocol(document_id: int, page: int, order: int) -> str:
    return f"INVALIDO-{document_id}-{page}-{order}"


def _record_validation_error(
    session: Session,
    document_id: int,
    page: int,
    reasons: list[str],
    protocol: str,
) -> None:
    validation_reasons = [
        reason for reason in reasons if reason != "protocolo_duplicado"
    ]
    if not validation_reasons:
        return
    session.add(
        ErroProcessamento(
            documento_id=document_id,
            pagina=page,
            etapa="validacao",
            tipo="InconsistenciaDados",
            mensagem=(
                f"{protocol or 'sem_protocolo'}: "
                f"{';'.join(validation_reasons)}"
            ),
        )
    )


def _records_dataframe(session: Session) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    statement = (
        select(RegistroProcessado, Documento.nome_arquivo)
        .join(Documento, Documento.id == RegistroProcessado.documento_id)
        .order_by(
            Documento.nome_arquivo,
            RegistroProcessado.pagina,
            RegistroProcessado.ordem_pagina,
        )
    )
    for record, filename in session.execute(statement).all():
        rows.append(
            {
                "protocolo": record.protocolo or "",
                "data": record.data.isoformat() if record.data else record.data_texto or "",
                "solicitante": record.solicitante or "",
                "email": record.email or "",
                "categoria": record.categoria or "",
                "descricao": record.descricao or "",
                "solucao": record.solucao or "",
                "tempo_minutos": record.tempo_minutos,
                "status": record.status or "",
                "cep": record.cep or "",
                "municipio": record.municipio or "",
                "uf": record.uf or "",
                "observacoes": record.observacoes or "",
                "classificacao": record.classificacao,
                "motivos": record.motivos or "",
                "documento": filename,
                "pagina": record.pagina,
                "metodo": record.metodo,
            }
        )
    return pd.DataFrame(rows)


def _errors_dataframe(session: Session) -> pd.DataFrame:
    rows = session.execute(
        select(ErroProcessamento, Documento.nome_arquivo)
        .outerjoin(Documento, Documento.id == ErroProcessamento.documento_id)
        .order_by(ErroProcessamento.id)
    ).all()
    return pd.DataFrame(
        [
            {
                "documento": filename or "",
                "pagina": error.pagina,
                "etapa": error.etapa,
                "tipo": error.tipo,
                "mensagem": error.mensagem,
                "registrado_em": error.registrado_em.isoformat(),
            }
            for error, filename in rows
        ]
    )


def _persist_record(
    *,
    session: Session,
    document: Documento,
    page: int,
    order: int,
    method: str,
    raw: str,
    fields: dict[str, str],
    normalized: dict[str, Any],
    classification: str,
    reasons: list[str],
    municipio: str | None,
    uf: str | None,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    protocol = normalized.get("protocolo", "")
    protocol_valid = is_valid_protocol(protocol)
    existing = find_by_protocol(session, protocol) if protocol_valid else None

    if existing is not None:
        classification = "duplicado"
        if "protocolo_duplicado" not in reasons:
            reasons.append("protocolo_duplicado")
        session.add(
            ErroProcessamento(
                documento_id=document.id,
                pagina=page,
                etapa="deduplicacao",
                tipo="Duplicidade",
                mensagem=protocol,
            )
        )
        atendimento_id = existing.id
    else:
        storage_protocol = (
            protocol
            if protocol_valid
            else _synthetic_protocol(document.id, page, order)
        )
        item = Atendimento(
            documento_id=document.id,
            pagina=page,
            protocolo=storage_protocol,
            protocolo_original=protocol or None,
            data=normalized.get("data_obj"),
            solicitante=normalized.get("solicitante") or None,
            email=normalized.get("email") or None,
            categoria=normalized.get("categoria_normalizada") or None,
            descricao=normalized.get("descricao") or None,
            solucao=normalized.get("solucao") or None,
            tempo_minutos=normalized.get("tempo_obj"),
            status=normalized.get("status_normalizado") or None,
            cep=normalized.get("cep") or None,
            municipio=municipio,
            uf=uf,
            observacoes=normalized.get("observacoes") or None,
            classificacao=classification,
            motivos=";".join(reasons),
            texto_original=raw,
            texto_limpo=preprocess(raw),
        )
        session.add(item)
        session.flush()
        atendimento_id = item.id

        for chunk_index, content in enumerate(
            split_chunks(raw, size=chunk_size, overlap=chunk_overlap)
        ):
            metadata = {
                "protocolo": protocol or storage_protocol,
                "documento": document.nome_arquivo,
                "pagina": page,
                "categoria": item.categoria or "",
            }
            session.add(
                Chunk(
                    atendimento_id=item.id,
                    documento_id=document.id,
                    pagina=page,
                    indice=chunk_index,
                    conteudo=content,
                    metadata_json=metadata_json(**metadata),
                )
            )

    session.add(
        RegistroProcessado(
            documento_id=document.id,
            atendimento_id=atendimento_id,
            pagina=page,
            ordem_pagina=order,
            protocolo=protocol or None,
            data_texto=normalized.get("data_texto") or fields.get("data") or None,
            data=normalized.get("data_obj"),
            solicitante=normalized.get("solicitante") or None,
            email=normalized.get("email") or None,
            categoria=normalized.get("categoria_normalizada") or None,
            descricao=normalized.get("descricao") or None,
            solucao=normalized.get("solucao") or None,
            tempo_minutos=normalized.get("tempo_obj"),
            status=normalized.get("status_normalizado") or None,
            cep=normalized.get("cep") or None,
            municipio=municipio,
            uf=uf,
            observacoes=normalized.get("observacoes") or None,
            classificacao=classification,
            motivos=";".join(reasons),
            metodo=method,
            texto_original=raw,
            texto_limpo=preprocess(raw),
        )
    )
    _record_validation_error(session, document.id, page, reasons, protocol)
    if reasons:
        LOGGER.warning(
            "Inconsistência de validação: %s p.%s protocolo=%s motivos=%s",
            document.nome_arquivo,
            page,
            protocol or "sem_protocolo",
            ";".join(reasons),
        )


def process_all(cfg: dict[str, Any], *, reset: bool = False) -> pd.DataFrame:
    """Processa PDFs, persiste dados e reconstrói outputs de forma idempotente."""
    root = Path(cfg["_root"])
    output = resolve(root, cfg["saida"]["diretorio"])
    output.mkdir(parents=True, exist_ok=True)
    configure_logging(output / cfg["saida"]["log"])

    if reset:
        reset_generated_storage(cfg, include_chroma=True)

    categories = _load_categories(cfg)
    factory = create_session_factory(_database_url(cfg))
    pdf_dir = resolve(root, cfg["entrada"]["diretorio_pdfs"])
    if not pdf_dir.is_dir():
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdf_dir}")

    cep_cache: dict[str, dict[str, Any] | None] = {}
    new_documents = 0

    with session_scope(factory) as session:
        for pdf in sorted(pdf_dir.glob(cfg["entrada"]["padrao"])):
            digest = sha256(pdf.read_bytes()).hexdigest()
            existing_by_hash = session.scalar(
                select(Documento).where(Documento.hash_sha256 == digest)
            )
            if existing_by_hash is not None and existing_by_hash.concluido:
                LOGGER.info("Documento já processado; reutilizando histórico: %s", pdf.name)
                continue

            # Reprocessa versão incompleta ou versão anterior com o mesmo nome.
            old_documents = list(
                session.scalars(select(Documento).where(Documento.nome_arquivo == pdf.name)).all()
            )
            for old in old_documents:
                session.delete(old)
            session.flush()

            try:
                page_data = extract_pdf_pages(
                    pdf, cfg["ocr"]["min_caracteres_extracao_direta"]
                )
            except PDFProcessingError as exc:
                LOGGER.exception("Falha ao abrir documento: %s", pdf.name)
                session.add(
                    ErroProcessamento(
                        documento_id=None,
                        pagina=None,
                        etapa="extracao_pdf",
                        tipo=type(exc).__name__,
                        mensagem=f"{pdf.name}: {exc}",
                    )
                )
                continue

            document = Documento(
                nome_arquivo=pdf.name,
                hash_sha256=digest,
                total_paginas=len(page_data),
                paginas_ocr=0,
                metodo="pendente",
                concluido=False,
            )
            session.add(document)
            session.flush()
            new_documents += 1
            LOGGER.info("Processando documento: %s", pdf.name)

            methods: list[str] = []
            document_failed = False
            ocr_pages = 0

            for page in page_data:
                page_number = page["pagina"]
                text = page["texto"]
                method = page["metodo"]

                if page.get("erro_extracao"):
                    session.add(
                        ErroProcessamento(
                            documento_id=document.id,
                            pagina=page_number,
                            etapa="extracao_pdf",
                            tipo="FalhaExtracaoDireta",
                            mensagem=str(page["erro_extracao"]),
                        )
                    )

                if method == "ocr_pendente":
                    try:
                        text = ocr_page(
                            pdf,
                            page_number,
                            cfg["ocr"]["dpi"],
                            cfg["ocr"]["idioma"],
                        )
                        method = "ocr"
                        ocr_pages += 1
                        LOGGER.info("OCR concluído: %s p.%s", pdf.name, page_number)
                    except OCRProcessingError as exc:
                        document_failed = True
                        session.add(
                            ErroProcessamento(
                                documento_id=document.id,
                                pagina=page_number,
                                etapa="ocr",
                                tipo=type(exc).__name__,
                                mensagem=str(exc),
                            )
                        )
                        LOGGER.exception("OCR falhou: %s p.%s", pdf.name, page_number)
                        continue

                methods.append(method)
                records = split_records(text)
                if not records:
                    document_failed = True
                    session.add(
                        ErroProcessamento(
                            documento_id=document.id,
                            pagina=page_number,
                            etapa="segmentacao",
                            tipo="NenhumRegistroIdentificado",
                            mensagem="A página não produziu registros após extração/OCR.",
                        )
                    )
                    LOGGER.warning("Nenhum registro identificado: %s p.%s", pdf.name, page_number)
                    continue

                for order, raw in enumerate(records, start=1):
                    fields = extract_fields(raw)
                    classification, reasons, normalized = validate_record(fields, categories)

                    municipio: str | None = None
                    uf: str | None = None
                    cep = normalized.get("cep", "")
                    if cep and len("".join(ch for ch in cep if ch.isdigit())) == 8:
                        if cep not in cep_cache:
                            cep_cache[cep] = lookup_cep(
                                cep,
                                cfg["api"]["cep_base_url"],
                                cfg["api"]["timeout_segundos"],
                            )
                        location = cep_cache[cep]
                        if location:
                            municipio = location.get("municipio")
                            uf = location.get("uf")

                    _persist_record(
                        session=session,
                        document=document,
                        page=page_number,
                        order=order,
                        method=method,
                        raw=raw,
                        fields=fields,
                        normalized=normalized,
                        classification=classification,
                        reasons=reasons,
                        municipio=municipio,
                        uf=uf,
                        chunk_size=cfg["embeddings"]["tamanho_chunk"],
                        chunk_overlap=cfg["embeddings"]["sobreposicao"],
                    )

            document.paginas_ocr = ocr_pages
            document.metodo = _document_method(methods) if methods else "falha"
            document.concluido = not document_failed
            LOGGER.info(
                "Documento concluído: %s | páginas=%s | OCR=%s | status=%s",
                pdf.name,
                document.total_paginas,
                ocr_pages,
                "ok" if document.concluido else "parcial",
            )

        session.flush()
        dataframe = _records_dataframe(session)
        errors = _errors_dataframe(session)
        documents = list(session.scalars(select(Documento)).all())
        total_pages = sum(item.total_paginas for item in documents)
        ocr_pages = sum(item.paginas_ocr for item in documents)

        export_results(
            dataframe,
            output,
            cfg["saida"]["csv"],
            cfg["saida"]["indicadores"],
            total_documentos=len(documents),
            total_paginas=total_pages,
            paginas_ocr=ocr_pages,
            erros=errors,
        )
        generate_charts(dataframe, resolve(root, cfg["saida"]["graficos"]))

        # O log textual é o principal arquivo de problemas; o banco mantém a forma estruturada.
        LOGGER.info("Indicadores da execução atualizados.")
        LOGGER.info(
            "Processamento concluído: documentos=%s, páginas=%s, "
            "páginas OCR=%s, registros=%s, novos_documentos=%s",
            len(documents),
            total_pages,
            ocr_pages,
            len(dataframe),
            new_documents,
        )
        return dataframe
