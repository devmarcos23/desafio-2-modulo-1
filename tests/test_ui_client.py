import requests

from src.ui_client import ApiClientError, ask_api, get_api_base_url


class FakeResponse:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self._body


def test_get_api_base_url_uses_environment(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://localhost:9000/")

    assert get_api_base_url() == "http://localhost:9000"


def test_ask_api_sends_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(
            {
                "resposta": "Resposta de teste",
                "modo": "recuperacao_local",
                "fontes": [],
            }
        )

    monkeypatch.setattr("src.ui_client.requests.post", fake_post)

    result = ask_api(
        "  Minha pergunta  ",
        top_k=4,
        category="  Python  ",
        base_url="http://api:8000/",
        timeout=12,
    )

    assert captured == {
        "url": "http://api:8000/ask",
        "json": {
            "pergunta": "Minha pergunta",
            "top_k": 4,
            "categoria": "Python",
        },
        "timeout": 12,
    }
    assert result["resposta"] == "Resposta de teste"


def test_ask_api_converts_connection_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("api fora do ar")

    monkeypatch.setattr("src.ui_client.requests.post", fake_post)

    try:
        ask_api("Pergunta válida")
    except ApiClientError as exc:
        assert "FastAPI" in str(exc)
    else:
        raise AssertionError("ApiClientError deveria ter sido lançado")


def test_ask_api_rejects_unexpected_json(monkeypatch):
    monkeypatch.setattr(
        "src.ui_client.requests.post",
        lambda *args, **kwargs: FakeResponse({"fontes": []}),
    )

    try:
        ask_api("Pergunta válida")
    except ApiClientError as exc:
        assert "formato esperado" in str(exc)
    else:
        raise AssertionError("ApiClientError deveria ter sido lançado")
