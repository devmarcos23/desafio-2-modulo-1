from src.indexer import _build_where


def test_filters_support_category_and_protocol():
    assert _build_where("Python", None) == {"categoria": "Python"}
    assert _build_where(None, "AT-001") == {"protocolo": "AT-001"}
    assert _build_where("Python", "AT-001") == {"$and": [{"categoria": "Python"}, {"protocolo": "AT-001"}]}
