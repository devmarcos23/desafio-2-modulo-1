"""Criação do banco, sessão e operações CRUD."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Atendimento


def create_session_factory(url: str):
    """Cria o engine, as tabelas e a fábrica de sessões."""
    engine = create_engine(url, future=True)

    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False
    )


@contextmanager
def session_scope(factory):
    """Abre uma sessão e garante commit, rollback e fechamento."""
    session: Session = factory()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def find_by_protocol(
    session: Session,
    protocol: str
) -> Atendimento | None:
    """Busca um atendimento pelo protocolo."""
    return session.scalar(
        select(Atendimento).where(
            Atendimento.protocolo == protocol
        )
    )


def delete_by_protocol(
    session: Session,
    protocol: str
) -> bool:
    """Exclui um atendimento pelo protocolo."""
    item = find_by_protocol(session, protocol)

    if not item:
        return False

    session.delete(item)
    return True