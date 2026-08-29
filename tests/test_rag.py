from src.rag import build_context, local_answer


def test_local_mode_reports_insufficient_context():
    result = local_answer("Qual atendimento?", [])
    assert "informação suficiente" in result["resposta"]
    assert result["fontes"] == []


def test_context_is_bounded_and_has_source_reference():
    sources = [{"protocolo": "AT-001", "documento": "a.pdf", "pagina": 2, "conteudo": "x" * 500}]
    context = build_context(sources, max_chars=120)
    assert len(context) <= 120
    assert "AT-001" in context
