import requests

from src import ui_client


class FakeResponse:
    def raise_for_status(self):
        return None
    def json(self):
        return {"resposta": "ok", "fontes": []}


def test_api_url_from_environment(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://localhost:9999/")
    assert ui_client.get_api_base_url() == "http://localhost:9999"


def test_ask_api_builds_payload(monkeypatch):
    captured = {}
    def fake_post(url, json, timeout):
        captured.update({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()
    monkeypatch.setattr(ui_client.requests, "post", fake_post)
    result = ui_client.ask_api("pergunta", 4, "Python", "AT-001", base_url="http://api")
    assert result["resposta"] == "ok"
    assert captured["json"]["protocolo"] == "AT-001"


def test_connection_error_is_understandable(monkeypatch):
    monkeypatch.setattr(ui_client.requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError("raw")))
    try:
        ui_client.ask_api("pergunta", base_url="http://api")
    except ui_client.ApiClientError as exc:
        assert "Não foi possível conectar" in str(exc)
        assert "raw" not in str(exc)
    else:
        raise AssertionError("ApiClientError esperado")
