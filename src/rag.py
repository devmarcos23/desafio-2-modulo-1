"""Resposta RAG opcional e modo local baseado somente nas fontes recuperadas."""
from __future__ import annotations

import logging
import os
from typing import Any, Sequence

LOGGER = logging.getLogger(__name__)

SYSTEM = """
Você responde perguntas sobre atendimentos processados.
Use somente o contexto fornecido.
Não invente informações.
Se o contexto não sustentar a resposta, informe que não há informação suficiente.
Cite os protocolos usados e, quando disponível, documento e página.
Responda objetivamente em português.
""".strip()


def _normalize_sources(sources: Sequence[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [dict(source) for source in (sources or []) if isinstance(source, dict)]


def _reference(source: dict[str, Any]) -> str:
    metadata = source.get("metadata") or {}
    protocol = source.get("protocolo") or metadata.get("protocolo")
    document = source.get("documento") or metadata.get("documento")
    page = source.get("pagina") if source.get("pagina") is not None else metadata.get("pagina")
    parts = []
    if protocol:
        parts.append(f"protocolo={protocol}")
    if document:
        parts.append(f"documento={document}")
    if page is not None:
        parts.append(f"pagina={page}")
    return ", ".join(parts)


def build_context(
    sources: Sequence[dict[str, Any]], max_chars: int = 6000
) -> str:
    """Monta contexto rastreável limitado por tamanho."""
    if max_chars <= 0:
        raise ValueError("max_chars deve ser positivo")
    blocks: list[str] = []
    total = 0
    for index, source in enumerate(sources, start=1):
        content = str(source.get("conteudo") or source.get("document") or "").strip()
        if not content:
            continue
        reference = _reference(source)
        block = f"[Fonte {index}{' — ' + reference if reference else ''}]\n{content}"
        remaining = max_chars - total
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining]
        blocks.append(block)
        total += len(block) + 2
    return "\n\n".join(blocks)


def local_answer(
    question: str, sources: Sequence[dict[str, Any]] | None
) -> dict[str, Any]:
    """Mantém a consulta funcional sem chamada a modelo gerativo."""
    question = str(question or "").strip()
    normalized = _normalize_sources(sources)
    if not question:
        return {
            "resposta": "Informe uma pergunta para realizar a consulta.",
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }
    if not normalized:
        return {
            "resposta": "Não há informação suficiente nos documentos para responder à pergunta.",
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }
    protocols: list[str] = []
    for source in normalized:
        protocol = source.get("protocolo") or (source.get("metadata") or {}).get("protocolo")
        if protocol and str(protocol) not in protocols:
            protocols.append(str(protocol))
    refs = ", ".join(protocols)
    response = "Modo local: foram recuperados os trechos mais relevantes."
    if refs:
        response += f" Protocolos recuperados: {refs}."
    response += " As fontes abaixo contêm o contexto recuperado."
    return {
        "resposta": response,
        "modo": "recuperacao_local",
        "pergunta": question,
        "fontes": normalized,
    }


def answer(
    question: str,
    sources: Sequence[dict[str, Any]] | None,
    model: str = "gpt-4.1-mini",
    *,
    max_context_chars: int = 6000,
) -> dict[str, Any]:
    """Gera síntese RAG quando houver chave; caso contrário usa recuperação local."""
    question = str(question or "").strip()
    normalized = _normalize_sources(sources)
    if not question or not normalized:
        return local_answer(question, normalized)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return local_answer(question, normalized)

    context = build_context(normalized, max_chars=max_context_chars)
    if not context:
        return local_answer(question, normalized)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM),
                ("human", "Pergunta: {question}\n\nContexto:\n{context}"),
            ]
        )
        chain = prompt | ChatOpenAI(model=model, temperature=0, api_key=api_key)
        result = chain.invoke({"question": question, "context": context})
        content = getattr(result, "content", None)
        if isinstance(content, list):
            content = "".join(str(item) for item in content)
        if not content:
            raise ValueError("modelo sem conteúdo")
        return {
            "resposta": str(content).strip(),
            "modo": "rag",
            "pergunta": question,
            "fontes": normalized,
        }
    except Exception:
        # Não expõe detalhes de infraestrutura/chaves ao usuário final.
        LOGGER.exception("Falha no modelo RAG; usando recuperação local")
        result = local_answer(question, normalized)
        result["aviso"] = "O modelo de linguagem não estava disponível; foi usado o modo local."
        return result
