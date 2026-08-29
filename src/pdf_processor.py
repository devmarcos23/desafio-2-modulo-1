"""Extração direta de texto e identificação de páginas que exigem OCR."""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFProcessingError(RuntimeError):
    """Erro que impede a abertura de um documento PDF."""


class PDFPage(TypedDict):
    """Resultado mínimo da inspeção de uma página PDF."""

    pagina: int
    texto: str
    metodo: str
    erro_extracao: str | None


def _meaningful_char_count(text: str) -> int:
    """Conta caracteres alfanuméricos, ignorando espaços e artefatos do PDF."""
    return sum(character.isalnum() for character in text)


def extract_pdf_pages(path: str | Path, min_chars: int = 40) -> list[PDFPage]:
    """Extrai texto selecionável e marca páginas insuficientes para OCR.

    Uma falha de extração em uma página não aborta as demais: a página é
    marcada como ``ocr_pendente`` e a mensagem fica disponível em
    ``erro_extracao`` para diagnóstico pelo pipeline.
    """
    pdf_path = Path(path)
    if min_chars < 0:
        raise ValueError("min_chars deve ser maior ou igual a zero")
    if not pdf_path.is_file():
        raise PDFProcessingError(f"PDF não encontrado: {pdf_path}")

    try:
        reader = PdfReader(str(pdf_path))
    except (PdfReadError, OSError, ValueError) as exc:
        raise PDFProcessingError(f"Falha ao abrir o PDF: {pdf_path.name}") from exc

    pages: list[PDFPage] = []
    for number, page in enumerate(reader.pages, start=1):
        extraction_error: str | None = None
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:  # pypdf pode lançar erros específicos por página.
            text = ""
            extraction_error = f"{type(exc).__name__}: {exc}"

        method = (
            "extracao_direta"
            if _meaningful_char_count(text) >= min_chars
            else "ocr_pendente"
        )
        pages.append(
            {
                "pagina": number,
                "texto": text,
                "metodo": method,
                "erro_extracao": extraction_error,
            }
        )

    return pages
