from src.validation import extract_fields, normalize_category, split_records, validate_record

CATS = {
    "categorias_oficiais": [
        {"nome": "Python e bibliotecas", "variacoes": ["python", "pip"]},
        {"nome": "Atividades e arquivos", "variacoes": ["atividade", "entrega"]},
    ],
    "status_validos": ["Concluido", "Pendente", "Em atendimento"],
}


def base_record(**changes):
    data = {
        "protocolo": "AT-001",
        "data": "01/08/2026",
        "email": "a@b.com",
        "cep": "78200-000",
        "categoria": "pip",
        "tempo_minutos": "20",
        "solicitante": "Ana",
        "descricao": "Erro",
        "status": "Concluido",
    }
    data.update(changes)
    return data


def test_valid_record_and_category_normalization():
    classification, reasons, normalized = validate_record(base_record(), CATS)
    assert classification == "valido"
    assert reasons == []
    assert normalized["categoria_normalizada"] == "Python e bibliotecas"


def test_invalid_email_is_preserved_as_invalid():
    assert "email_invalido" in validate_record(base_record(email="invalido"), CATS)[1]


def test_missing_marker_is_incomplete():
    classification, reasons, _ = validate_record(base_record(solicitante="[vazio]"), CATS)
    assert classification == "incompleto"
    assert "solicitante_ausente" in reasons


def test_ocr_protocol_variations_are_normalized():
    text = "Protocolo AT -@52 Data 0107/2026 Solicitante Ana Email a@b.com Categoria pip Status Pendente CEP 78200-000 Tempo 10 min Problema Erro Solucao X Observacoes Y"
    fields = extract_fields(text)
    assert fields["protocolo"] == "AT-052"


def test_split_records_recovers_multiple_ocr_records():
    page = (
        "Protocol AT-051 Data 01/07/2026 Solicitante A Email a@b.com Categoria pip "
        "Status Pendente CEP 78200-000 Tempo 10 min Problema X Solucao Y Observacoes Z "
        "Protocol AT -@52 Data 02/07/2026 Solicitante B Email b@b.com Categoria entrega "
        "Status Concluido CEP 78200-000 Tempo 20 min Problema X Solucao Y Observacoes Z"
    )
    records = split_records(page)
    assert len(records) == 2
    assert extract_fields(records[1])["protocolo"] == "AT-052"


def test_fuzzy_category_handles_small_ocr_distortion():
    assert normalize_category("atvidade", CATS) == "Atividades e arquivos"
