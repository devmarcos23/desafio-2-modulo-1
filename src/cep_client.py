"""Cliente HTTP tolerante a falhas para complementação de CEP."""
from __future__ import annotations

from typing import Any

import requests


def lookup_cep(cep: str, base_url: str, timeout: float = 8) -> dict[str, Any] | None:
    """Consulta uma API pública de CEP sem interromper o pipeline em falhas.

    Retorna apenas dados necessários ao projeto. CEP inválido, 404/5xx, timeout,
    resposta inválida ou indisponibilidade de rede resultam em ``None``.
    """
    digits = "".join(character for character in str(cep or "") if character.isdigit())
    if len(digits) != 8:
        return None
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/{digits}/json/",
            timeout=timeout,
            headers={"User-Agent": "fic-dev-desafio/1.0"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get("erro"):
            return None
        return {
            "municipio": data.get("localidade"),
            "uf": data.get("uf"),
            "logradouro": data.get("logradouro"),
        }
    except (requests.RequestException, ValueError, TypeError):
        return None
