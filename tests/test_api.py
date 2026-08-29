from fastapi.testclient import TestClient

import src.api as api

client = TestClient(api.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_validation():
    assert client.post("/ask", json={"pergunta": "x"}).status_code == 422


def test_ask_returns_answer_sources_and_score(monkeypatch):
    monkeypatch.setattr(api, "semantic_query", lambda *a, **k: [{"protocolo": "AT-001", "documento": "a.pdf", "pagina": 1, "conteudo": "erro de senha", "similaridade": 0.9}])
    monkeypatch.setattr(api, "answer", lambda question, sources, model: {"resposta": "Resposta", "modo": "recuperacao_local", "pergunta": question, "fontes": sources})
    response = client.post("/ask", json={"pergunta": "Como resolver senha?", "top_k": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["resposta"] == "Resposta"
    assert body["fontes"][0]["similaridade"] == 0.9


def test_ask_internal_failure_returns_503_without_traceback(monkeypatch):
    monkeypatch.setattr(api, "semantic_query", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("segredo interno")))
    response = client.post("/ask", json={"pergunta": "Pergunta válida"})
    assert response.status_code == 503
    assert "segredo interno" not in response.text
