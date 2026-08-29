from src.validation import (
    extract_fields,
    normalize_category,
    parse_date,
    split_records,
    validate_record,
)

CATS = {
    "categorias_oficiais": [
        {
            "nome": "Python e bibliotecas",
            "variacoes": ["python", "pip", "biblioteca"],
        },
        {
            "nome": "Atividades e arquivos",
            "variacoes": ["atividade", "arquivo"],
        },
    ],
    "status_validos": ["Concluido", "Pendente", "Em atendimento"],
}


def test_valid_record():
    record = {
        "protocolo": "AT-001",
        "data": "01/08/2026",
        "email": "a@b.com",
        "cep": "78200-000",
        "categoria": "pip",
        "status": "Concluido",
        "tempo_minutos": "20",
        "solicitante": "Ana",
        "descricao": "Erro",
    }
    classification, reasons, normalized = validate_record(record, CATS)
    assert classification == "valido"
    assert not reasons
    assert normalized["categoria_normalizada"] == "Python e bibliotecas"
    assert normalized["status_normalizado"] == "Concluido"


def test_invalid_email():
    record = {
        "protocolo": "AT-001",
        "data": "01/08/2026",
        "email": "invalido",
        "cep": "78200-000",
        "categoria": "python",
        "status": "Pendente",
        "tempo_minutos": "20",
        "solicitante": "Ana",
        "descricao": "Erro",
    }
    assert "email_invalido" in validate_record(record, CATS)[1]


def test_missing_markers_are_classified_as_incomplete():
    record = {
        "protocolo": "AT-081",
        "data": "11/08/2026",
        "email": "a@b.com",
        "cep": "78550-000",
        "categoria": "python",
        "status": "Concluido",
        "tempo_minutos": "[vazio]",
        "solicitante": "[vazio]",
        "descricao": "Erro",
    }
    classification, reasons, _ = validate_record(record, CATS)
    assert classification == "incompleto"
    assert "tempo_ausente" in reasons
    assert "solicitante_ausente" in reasons


def test_invalid_status_is_reported():
    record = {
        "protocolo": "AT-001",
        "data": "01/08/2026",
        "email": "a@b.com",
        "cep": "78200-000",
        "categoria": "python",
        "status": "Finalizado de qualquer jeito",
        "tempo_minutos": "20",
        "solicitante": "Ana",
        "descricao": "Erro",
    }
    classification, reasons, _ = validate_record(record, CATS)
    assert classification == "invalido"
    assert "status_invalido" in reasons


def test_ocr_variations_are_split_and_extracted():
    text = (
        "Protocol AT -@52 Data 0107/2026 "
        "Solicitante Otavia Cardoso Leal Email otavia.cardoso@ aluno.exemplo.br "
        "Categoria atvidade Status Pendente CEP /cidade 78110-000 - Varzea Grande/MT "
        "Tem po 60mn Problem a CSV abre errado. Solucao Ajustado. "
        "Observacoes Registro 052. "
        "Protocolo AT 053 Data 2026-07-06 Solicitante Vinicius Mendes "
        "Email vinicius@aluno.exemplo.br Categoria python Status Concluido "
        "CEP /cidade 78700-000 Tem po 67min Problema pip falha. "
        "Solucao Corrigido. Observacoes Registro 053."
    )
    records = split_records(text)
    assert len(records) == 2

    first = extract_fields(records[0])
    assert first["protocolo"] == "AT-052"
    assert first["data"] == "0107/2026"
    assert first["tempo_minutos"] == "60"
    assert normalize_category(first["categoria"], CATS) == "Atividades e arquivos"


def test_parse_date_recovers_missing_ocr_separator():
    assert str(parse_date("0107/2026")) == "2026-07-01"


def test_split_records_ignores_word_protocol_inside_observation():
    text = (
        "Protocolo AT-001 Data 01/08/2026 Solicitante Ana E-mail a@b.com "
        "Categoria python Status Pendente CEP / cidade 78200-000 Tempo 20 min "
        "Problema Erro Solucao Ok Observacoes Segunda ocorrencia do mesmo protocolo "
        "para teste. Protocolo AT-002 Data 02/08/2026 Solicitante Bia E-mail b@b.com "
        "Categoria python Status Pendente CEP / cidade 78200-000 Tempo 25 min "
        "Problema Erro Solucao Ok Observacoes Fim."
    )
    assert len(split_records(text)) == 2
