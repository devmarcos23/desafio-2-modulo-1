"""API HTTP de consulta dos atendimentos.

Expõe a recuperação/RAG por HTTP de forma validada, documentada e tolerante a falhas da camada interna.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import load_config
from .indexer import semantic_query
from .rag import answer

LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="Atendimentos FIC_DEV",
    description=(
        "API para consulta semântica dos atendimentos processados pelo desafio "
        "final de Python para IA."
    ),
    version="1.0.0",
)
cfg = load_config()


class AskRequest(BaseModel):
    """Dados aceitos pelo endpoint de consulta."""

    pergunta: str = Field(
        min_length=3,
        max_length=500,
        description="Pergunta em linguagem natural.",
        examples=["Quais problemas mencionam instalação do Python?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Quantidade máxima de fontes recuperadas.",
    )
    categoria: str | None = Field(
        default=None,
        description="Filtro opcional de categoria para a busca semântica.",
    )


class SourceResponse(BaseModel):
    """Fonte recuperada pelo mecanismo semântico."""

    protocolo: str | None = None
    documento: str | None = None
    pagina: int | None = None
    categoria: str | None = None
    conteudo: str | None = None
    similaridade: float | None = None

    model_config = {"extra": "allow"}


class AskResponse(BaseModel):
    """Resposta pública do endpoint ``POST /ask``."""

    resposta: str
    modo: str
    fontes: list[SourceResponse] = Field(default_factory=list)
    pergunta: str | None = None
    aviso: str | None = None


class HealthResponse(BaseModel):
    """Resposta do endpoint de disponibilidade da API."""

    status: str
    servico: str
    versao: str
    modo: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Informa se o serviço HTTP está disponível e qual modo de resposta está ativo."""

    mode = "rag" if os.getenv("OPENAI_API_KEY") else "recuperacao_local"
    return HealthResponse(
        status="ok",
        servico="Atendimentos FIC_DEV",
        versao=app.version,
        modo=mode,
    )


@app.post(
    "/ask",
    response_model=AskResponse,
    response_model_exclude_none=True,
)
def ask(payload: AskRequest) -> dict[str, Any]:
    """Recupera fontes e monta a resposta para uma pergunta do usuário.

    A recuperação semântica é responsabilidade da camada de indexação/RAG. Esta
    função valida a entrada, encaminha os parâmetros e converte falhas internas
    em uma resposta HTTP adequada sem expor detalhes sensíveis.
    """

    try:
        sources = semantic_query(
            cfg,
            payload.pergunta,
            payload.top_k,
            payload.categoria,
        )
        return answer(
            payload.pergunta,
            sources,
            os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )
    except Exception as exc:
        LOGGER.exception("Falha ao processar consulta no endpoint /ask")
        raise HTTPException(
            status_code=503,
            detail=(
                "Consulta indisponível no momento. Verifique se o banco e o "
                "índice vetorial foram preparados e tente novamente."
            ),
        ) from exc
