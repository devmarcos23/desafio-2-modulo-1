"""Orquestração do processamento ponta a ponta."""

from __future__ import annotations

import json
import logging
import re
from hashlib import sha256
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from .analytics import export_results, generate_charts
from .config import resolve
from .database import (
    create_session_factory,
    find_by_protocol,
    session_scope,
)
from .models import (
    Atendimento,
    Chunk,
    Documento,
    ErroProcessamento,
)
from .ocr_processor import ocr_page
from .pdf_processor import extract_pdf_pages
from .text_processor import (
    metadata_json,
    preprocess,
    split_chunks,
)
from .validation import (
    clean_text,
    extract_fields,
    validate_record,
)


def configure_logging(path: Path) -> None:
    """Configura o log do processamento."""

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
    Divide o texto de uma página em registros de atendimento.

    Formatos esperados:

        Protocolo AT-001
        Protocolo?
    """

    text = clean_text(page_text)

    parts = re.split(
        r"(?=Protocolo\s+(?:AT-\d{3}|PROTOCOLO\?))",
        text,
        flags=re.IGNORECASE,
    )

    return [
        part.strip()
        for part in parts
        if re.search(
            r"Protocolo\s+",
            part,
            flags=re.IGNORECASE,
        )
    ]


def _database_url(cfg: dict, root: Path) -> str:
    """Resolve a URL do banco SQLite."""

    db_url = cfg["banco"]["url"]

    if db_url.startswith("sqlite:/// "):
        return (
            "sqlite:///"
            + str(
                root
                / db_url.removeprefix(
                    "sqlite:/// "
                )
            )
        )

    if (
        db_url.startswith("sqlite:///")
        and not db_url.startswith("sqlite:////")
    ):
        return (
            "sqlite:///"
            + str(
                root
                / db_url[10:]
            )
        )

    return db_url


def _load_categories(root: Path) -> dict:
    """Carrega as categorias auxiliares."""

    categories_path = (
        root
        / "data"
        / "auxiliares"
        / "categorias.json"
    )

    return json.loads(
        categories_path.read_text(
            encoding="utf-8"
        )
    )


def _atendimento_to_row(
    atendimento: Atendimento,
) -> dict:
    """
    Converte um Atendimento SQLAlchemy em registro
    compatível com o DataFrame usado pelo Analytics.
    """

    return {
        "protocolo": atendimento.protocolo,
        "data": atendimento.data,
        "solicitante": atendimento.solicitante,
        "email": atendimento.email,
        "categoria": atendimento.categoria,
        "descricao": atendimento.descricao,
        "solucao": atendimento.solucao,
        "tempo_minutos": atendimento.tempo_minutos,
        "status": atendimento.status,
        "cep": atendimento.cep,
        "municipio": atendimento.municipio,
        "uf": atendimento.uf,
        "classificacao": atendimento.classificacao,
        "motivos": atendimento.motivos,
        "documento": (
            atendimento.documento.nome_arquivo
            if atendimento.documento
            else None
        ),
        "pagina": atendimento.pagina,
        "metodo": (
            atendimento.documento.metodo
            if atendimento.documento
            else None
        ),
    }


def _load_database_data(
    factory,
) -> tuple[pd.DataFrame, pd.DataFrame, int, int, int]:
    """
    Recupera os dados históricos do banco.

    Retorna:

        DataFrame de atendimentos
        DataFrame de erros
        total de documentos
        total de páginas
        total de páginas OCR
    """

    with session_scope(factory) as session:

        # -----------------------------------------------------
        # Documentos
        # -----------------------------------------------------

        documentos = session.scalars(
            select(Documento)
        ).all()

        total_documentos = len(documentos)

        total_paginas = sum(
            int(documento.total_paginas or 0)
            for documento in documentos
        )

        paginas_ocr = sum(
            int(
                getattr(
                    documento,
                    "paginas_ocr",
                    0,
                )
                or 0
            )
            for documento in documentos
        )

        # -----------------------------------------------------
        # Atendimentos
        # -----------------------------------------------------

        atendimentos = session.scalars(
            select(Atendimento)
        ).all()

        rows = [
            _atendimento_to_row(
                atendimento
            )
            for atendimento in atendimentos
        ]

        df = pd.DataFrame(rows)

        # -----------------------------------------------------
        # Erros
        # -----------------------------------------------------

        erros = session.scalars(
            select(ErroProcessamento)
        ).all()

        erros_rows = [
            {
                "tipo": erro.tipo,
                "etapa": erro.etapa,
                "pagina": erro.pagina,
                "mensagem": erro.mensagem,
            }
            for erro in erros
        ]

        erros_df = pd.DataFrame(
            erros_rows
        )

    return (
        df,
        erros_df,
        total_documentos,
        total_paginas,
        paginas_ocr,
    )


def _export_database_indicators(
    factory,
    output: Path,
    cfg: dict,
    root: Path,
) -> pd.DataFrame:
    """
    Gera novamente CSV, indicadores e gráficos
    usando os dados existentes no banco.

    Isso evita que uma execução sem PDFs novos
    gere indicadores zerados.
    """

    (
        df,
        erros_df,
        total_documentos,
        total_paginas,
        paginas_ocr,
    ) = _load_database_data(factory)

    if df.empty:
        logging.warning(
            "Banco sem atendimentos para gerar indicadores."
        )
        return df

    export_results(
        df,
        output,
        cfg["saida"]["csv"],
        cfg["saida"]["indicadores"],
        total_documentos=total_documentos,
        total_paginas=total_paginas,
        paginas_ocr=paginas_ocr,
        erros=erros_df,
    )

    generate_charts(
        df,
        resolve(
            root,
            cfg["saida"]["graficos"],
        ),
    )

    logging.info(
        "Indicadores históricos atualizados: "
        "documentos=%s, páginas=%s, páginas OCR=%s, "
        "registros=%s, erros=%s",
        total_documentos,
        total_paginas,
        paginas_ocr,
        len(df),
        len(erros_df),
    )

    return df


def process_all(cfg: dict) -> pd.DataFrame:
    """
    Executa o processamento completo dos PDFs.

    Fluxo:

        PDF
          ↓
        Extração direta / OCR
          ↓
        Validação
          ↓
        Deduplicação
          ↓
        SQLite
          ↓
        Chunks
          ↓
        CSV + indicadores + gráficos

    Quando todos os documentos já estiverem processados,
    os indicadores são reconstruídos a partir do banco.
    """

    root = Path(cfg["_root"])

    # =========================================================
    # Saída
    # =========================================================

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

    # =========================================================
    # Categorias
    # =========================================================

    categories = _load_categories(root)

    # =========================================================
    # Banco
    # =========================================================

    db_url = _database_url(
        cfg,
        root,
    )

    factory = create_session_factory(
        db_url
    )

    # =========================================================
    # PDFs
    # =========================================================

    pdf_dir = resolve(
        root,
        cfg["entrada"]["diretorio_pdfs"],
    )

    rows: list[dict] = []

    total_documentos = 0
    total_paginas = 0
    paginas_ocr = 0

    # =========================================================
    # Processamento
    # =========================================================

    with session_scope(factory) as session:

        for pdf in sorted(
            pdf_dir.glob(
                cfg["entrada"]["padrao"]
            )
        ):

            logging.info(
                "Processando documento: %s",
                pdf.name,
            )

            # -------------------------------------------------
            # Hash
            # -------------------------------------------------

            digest = sha256(
                pdf.read_bytes()
            ).hexdigest()

            # -------------------------------------------------
            # Extração inicial
            # -------------------------------------------------

            page_data = extract_pdf_pages(
                pdf,
                cfg["ocr"][
                    "min_caracteres_extracao_direta"
                ],
            )

            # -------------------------------------------------
            # Documento já processado
            # -------------------------------------------------

            documento_existente = session.scalar(
                select(Documento).where(
                    Documento.hash_sha256
                    == digest
                )
            )

            if documento_existente:

                logging.info(
                    "Documento já processado; ignorando: %s",
                    pdf.name,
                )

                continue

            # -------------------------------------------------
            # Contadores
            # -------------------------------------------------

            total_documentos += 1
            total_paginas += len(page_data)

            paginas_ocr_documento = 0

            # -------------------------------------------------
            # Método
            # -------------------------------------------------

            method = (
                "ocr"
                if page_data
                and all(
                    page["metodo"]
                    == "ocr_pendente"
                    for page in page_data
                )
                else "extracao_direta"
            )

            # -------------------------------------------------
            # Documento
            # -------------------------------------------------

            doc = Documento(
                nome_arquivo=pdf.name,
                hash_sha256=digest,
                total_paginas=len(
                    page_data
                ),
                paginas_ocr=0,
                metodo=method,
            )

            session.add(doc)
            session.flush()

            # -------------------------------------------------
            # Páginas
            # -------------------------------------------------

            for page in page_data:

                text = page["texto"]

                # =============================================
                # OCR
                # =============================================

                if (
                    page["metodo"]
                    == "ocr_pendente"
                ):

                    try:

                        text = ocr_page(
                            pdf,
                            page["pagina"],
                            cfg["ocr"]["dpi"],
                            cfg["ocr"]["idioma"],
                        )

                        page["metodo"] = "ocr"

                        paginas_ocr += 1
                        paginas_ocr_documento += 1

                        logging.info(
                            "OCR concluído: %s p.%s",
                            pdf.name,
                            page["pagina"],
                        )

                    except Exception as exc:

                        session.add(
                            ErroProcessamento(
                                documento_id=doc.id,
                                pagina=page["pagina"],
                                etapa="ocr",
                                tipo=type(
                                    exc
                                ).__name__,
                                mensagem=str(
                                    exc
                                ),
                            )
                        )

                        logging.exception(
                            "OCR falhou: %s p.%s",
                            pdf.name,
                            page["pagina"],
                        )

                        continue

                # =============================================
                # Registros
                # =============================================

                for raw in split_records(
                    text
                ):

                    # -----------------------------------------
                    # Extração
                    # -----------------------------------------

                    fields = extract_fields(
                        raw
                    )

                    # -----------------------------------------
                    # Validação
                    # -----------------------------------------

                    (
                        classification,
                        reasons,
                        normalized,
                    ) = validate_record(
                        fields,
                        categories,
                    )

                    # -----------------------------------------
                    # Protocolo
                    # -----------------------------------------

                    protocol = (
                        normalized.get(
                            "protocolo"
                        )
                        or f"INVALIDO-{doc.id}-"
                        f"{page['pagina']}-"
                        f"{len(rows) + 1}"
                    )

                    # -----------------------------------------
                    # Deduplicação
                    # -----------------------------------------

                    if find_by_protocol(
                        session,
                        protocol,
                    ):

                        classification = "duplicado"

                        reasons.append(
                            "protocolo_duplicado"
                        )

                    # -----------------------------------------
                    # DataFrame
                    # -----------------------------------------

                    row = {
                        **fields,
                        "protocolo": protocol,
                        "categoria": (
                            normalized.get(
                                "categoria_normalizada"
                            )
                            or fields.get(
                                "categoria"
                            )
                        ),
                        "data": normalized.get(
                            "data_obj"
                        ),
                        "tempo_minutos": normalized.get(
                            "tempo_obj"
                        ),
                        "classificacao": classification,
                        "motivos": ";".join(
                            reasons
                        ),
                        "documento": pdf.name,
                        "pagina": page["pagina"],
                        "metodo": page["metodo"],
                    }

                    rows.append(row)

                    # -----------------------------------------
                    # Duplicado
                    # -----------------------------------------

                    if (
                        classification
                        == "duplicado"
                    ):

                        session.add(
                            ErroProcessamento(
                                documento_id=doc.id,
                                pagina=page["pagina"],
                                etapa="deduplicacao",
                                tipo="Duplicidade",
                                mensagem=protocol,
                            )
                        )

                        continue

                    # -----------------------------------------
                    # Atendimento
                    # -----------------------------------------

                    item = Atendimento(
                        documento_id=doc.id,
                        pagina=page["pagina"],
                        protocolo=protocol,
                        data=normalized.get(
                            "data_obj"
                        ),
                        solicitante=fields.get(
                            "solicitante"
                        ),
                        email=fields.get(
                            "email"
                        ),
                        categoria=row[
                            "categoria"
                        ],
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
                        municipio=None,
                        uf=None,
                        classificacao=classification,
                        motivos=row[
                            "motivos"
                        ],
                        texto_original=raw,
                        texto_limpo=preprocess(
                            raw
                        ),
                    )

                    session.add(item)
                    session.flush()

                    # -----------------------------------------
                    # Chunks
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
                            "protocolo": protocol,
                            "documento": pdf.name,
                            "pagina": page["pagina"],
                            "categoria": (
                                row[
                                    "categoria"
                                ]
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

            # -------------------------------------------------
            # Persiste OCR
            # -------------------------------------------------

            doc.paginas_ocr = (
                paginas_ocr_documento
            )

            logging.info(
                "Documento concluído: %s | páginas=%s | OCR=%s",
                pdf.name,
                len(page_data),
                paginas_ocr_documento,
            )

    # =========================================================
    # DataFrame da execução
    # =========================================================

    df = pd.DataFrame(rows)

    # =========================================================
    # Existem PDFs novos?
    # =========================================================

    if not df.empty:

        (
            _,
            erros_df,
            _,
            _,
            _,
        ) = _load_database_data(
            factory
        )

        export_results(
            df,
            output,
            cfg["saida"]["csv"],
            cfg["saida"]["indicadores"],
            total_documentos=total_documentos,
            total_paginas=total_paginas,
            paginas_ocr=paginas_ocr,
            erros=erros_df,
        )

        generate_charts(
            df,
            resolve(
                root,
                cfg["saida"]["graficos"],
            ),
        )

        logging.info(
            "Indicadores da execução atualizados."
        )

    # =========================================================
    # Não existem PDFs novos
    # =========================================================

    else:

        logging.info(
            "Nenhum documento novo encontrado."
        )

        df = _export_database_indicators(
            factory,
            output,
            cfg,
            root,
        )

        # Recupera os totais históricos para o log
        (
            _,
            _,
            total_documentos_db,
            total_paginas_db,
            paginas_ocr_db,
        ) = _load_database_data(
            factory
        )

        total_documentos = (
            total_documentos_db
        )

        total_paginas = (
            total_paginas_db
        )

        paginas_ocr = (
            paginas_ocr_db
        )

    # =========================================================
    # Log final
    # =========================================================

    logging.info(
        "Processamento concluído: "
        "documentos=%s, páginas=%s, páginas OCR=%s, "
        "registros=%s",
        total_documentos,
        total_paginas,
        paginas_ocr,
        len(df),
    )

    return df