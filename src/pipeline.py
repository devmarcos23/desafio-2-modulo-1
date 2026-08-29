"""Orquestração do processamento ponta a ponta."""

from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import json
import logging
import re

import pandas as pd
from sqlalchemy import select

from .config import resolve
from .database import create_session_factory, session_scope, find_by_protocol
from .models import Documento, Atendimento, Chunk, ErroProcessamento
from .pdf_processor import extract_pdf_pages
from .ocr_processor import ocr_page
from .validation import extract_fields, validate_record, clean_text
from .text_processor import preprocess, split_chunks, metadata_json
from .analytics import export_results, generate_charts


def configure_logging(path: Path) -> None:
    """Configura logging em arquivo e no terminal."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(
                path,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def split_records(page_text: str) -> list[str]:
    """
    Divide uma página em atendimentos individuais.

    O OCR pode produzir tanto:

        Protocolo AT-088

    quanto:

        Protocolo Protocolo?

    O segundo caso representa um protocolo não reconhecido,
    mas ainda assim deve iniciar um novo registro.
    """

    texto = clean_text(page_text)

    pattern = re.compile(
        r"(?=\bProtocolo\s+(?:AT-\d{3}\b|Protocolo\?))",
        flags=re.IGNORECASE,
    )

    partes = pattern.split(texto)

    registros: list[str] = []

    for parte in partes:
        parte = parte.strip()

        if not parte:
            continue

        if re.search(
            r"\bProtocolo\s+(?:AT-\d{3}\b|Protocolo\?)",
            parte,
            flags=re.IGNORECASE,
        ):
            registros.append(parte)

    return registros


def _database_url(root: Path, url: str) -> str:
    """Resolve corretamente URLs relativas do SQLite."""

    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative_path = url[len("sqlite:///"):]

        return "sqlite:///" + str(
            root / relative_path
        )

    return url


def _registrar_erro_validacao(
    session,
    documento_id: int,
    pagina: int,
    protocolo: str,
    classification: str,
    reasons: list[str],
) -> None:
    """Registra problemas de validação sem descartar o atendimento."""

    if classification not in {
        "invalido",
        "incompleto",
    }:
        return

    mensagem = (
        f"{protocolo}: "
        f"{';'.join(reasons)}"
        if reasons
        else protocolo
    )

    session.add(
        ErroProcessamento(
            documento_id=documento_id,
            pagina=pagina,
            etapa="validacao",
            tipo=classification,
            mensagem=mensagem,
        )
    )

    logging.warning(
        "Registro %s preservado: %s p.%s - %s",
        classification,
        protocolo,
        pagina,
        ";".join(reasons) or "sem motivo informado",
    )


def process_all(
    cfg: dict,
    reprocessar: bool = False,
) -> pd.DataFrame:
    """
    Processa todos os PDFs, extrai os atendimentos,
    valida, persiste no SQLite e cria os chunks.

    Registros válidos, incompletos e inválidos são preservados
    quando possuem dados suficientes para identificação.

    Registros duplicados são registrados como erro e não são
    inseridos novamente.
    """

    root = Path(cfg["_root"])

    # ---------------------------------------------------------
    # SAÍDA
    # ---------------------------------------------------------

    output = resolve(
        root,
        cfg["saida"]["diretorio"],
    )

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    configure_logging(
        output / cfg["saida"]["log"]
    )

    # ---------------------------------------------------------
    # CATEGORIAS
    # ---------------------------------------------------------

    categories = json.loads(
        (
            root
            / "data"
            / "auxiliares"
            / "categorias.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    # ---------------------------------------------------------
    # BANCO
    # ---------------------------------------------------------

    db_url = _database_url(
        root,
        cfg["banco"]["url"],
    )

    factory = create_session_factory(
        db_url
    )

    # ---------------------------------------------------------
    # PDFs
    # ---------------------------------------------------------

    pdf_dir = resolve(
        root,
        cfg["entrada"]["diretorio_pdfs"],
    )

    rows: list[dict] = []

    # ---------------------------------------------------------
    # PROCESSAMENTO
    # ---------------------------------------------------------

    with session_scope(factory) as session:

        for pdf in sorted(
            pdf_dir.glob(
                cfg["entrada"]["padrao"]
            )
        ):

            logging.info(
                "Processando PDF: %s",
                pdf.name,
            )

            # -------------------------------------------------
            # HASH
            # -------------------------------------------------

            digest = sha256(
                pdf.read_bytes()
            ).hexdigest()

            # -------------------------------------------------
            # EXTRAÇÃO DIRETA
            # -------------------------------------------------

            page_data = extract_pdf_pages(
                pdf,
                cfg["ocr"][
                    "min_caracteres_extracao_direta"
                ],
            )

            documento_existente = session.scalar(
                select(Documento).where(
                    Documento.hash_sha256 == digest
                )
            )

            # -------------------------------------------------
            # DOCUMENTO JÁ PROCESSADO
            # -------------------------------------------------

            if documento_existente and not reprocessar:

                logging.info(
                    "Documento já processado; ignorando: %s",
                    pdf.name,
                )

                continue

            # -------------------------------------------------
            # REPROCESSAMENTO
            # -------------------------------------------------

            if documento_existente and reprocessar:

                logging.info(
                    "Reprocessando documento: %s",
                    pdf.name,
                )

                session.delete(
                    documento_existente
                )

                session.flush()

            # -------------------------------------------------
            # DOCUMENTO
            # -------------------------------------------------

            doc = Documento(
                nome_arquivo=pdf.name,
                hash_sha256=digest,
                total_paginas=len(page_data),
                metodo=(
                    "ocr"
                    if page_data
                    and all(
                        p["metodo"] == "ocr_pendente"
                        for p in page_data
                    )
                    else "extracao_direta"
                ),
            )

            session.add(doc)
            session.flush()

            logging.info(
                "Documento registrado: %s",
                pdf.name,
            )

            # -------------------------------------------------
            # PÁGINAS
            # -------------------------------------------------

            for page in page_data:

                text = page["texto"]

                # ---------------------------------------------
                # OCR
                # ---------------------------------------------

                if page["metodo"] == "ocr_pendente":

                    try:

                        logging.info(
                            "Executando OCR: %s - página %s",
                            pdf.name,
                            page["pagina"],
                        )

                        text = ocr_page(
                            pdf,
                            page["pagina"],
                            cfg["ocr"]["dpi"],
                            cfg["ocr"]["idioma"],
                        )

                        page["metodo"] = "ocr"

                        logging.info(
                            "OCR concluído: %s - página %s",
                            pdf.name,
                            page["pagina"],
                        )

                    except Exception as exc:

                        session.add(
                            ErroProcessamento(
                                documento_id=doc.id,
                                pagina=page["pagina"],
                                etapa="ocr",
                                tipo=type(exc).__name__,
                                mensagem=str(exc),
                            )
                        )

                        logging.exception(
                            "OCR falhou: %s p.%s",
                            pdf.name,
                            page["pagina"],
                        )

                        continue

                # ---------------------------------------------
                # SEPARAÇÃO DOS ATENDIMENTOS
                # ---------------------------------------------

                registros = split_records(text)

                logging.info(
                    "Registros encontrados em %s página %s: %s",
                    pdf.name,
                    page["pagina"],
                    len(registros),
                )

                # ---------------------------------------------
                # REGISTROS
                # ---------------------------------------------

                for raw in registros:

                    fields = extract_fields(raw)

                    classification, reasons, normalized = (
                        validate_record(
                            fields,
                            categories,
                        )
                    )

                    protocolo = (
                        normalized.get("protocolo")
                        or ""
                    ).strip().upper()

                    # -----------------------------------------
                    # PROTOCOLO
                    # -----------------------------------------

                    if not protocolo:

                        protocolo = (
                            f"INVALIDO-{doc.id}-"
                            f"{page['pagina']}-"
                            f"{len(rows) + 1}"
                        )

                    # -----------------------------------------
                    # DUPLICIDADE
                    # -----------------------------------------

                    if (
                        protocolo.startswith("AT-")
                        and find_by_protocol(
                            session,
                            protocolo,
                        )
                    ):

                        classification = "duplicado"

                        if (
                            "protocolo_duplicado"
                            not in reasons
                        ):
                            reasons.append(
                                "protocolo_duplicado"
                            )

                        logging.warning(
                            "Registro duplicado: %s",
                            protocolo,
                        )

                    # -----------------------------------------
                    # CATEGORIA
                    # -----------------------------------------

                    categoria = (
                        normalized.get(
                            "categoria_normalizada"
                        )
                        or fields.get("categoria")
                        or None
                    )

                    # -----------------------------------------
                    # LINHA DE EXPORTAÇÃO
                    # -----------------------------------------

                    row = {
                        **fields,
                        "protocolo": protocolo,
                        "categoria": categoria,
                        "data": normalized.get(
                            "data_obj"
                        ),
                        "tempo_minutos": normalized.get(
                            "tempo_obj"
                        ),
                        "classificacao": classification,
                        "motivos": ";".join(reasons),
                        "documento": pdf.name,
                        "pagina": page["pagina"],
                        "metodo": page["metodo"],
                    }

                    rows.append(row)

                    # -----------------------------------------
                    # ERROS DE VALIDAÇÃO
                    # -----------------------------------------
                    #
                    # IMPORTANTE:
                    #
                    # Não usamos continue aqui.
                    #
                    # O registro continua para o banco e para
                    # o ChromaDB.
                    # -----------------------------------------

                    _registrar_erro_validacao(
                        session=session,
                        documento_id=doc.id,
                        pagina=page["pagina"],
                        protocolo=protocolo,
                        classification=classification,
                        reasons=reasons,
                    )

                    # -----------------------------------------
                    # DUPLICADO
                    # -----------------------------------------

                    if classification == "duplicado":

                        session.add(
                            ErroProcessamento(
                                documento_id=doc.id,
                                pagina=page["pagina"],
                                etapa="deduplicacao",
                                tipo="Duplicidade",
                                mensagem=protocolo,
                            )
                        )

                        continue

                    # -----------------------------------------
                    # ATENDIMENTO
                    # -----------------------------------------

                    item = Atendimento(
                        documento_id=doc.id,
                        pagina=page["pagina"],
                        protocolo=protocolo,
                        data=normalized.get(
                            "data_obj"
                        ),
                        solicitante=fields.get(
                            "solicitante"
                        ),
                        email=fields.get(
                            "email"
                        ),
                        categoria=categoria,
                        descricao=fields.get(
                            "descricao"
                        ),
                        solucao=fields.get(
                            "solucao"
                        ),
                        tempo_minutos=normalized.get(
                            "tempo_obj"
                        ),
                        status=fields.get(
                            "status"
                        ),
                        cep=fields.get(
                            "cep"
                        ),
                        municipio=fields.get(
                            "municipio"
                        ),
                        uf=fields.get(
                            "uf"
                        ),
                        classificacao=classification,
                        motivos=row["motivos"],
                        texto_original=raw,
                        texto_limpo=preprocess(raw),
                    )

                    session.add(item)
                    session.flush()

                    # -----------------------------------------
                    # CHUNKS
                    # -----------------------------------------

                    chunks = split_chunks(
                        raw,
                        cfg["embeddings"][
                            "tamanho_chunk"
                        ],
                        cfg["embeddings"][
                            "sobreposicao"
                        ],
                    )

                    for idx, content in enumerate(
                        chunks
                    ):

                        meta = {
                            "protocolo": protocolo,
                            "documento": pdf.name,
                            "pagina": page["pagina"],
                            "categoria": categoria or "",
                            "classificacao": classification,
                            "municipio": (
                                fields.get("municipio")
                                or ""
                            ),
                            "uf": (
                                fields.get("uf")
                                or ""
                            ),
                        }

                        session.add(
                            Chunk(
                                atendimento_id=item.id,
                                documento_id=doc.id,
                                pagina=page["pagina"],
                                indice=idx,
                                conteudo=content,
                                metadata_json=metadata_json(
                                    **meta
                                ),
                            )
                        )

    # ---------------------------------------------------------
    # DATAFRAME
    # ---------------------------------------------------------

    df = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # EXPORTAÇÕES
    # ---------------------------------------------------------

    if not df.empty:

        export_results(
            df,
            output,
            cfg["saida"]["csv"],
            cfg["saida"]["indicadores"],
        )

        generate_charts(
            df,
            resolve(
                root,
                cfg["saida"]["graficos"],
            ),
        )

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    logging.info(
        "Processamento concluído. Registros encontrados: %s",
        len(df),
    )

    return df
