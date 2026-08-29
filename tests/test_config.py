import json
from pathlib import Path

import pytest

from src.config import ConfigError, load_config


def test_default_config_loads_project_root():
    cfg = load_config()
    root = Path(cfg["_root"])
    assert (root / "config.json").is_file()
    assert cfg["entrada"]["diretorio_pdfs"] == "data/pdfs"


def test_missing_required_section_is_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"entrada": {}}), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)
