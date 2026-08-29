"""Orquestração do processamento ponta a ponta."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json, logging
import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .config import resolve
from .database import create_session_factory, session_scope, find_by_protocol
from .models import Documento, Atendimento, Chunk, ErroProcessamento
from .pdf_processor import extract_pdf_pages
from .ocr_processor import ocr_page
from .validation import (
    extract_fields,
    is_valid_protocol,
    split_records as split_attendance_records,
    validate_record,
)
from .text_processor import preprocess, split_chunks, metadata_json
from .analytics import export_results, generate_charts

def configure_logging(path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",handlers=[logging.FileHandler(path,encoding="utf-8"),logging.StreamHandler()])

def split_records(page_text: str) -> list[str]:
    """Compatibilidade: delega a segmentação para o módulo de validação."""
    return split_attendance_records(page_text)

def process_all(cfg: dict) -> pd.DataFrame:
    root=Path(cfg["_root"]); output=resolve(root,cfg["saida"]["diretorio"]); output.mkdir(parents=True,exist_ok=True)
    configure_logging(output/cfg["saida"]["log"])
    categories=json.loads((root/"data"/"auxiliares"/"categorias.json").read_text(encoding="utf-8"))
    db_url=cfg["banco"]["url"]
    if db_url.startswith("sqlite:/// "): db_url="sqlite:///"+str(root/db_url.removeprefix("sqlite:/// "))
    elif db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"): db_url="sqlite:///"+str(root/db_url[10:])
    factory=create_session_factory(db_url)
    pdf_dir=resolve(root,cfg["entrada"]["diretorio_pdfs"]); rows=[]
    with session_scope(factory) as session:
        for pdf in sorted(pdf_dir.glob(cfg["entrada"]["padrao"])):
            digest=sha256(pdf.read_bytes()).hexdigest(); page_data=extract_pdf_pages(pdf,cfg["ocr"]["min_caracteres_extracao_direta"])
            if session.scalar(select(Documento).where(Documento.hash_sha256==digest)):
                logging.info("Documento já processado; ignorando: %s",pdf.name)
                continue
            method="ocr" if all(p["metodo"]=="ocr_pendente" for p in page_data) else "extracao_direta"
            doc=Documento(nome_arquivo=pdf.name,hash_sha256=digest,total_paginas=len(page_data),metodo=method); session.add(doc); session.flush()
            for page in page_data:
                text=page["texto"]
                if page.get("erro_extracao"):
                    session.add(
                        ErroProcessamento(
                            documento_id=doc.id,
                            pagina=page["pagina"],
                            etapa="extracao_pdf",
                            tipo="FalhaExtracaoDireta",
                            mensagem=page["erro_extracao"],
                        )
                    )
                if page["metodo"]=="ocr_pendente":
                    try: text=ocr_page(pdf,page["pagina"],cfg["ocr"]["dpi"],cfg["ocr"]["idioma"]); page["metodo"]="ocr"
                    except Exception as exc:
                        session.add(ErroProcessamento(documento_id=doc.id,pagina=page["pagina"],etapa="ocr",tipo=type(exc).__name__,mensagem=str(exc))); logging.exception("OCR falhou: %s p.%s",pdf.name,page["pagina"]); continue
                for raw in split_records(text):
                    fields=extract_fields(raw); classification,reasons,normalized=validate_record(fields,categories)
                    extracted_protocol=normalized.get("protocolo", "")
                    protocol_is_valid=is_valid_protocol(extracted_protocol)
                    storage_protocol=(
                        extracted_protocol
                        if protocol_is_valid
                        else f"INVALIDO-{doc.id}-{page['pagina']}-{len(rows)+1}"
                    )
                    if protocol_is_valid and find_by_protocol(session,storage_protocol):
                        classification="duplicado"; reasons.append("protocolo_duplicado")
                    row={
                        **fields,
                        "protocolo":extracted_protocol,
                        "email":normalized.get("email", fields.get("email")),
                        "categoria":normalized.get("categoria_normalizada") or fields.get("categoria"),
                        "status":normalized.get("status_normalizado") or fields.get("status"),
                        "cep":normalized.get("cep", fields.get("cep")),
                        "solicitante":normalized.get("solicitante", fields.get("solicitante")),
                        "descricao":normalized.get("descricao", fields.get("descricao")),
                        "data":normalized.get("data_obj"),
                        "tempo_minutos":normalized.get("tempo_obj"),
                        "classificacao":classification,
                        "motivos":";".join(reasons),
                        "documento":pdf.name,
                        "pagina":page["pagina"],
                        "metodo":page["metodo"],
                    }
                    rows.append(row)
                    if classification=="duplicado":
                        session.add(ErroProcessamento(documento_id=doc.id,pagina=page["pagina"],etapa="deduplicacao",tipo="Duplicidade",mensagem=storage_protocol)); continue
                    item=Atendimento(documento_id=doc.id,pagina=page["pagina"],protocolo=storage_protocol,data=normalized.get("data_obj"),solicitante=row.get("solicitante"),email=row.get("email"),categoria=row["categoria"],descricao=row.get("descricao"),solucao=fields.get("solucao"),tempo_minutos=normalized.get("tempo_obj"),status=row.get("status"),cep=row.get("cep"),municipio=None,uf=None,classificacao=classification,motivos=row["motivos"],texto_original=raw,texto_limpo=preprocess(raw))
                    session.add(item); session.flush()
                    for idx,content in enumerate(split_chunks(raw,cfg["embeddings"]["tamanho_chunk"],cfg["embeddings"]["sobreposicao"])):
                        meta={"protocolo":extracted_protocol or storage_protocol,"documento":pdf.name,"pagina":page["pagina"],"categoria":row["categoria"] or ""}
                        session.add(Chunk(atendimento_id=item.id,documento_id=doc.id,pagina=page["pagina"],indice=idx,conteudo=content,metadata_json=metadata_json(**meta)))
    df=pd.DataFrame(rows)
    if not df.empty:
        export_results(df,output,cfg["saida"]["csv"],cfg["saida"]["indicadores"]); generate_charts(df,resolve(root,cfg["saida"]["graficos"]))
    return df
