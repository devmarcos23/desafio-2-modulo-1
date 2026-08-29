from pathlib import Path

from src.database import create_session_factory, delete_by_protocol, find_by_protocol, session_scope, update_by_protocol
from src.models import Atendimento, Documento


def test_sqlite_parent_is_created(tmp_path):
    db_path = tmp_path / "nested" / "database" / "test.db"
    factory = create_session_factory(f"sqlite:///{db_path}")
    assert db_path.parent.is_dir()
    with session_scope(factory) as session:
        document = Documento(nome_arquivo="a.pdf", hash_sha256="a" * 64, total_paginas=1, paginas_ocr=0, metodo="extracao_direta", concluido=True)
        session.add(document)
        session.flush()
        session.add(Atendimento(documento_id=document.id, pagina=1, protocolo="AT-001", classificacao="valido", texto_original="x", texto_limpo="x"))

    with session_scope(factory) as session:
        assert find_by_protocol(session, "AT-001") is not None
        assert update_by_protocol(session, "AT-001", status="Concluido") is not None
        assert find_by_protocol(session, "AT-001").status == "Concluido"
        assert delete_by_protocol(session, "AT-001") is True
        assert find_by_protocol(session, "AT-001") is None
