from pathlib import Path

from src.pdf_processor import extract_pdf_pages

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdfs"


def test_pdf_digital_uses_direct_extraction():
    pages = extract_pdf_pages(PDF_DIR / "atendimentos_digitais.pdf", min_chars=40)
    assert len(pages) == 13
    assert all(page["metodo"] == "extracao_direta" for page in pages)
    assert all(page["texto"] for page in pages)


def test_scanned_pdf_is_sent_to_ocr():
    pages = extract_pdf_pages(PDF_DIR / "atendimentos_digitalizados.pdf", min_chars=40)
    assert len(pages) == 7
    assert all(page["metodo"] == "ocr_pendente" for page in pages)
