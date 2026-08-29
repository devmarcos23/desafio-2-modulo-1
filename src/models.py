"""Modelos SQLAlchemy usados pelo pipeline, auditoria e RAG."""
from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa da aplicação."""


class Documento(Base):
    """Documento PDF processado pelo pipeline."""

    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255), index=True)
    hash_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    total_paginas: Mapped[int] = mapped_column(Integer)
    paginas_ocr: Mapped[int] = mapped_column(Integer, default=0)
    metodo: Mapped[str] = mapped_column(String(30))
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    processado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    atendimentos: Mapped[list["Atendimento"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )
    erros: Mapped[list["ErroProcessamento"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )
    registros: Mapped[list["RegistroProcessado"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan"
    )


class Atendimento(Base):
    """Atendimento único persistido e utilizado na busca semântica."""

    __tablename__ = "atendimentos"
    __table_args__ = (UniqueConstraint("protocolo", name="uq_atendimento_protocolo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), index=True)
    pagina: Mapped[int] = mapped_column(Integer)
    protocolo: Mapped[str] = mapped_column(String(50), index=True)
    protocolo_original: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    solicitante: Mapped[str | None] = mapped_column(String(180), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    solucao: Mapped[str | None] = mapped_column(Text, nullable=True)
    tempo_minutos: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(10), nullable=True)
    municipio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    classificacao: Mapped[str] = mapped_column(String(30))
    motivos: Mapped[str | None] = mapped_column(Text, nullable=True)
    texto_original: Mapped[str] = mapped_column(Text)
    texto_limpo: Mapped[str] = mapped_column(Text)

    documento: Mapped[Documento] = relationship(back_populates="atendimentos")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan"
    )


class RegistroProcessado(Base):
    """Histórico de todos os registros extraídos, inclusive duplicados.

    Esta tabela permite reconstruir CSV e indicadores de forma idempotente sem
    reinserir protocolos duplicados em ``atendimentos``.
    """

    __tablename__ = "registros_processados"
    __table_args__ = (
        UniqueConstraint(
            "documento_id", "pagina", "ordem_pagina", name="uq_registro_documento_pagina_ordem"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), index=True)
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimentos.id"), nullable=True
    )
    pagina: Mapped[int] = mapped_column(Integer)
    ordem_pagina: Mapped[int] = mapped_column(Integer)
    protocolo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_texto: Mapped[str | None] = mapped_column(String(30), nullable=True)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    solicitante: Mapped[str | None] = mapped_column(String(180), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    solucao: Mapped[str | None] = mapped_column(Text, nullable=True)
    tempo_minutos: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(10), nullable=True)
    municipio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    classificacao: Mapped[str] = mapped_column(String(30), index=True)
    motivos: Mapped[str | None] = mapped_column(Text, nullable=True)
    metodo: Mapped[str] = mapped_column(String(30))
    texto_original: Mapped[str] = mapped_column(Text)
    texto_limpo: Mapped[str] = mapped_column(Text)

    documento: Mapped[Documento] = relationship(back_populates="registros")


class Chunk(Base):
    """Trecho de texto usado na busca semântica/RAG."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("atendimento_id", "indice", name="uq_chunk_atendimento_indice"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    atendimento_id: Mapped[int] = mapped_column(ForeignKey("atendimentos.id"), index=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), index=True)
    pagina: Mapped[int] = mapped_column(Integer)
    indice: Mapped[int] = mapped_column(Integer)
    conteudo: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)

    atendimento: Mapped[Atendimento] = relationship(back_populates="chunks")
    documento: Mapped[Documento] = relationship(back_populates="chunks")


class ErroProcessamento(Base):
    """Erro ou inconsistência registrada durante o processamento."""

    __tablename__ = "erros_processamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documentos.id"), nullable=True, index=True
    )
    pagina: Mapped[int | None] = mapped_column(Integer, nullable=True)
    etapa: Mapped[str] = mapped_column(String(80), index=True)
    tipo: Mapped[str] = mapped_column(String(100), index=True)
    mensagem: Mapped[str] = mapped_column(Text)
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    documento: Mapped[Documento | None] = relationship(back_populates="erros")
