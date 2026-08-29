from src.text_processor import preprocess, split_chunks, tokens


def test_chunks_have_overlap_and_limit():
    chunks = split_chunks("texto de exemplo " * 100, size=120, overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_preprocess_keeps_original_outside_function_and_removes_stopword():
    original = "A senha para o ambiente virtual"
    processed = preprocess(original)
    assert original == "A senha para o ambiente virtual"
    assert "para" not in processed.split()


def test_tokenize_returns_words():
    assert tokens("Python, ambiente virtual!")[:2] == ["python", "ambiente"]
