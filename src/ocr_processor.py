"""OCR de páginas rasterizadas com Tesseract e Poppler/pdf2image."""
from __future__ import annotations

from pathlib import Path
import shutil


class OCRProcessingError(RuntimeError):
    """Erro de infraestrutura ou execução do OCR."""


def check_ocr_dependencies() -> list[str]:
    """Retorna dependências externas ausentes no PATH.

    ``pdf2image`` usa ferramentas Poppler (``pdfinfo``/``pdftoppm``) e
    ``pytesseract`` usa o executável ``tesseract``.
    """
    missing: list[str] = []
    if shutil.which("tesseract") is None:
        missing.append("Tesseract (tesseract)")
    if shutil.which("pdfinfo") is None and shutil.which("pdftoppm") is None:
        missing.append("Poppler (pdfinfo/pdftoppm)")
    return missing


def _select_language(pytesseract_module, requested: str) -> str:
    available = set(pytesseract_module.get_languages(config=""))
    if requested in available:
        return f"{requested}+eng" if requested != "eng" and "eng" in available else requested
    if "eng" in available:
        return "eng"
    raise OCRProcessingError(
        f"Idioma do Tesseract indisponível: {requested!r}; inglês também ausente"
    )


def ocr_page(
    pdf_path: str | Path,
    page_number: int,
    dpi: int = 300,
    language: str = "por",
) -> str:
    """Rasteriza uma página e devolve o texto bruto reconhecido pelo Tesseract."""
    if page_number < 1:
        raise ValueError("page_number deve começar em 1")
    if dpi <= 0:
        raise ValueError("dpi deve ser positivo")

    path = Path(pdf_path)
    if not path.is_file():
        raise OCRProcessingError(f"PDF não encontrado para OCR: {path}")

    missing = check_ocr_dependencies()
    if missing:
        raise OCRProcessingError(
            "Dependências externas de OCR ausentes: " + ", ".join(missing)
        )

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise OCRProcessingError(
            "Instale pdf2image e pytesseract com requirements.txt"
        ) from exc

    try:
        images = convert_from_path(
            str(path),
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
            fmt="png",
        )
    except Exception as exc:
        raise OCRProcessingError(
            f"Falha ao rasterizar {path.name}, página {page_number}. "
            "Confirme se o Poppler está instalado e disponível no PATH."
        ) from exc

    if not images:
        raise OCRProcessingError(
            f"Nenhuma imagem gerada para {path.name}, página {page_number}"
        )

    try:
        selected_language = _select_language(pytesseract, language)
        return pytesseract.image_to_string(
            images[0],
            lang=selected_language,
            config="--psm 4",
            timeout=60,
        )
    except OCRProcessingError:
        raise
    except Exception as exc:
        raise OCRProcessingError(
            f"Tesseract falhou em {path.name}, página {page_number}: {exc}"
        ) from exc
