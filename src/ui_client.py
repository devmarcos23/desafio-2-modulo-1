"""Cliente HTTP usado pela interface Streamlit.

O módulo separa a comunicação HTTP da camada visual para permitir testes sem
iniciar o Streamlit.
"""
from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 60


class ApiClientError(RuntimeError):
    """Erro compreensível de comunicação ou resposta inválida da API."""


def get_api_base_url() -> str:
    """Obtém a URL da API por variável de ambiente, com fallback local."""

    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def ask_api(
    question: str,
    top_k: int = 5,
    category: str | None = None,
    *,
    base_url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Envia uma pergunta ao endpoint ``POST /ask`` e valida a resposta básica."""

    payload: dict[str, Any] = {
        "pergunta": question.strip(),
        "top_k": top_k,
    }
    if category and category.strip():
        payload["categoria"] = category.strip()

    target = f"{(base_url or get_api_base_url()).rstrip('/')}/ask"

    try:
        response = requests.post(target, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ApiClientError(
            "Não foi possível conectar à API. Verifique se a FastAPI está em "
            "execução e se API_BASE_URL está correta."
        ) from exc
    except ValueError as exc:
        raise ApiClientError("A API retornou uma resposta que não é JSON válido.") from exc

    if not isinstance(data, dict) or "resposta" not in data:
        raise ApiClientError("A resposta da API não possui o formato esperado.")

    return data
