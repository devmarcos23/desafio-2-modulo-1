from fastapi.testclient import TestClient

import src.api as api_module

client = TestClient(api_module.app)


def test_health_returns_service_information(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "servico": "Atendimentos FIC_DEV",
        "versao": "1.0.0",
        "modo": "recuperacao_local",
    }


def test_health_reports_rag_mode_when_key_exists(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "chave-de-teste")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["modo"] == "rag"


def test_ask_rejects_short_question():
    response = client.post("/ask", json={"pergunta": "x"})

    assert response.status_code == 422


def test_ask_rejects_invalid_top_k():
    response = client.post(
        "/ask",
        json={"pergunta": "Pergunta válida", "top_k": 21},
    )

    assert response.status_code == 422


def test_ask_returns_answer_and_sources(monkeypatch):
    expected_sources = [
        {
            "protocolo": "AT-001",
            "documento": "atendimentos_digitais.pdf",
            "pagina": 1,
            "categoria": "Python",
            "conteudo": "Falha ao instalar uma biblioteca.",
            "similaridade": 0.91,
        }
    ]

    def fake_semantic_query(cfg, question, top_k, category):
        assert question == "Problemas com Python"
        assert top_k == 3
        assert category == "Python"
        return expected_sources

    def fake_answer(question, sources, model):
        assert question == "Problemas com Python"
        assert sources == expected_sources
        assert model
        return {
            "resposta": "Há registros relacionados à instalação de bibliotecas.",
            "modo": "recuperacao_local",
            "fontes": sources,
        }

    monkeypatch.setattr(api_module, "semantic_query", fake_semantic_query)
    monkeypatch.setattr(api_module, "answer", fake_answer)

    response = client.post(
        "/ask",
        json={
            "pergunta": "Problemas com Python",
            "top_k": 3,
            "categoria": "Python",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["modo"] == "recuperacao_local"
    assert body["fontes"][0]["protocolo"] == "AT-001"
    assert body["fontes"][0]["conteudo"] == "Falha ao instalar uma biblioteca."


def test_ask_converts_internal_failure_to_503(monkeypatch):
    def fail_query(*args, **kwargs):
        raise RuntimeError("detalhe interno que não deve ir ao cliente")

    monkeypatch.setattr(api_module, "semantic_query", fail_query)

    response = client.post(
        "/ask",
        json={"pergunta": "Pergunta válida para teste"},
    )

    assert response.status_code == 503
    assert "índice vetorial" in response.json()["detail"]
    assert "detalhe interno" not in response.text
