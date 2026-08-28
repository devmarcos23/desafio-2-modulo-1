"""Recuperação local e resposta RAG opcional com OpenAI/LangChain."""

from __future__ import annotations

import os
from typing import Any, Sequence


SYSTEM = """
Você é um assistente responsável por responder perguntas sobre
atendimentos processados.

Responda somente com base no contexto fornecido.

Regras:
1. Não invente informações.
2. Se o contexto não for suficiente para responder, informe
   que não há informação suficiente.
3. Cite os protocolos utilizados na resposta.
4. Quando disponível, informe documento e página da fonte.
5. Seja objetivo e responda em português.
""".strip()


def _normalize_question(question: str) -> str:
    """Normaliza e valida a pergunta."""
    if question is None:
        return ""

    return str(question).strip()


def _format_source(source: dict[str, Any]) -> str:
    """Formata uma fonte para apresentação ao usuário."""
    protocolo = source.get("protocolo")

    if not protocolo:
        metadata = source.get("metadata") or {}
        protocolo = metadata.get("protocolo")

    pagina = source.get("pagina")

    if pagina is None:
        metadata = source.get("metadata") or {}
        pagina = metadata.get("pagina")

    documento = source.get("documento")

    if not documento:
        metadata = source.get("metadata") or {}
        documento = metadata.get("documento")

    parts: list[str] = []

    if protocolo:
        parts.append(f"protocolo={protocolo}")

    if documento:
        parts.append(f"documento={documento}")

    if pagina is not None:
        parts.append(f"pagina={pagina}")

    return ", ".join(parts)


def _build_context(
    sources: Sequence[dict[str, Any]],
) -> str:
    """Monta o contexto utilizado pelo modelo."""
    blocks: list[str] = []

    for index, source in enumerate(sources, start=1):
        content = str(
            source.get("conteudo")
            or source.get("document")
            or ""
        ).strip()

        if not content:
            continue

        reference = _format_source(source)

        if reference:
            blocks.append(
                f"[Fonte {index} — {reference}]\n{content}"
            )
        else:
            blocks.append(
                f"[Fonte {index}]\n{content}"
            )

    return "\n\n".join(blocks)


def _normalize_sources(
    sources: Sequence[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Converte as fontes para uma lista segura."""
    if not sources:
        return []

    return [
        dict(source)
        for source in sources
        if isinstance(source, dict)
    ]


def local_answer(
    question: str,
    sources: Sequence[dict[str, Any]] | None,
) -> dict[str, Any]:
    """
    Retorna uma resposta no modo local.

    O modo local não utiliza uma API de geração de texto.
    Ele apresenta os trechos recuperados e suas respectivas fontes.
    """
    question = _normalize_question(question)
    normalized_sources = _normalize_sources(sources)

    if not question:
        return {
            "resposta": "Informe uma pergunta para realizar a consulta.",
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }

    if not normalized_sources:
        return {
            "resposta": (
                "Não há informação suficiente no contexto "
                "recuperado para responder à pergunta."
            ),
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }

    protocolos: list[str] = []

    for source in normalized_sources:
        protocolo = source.get("protocolo")

        if not protocolo:
            metadata = source.get("metadata") or {}
            protocolo = metadata.get("protocolo")

        if protocolo and protocolo not in protocolos:
            protocolos.append(str(protocolo))

    if protocolos:
        referencia = ", ".join(protocolos)

        resposta = (
            "Modo local: foram recuperados os trechos mais "
            "semelhantes à pergunta. "
            f"Protocolos recuperados: {referencia}. "
            "Configure OPENAI_API_KEY para gerar uma síntese "
            "fundamentada no contexto."
        )
    else:
        resposta = (
            "Modo local: foram recuperados os trechos mais "
            "semelhantes à pergunta. "
            "Configure OPENAI_API_KEY para gerar uma síntese "
            "fundamentada no contexto."
        )

    return {
        "resposta": resposta,
        "modo": "recuperacao_local",
        "pergunta": question,
        "fontes": normalized_sources,
    }


def answer(
    question: str,
    sources: Sequence[dict[str, Any]] | None,
    model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    """
    Gera uma resposta utilizando RAG quando a chave OpenAI estiver disponível.

    Sem OPENAI_API_KEY, utiliza o modo de recuperação local.

    Args:
        question: Pergunta do usuário.
        sources: Chunks recuperados pelo mecanismo de busca.
        model: Modelo OpenAI utilizado para a síntese.

    Returns:
        Dicionário contendo resposta, modo, pergunta e fontes.
    """
    question = _normalize_question(question)
    normalized_sources = _normalize_sources(sources)

    if not question:
        return {
            "resposta": "Informe uma pergunta para realizar a consulta.",
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }

    if not normalized_sources:
        return {
            "resposta": (
                "Não há informação suficiente no contexto "
                "recuperado para responder à pergunta."
            ),
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": [],
        }

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return local_answer(
            question,
            normalized_sources,
        )

    context = _build_context(normalized_sources)

    if not context:
        return {
            "resposta": (
                "Não há informação suficiente no contexto "
                "recuperado para responder à pergunta."
            ),
            "modo": "recuperacao_local",
            "pergunta": question,
            "fontes": normalized_sources,
        }

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM),
                (
                    "human",
                    "Pergunta: {question}\n\n"
                    "Contexto:\n{context}",
                ),
            ]
        )

        llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key,
        )

        chain = prompt | llm

        response = chain.invoke(
            {
                "question": question,
                "context": context,
            }
        )

        content = getattr(
            response,
            "content",
            None,
        )

        if isinstance(content, list):
            content = "".join(
                str(item)
                for item in content
            )

        if not content:
            raise ValueError(
                "O modelo não retornou conteúdo."
            )

        return {
            "resposta": str(content).strip(),
            "modo": "rag",
            "pergunta": question,
            "fontes": normalized_sources,
        }

    except Exception as exc:
        result = local_answer(
            question,
            normalized_sources,
        )

        result["aviso"] = (
            f"Falha no modelo RAG: "
            f"{type(exc).__name__}: {exc}"
        )

        return result