"""API FastAPI para consulta semântica/RAG dos atendimentos."""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .config import load_config
from .indexer import semantic_query
from .rag import answer

LOGGER = logging.getLogger(__name__)
app = FastAPI(
    title="Atendimentos FIC_DEV",
    description="Consulta semântica dos atendimentos processados no desafio.",
    version=__version__,
)
cfg = load_config()


class AskRequest(BaseModel):
    """Entrada validada do endpoint de pergunta."""

    pergunta: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    categoria: str | None = None
    protocolo: str | None = None


class SourceResponse(BaseModel):
    protocolo: str | None = None
    documento: str | None = None
    pagina: int | None = None
    categoria: str | None = None
    conteudo: str | None = None
    similaridade: float | None = None
    model_config = {"extra": "allow"}


class AskResponse(BaseModel):
    resposta: str
    modo: str
    fontes: list[SourceResponse] = Field(default_factory=list)
    pergunta: str | None = None
    aviso: str | None = None


class HealthResponse(BaseModel):
    status: str
    servico: str
    versao: str
    modo: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check da API e indicação do modo de resposta."""
    return HealthResponse(
        status="ok",
        servico="Atendimentos FIC_DEV",
        versao=app.version,
        modo="rag" if os.getenv("OPENAI_API_KEY") else "recuperacao_local",
    )


@app.post("/ask", response_model=AskResponse, response_model_exclude_none=True)
def ask(payload: AskRequest) -> dict[str, Any]:
    """Recupera chunks relevantes e devolve resposta + fontes + pontuações."""
    try:
        sources = semantic_query(
            cfg,
            payload.pergunta,
            payload.top_k,
            payload.categoria,
            payload.protocolo,
        )
        return answer(
            payload.pergunta,
            sources,
            os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )
    except Exception as exc:
        LOGGER.exception("Falha no endpoint /ask")
        raise HTTPException(
            status_code=503,
            detail=(
                "Consulta indisponível. Execute o pipeline e a indexação vetorial "
                "e tente novamente."
            ),
        ) from exc
