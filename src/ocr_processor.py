"""OCR de páginas rasterizadas, com dependências carregadas sob demanda."""
from __future__ import annotations

from pathlib import Path


class OCRProcessingError(RuntimeError):
    """Erro de infraestrutura ou execução do mecanismo de OCR."""


def _select_language(pytesseract_module, requested: str) -> str:
    """Seleciona o idioma solicitado e, quando disponível, combina inglês.

    Os documentos oficiais possuem rótulos em português, mas campos como
    e-mail e identificadores usam muitos símbolos ASCII. A combinação
    ``por+eng`` melhora a leitura desses símbolos sem abandonar o idioma
    definido em ``config.json``. Se o idioma solicitado não estiver instalado,
    usa inglês apenas como fallback técnico.
    """
    available = set(pytesseract_module.get_languages(config=""))
    if requested in available:
        if requested != "eng" and "eng" in available:
            return f"{requested}+eng"
        return requested
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
    """Converte uma única página do PDF em imagem e retorna o texto OCR bruto.

    O texto retornado não é normalizado aqui, preservando a evidência bruta do
    OCR. Limpeza e padronização são responsabilidades das etapas seguintes.
    """
    if page_number < 1:
        raise ValueError("page_number deve começar em 1")
    if dpi <= 0:
        raise ValueError("dpi deve ser positivo")

    path = Path(pdf_path)
    if not path.is_file():
        raise OCRProcessingError(f"PDF não encontrado para OCR: {path}")

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise OCRProcessingError(
            "Instale pdf2image e pytesseract para executar OCR"
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
            f"Falha ao rasterizar {path.name}, página {page_number}"
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
