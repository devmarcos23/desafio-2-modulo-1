import requests

from src import cep_client


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("erro")
    def json(self):
        return self.payload


def test_cep_lookup_success(monkeypatch):
    monkeypatch.setattr(cep_client.requests, "get", lambda *a, **k: FakeResponse({"localidade": "Cuiaba", "uf": "MT", "logradouro": "Rua X"}))
    result = cep_client.lookup_cep("78000-000", "https://exemplo.test/ws", 1)
    assert result["municipio"] == "Cuiaba"
    assert result["uf"] == "MT"


def test_cep_lookup_failure_does_not_raise(monkeypatch):
    def fail(*a, **k):
        raise requests.Timeout("offline")
    monkeypatch.setattr(cep_client.requests, "get", fail)
    assert cep_client.lookup_cep("78000-000", "https://exemplo.test/ws", 1) is None
