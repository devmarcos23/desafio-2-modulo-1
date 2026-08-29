"""Testes de integração entre a API e o modo local de recuperação.

A busca vetorial é substituída por uma fonte determinística para validar o fluxo
HTTP -> RAG local -> resposta pública sem baixar modelos ou chamar serviços
externos.
"""
from urllib import response

from fastapi.testclient import TestClient

import src.api as api_module


client = TestClient(api_module.app)


def test_http_to_local_rag_flow(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    sources = [
        {
            "protocolo": "AT-051",
            "documento": "atendimentos_digitalizados.pdf",
            "pagina": 1,
            "categoria": "Ambiente Python",
            "conteudo": "Usuário relatou dificuldade na instalação do Python.",
            "similaridade": 0.88,
        }
    ]
    monkeypatch.setattr(
        api_module,
        "semantic_query",
        lambda cfg, question, top_k, category=None, protocol=None: sources,
    )

    response = client.post(
        "/ask",
        json={"pergunta": "Existe problema de instalação do Python?", "top_k": 1},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["modo"] == "recuperacao_local"
    assert body["fontes"][0]["protocolo"] == "AT-051"
    assert "AT-051" in body["resposta"]
    assert "contexto recuperado" in body["resposta"]