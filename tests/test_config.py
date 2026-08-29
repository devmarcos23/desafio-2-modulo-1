import json
from pathlib import Path

import pytest

from src.config import ConfigError, load_config, resolve


def test_load_project_config():
    cfg = load_config()
    assert cfg["entrada"]["diretorio_pdfs"] == "data/pdfs"
    assert Path(cfg["_root"]).is_dir()


def test_resolve_relative_and_absolute(tmp_path):
    assert resolve(tmp_path, "data") == tmp_path / "data"
    absolute = tmp_path / "x"
    assert resolve("/outra", absolute) == absolute


def test_invalid_config_reports_missing_sections(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"entrada": {}}), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)
