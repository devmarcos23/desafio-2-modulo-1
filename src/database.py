"""Criação do banco, sessões e operações CRUD controladas."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import unquote

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Atendimento, Base


def ensure_sqlite_parent(url: str) -> None:
    """Cria o diretório pai quando a URL aponta para um arquivo SQLite."""
    prefix = "sqlite:///"
    if not url.startswith(prefix) or url == "sqlite:///:memory:":
        return
    raw_path = unquote(url[len(prefix) :])
    path = Path(raw_path)
    # URLs absolutas POSIX começam com /; no Windows Path aceita C:/ normalmente.
    path.parent.mkdir(parents=True, exist_ok=True)


def create_engine_for_url(url: str) -> Engine:
    """Cria um engine SQLAlchemy garantindo o diretório do SQLite."""
    ensure_sqlite_parent(url)
    return create_engine(url, future=True)


def create_session_factory(url: str):
    """Cria tabelas e retorna a fábrica de sessões."""
    engine = create_engine_for_url(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory) -> Iterator[Session]:
    """Abre sessão transacional com commit/rollback/close."""
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def find_by_protocol(session: Session, protocol: str) -> Atendimento | None:
    """Busca um atendimento pelo protocolo persistido."""
    return session.scalar(select(Atendimento).where(Atendimento.protocolo == protocol))


def update_by_protocol(session: Session, protocol: str, **changes) -> Atendimento | None:
    """Atualiza campos conhecidos de um atendimento e devolve a entidade."""
    item = find_by_protocol(session, protocol)
    if item is None:
        return None
    for key, value in changes.items():
        if not hasattr(item, key) or key in {"id", "protocolo"}:
            continue
        setattr(item, key, value)
    session.flush()
    return item


def delete_by_protocol(session: Session, protocol: str) -> bool:
    """Exclui de forma controlada um atendimento pelo protocolo."""
    item = find_by_protocol(session, protocol)
    if item is None:
        return False
    session.delete(item)
    return True
