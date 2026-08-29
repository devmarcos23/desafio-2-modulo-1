from pathlib import Path
import shutil

import pytest

from src.config import load_config
from src.ocr_processor import check_ocr_dependencies
import src.pipeline as pipeline


@pytest.mark.integration
def test_official_dataset_has_100_records_and_25_ocr(monkeypatch, tmp_path):
    if check_ocr_dependencies():
        pytest.skip("Tesseract/Poppler não disponíveis")

    project = Path(load_config()["_root"])
    sandbox = tmp_path / "project"
    shutil.copytree(project / "data", sandbox / "data")
    shutil.copy(project / "config.json", sandbox / "config.json")

    cfg = load_config(sandbox / "config.json")
    monkeypatch.setattr(pipeline, "lookup_cep", lambda *a, **k: None)
    frame = pipeline.process_all(cfg, reset=True)

    assert len(frame) == 100
    assert int((frame["metodo"] == "ocr").sum()) == 25
    assert frame["documento"].nunique() == 4
    assert set(frame[frame["documento"] == "atendimentos_duplicados.pdf"]["classificacao"]) == {"duplicado"}

    # Reexecução deve reconstruir a mesma visão a partir do banco, sem zerar outputs.
    rerun = pipeline.process_all(cfg)
    assert len(rerun) == 100
