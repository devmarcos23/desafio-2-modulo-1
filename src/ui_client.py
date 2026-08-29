"""Cliente HTTP da interface Streamlit, separado para facilitar testes."""
from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 60


class ApiClientError(RuntimeError):
    """Erro compreensível de comunicação com a FastAPI."""


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def ask_api(
    question: str,
    top_k: int = 5,
    category: str | None = None,
    protocol: str | None = None,
    *,
    base_url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Faz POST /ask e valida o formato mínimo da resposta."""
    payload: dict[str, Any] = {"pergunta": str(question or "").strip(), "top_k": top_k}
    if category and category.strip():
        payload["categoria"] = category.strip()
    if protocol and protocol.strip():
        payload["protocolo"] = protocol.strip()
    target = f"{(base_url or get_api_base_url()).rstrip('/')}/ask"
    try:
        response = requests.post(target, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ApiClientError(
            "Não foi possível conectar à API. Confirme se a FastAPI está em execução "
            "e se API_BASE_URL está correta."
        ) from exc
    except ValueError as exc:
        raise ApiClientError("A API retornou JSON inválido.") from exc
    if not isinstance(data, dict) or "resposta" not in data or "fontes" not in data:
        raise ApiClientError("A resposta da API não possui o formato esperado.")
    return data
