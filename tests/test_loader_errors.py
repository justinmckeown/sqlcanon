from pathlib import Path

import pytest

from sqlcanon.config.loader import ConfigError, load_config_file


def test_load_config_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config_file(tmp_path / "nope.toml")


def test_load_config_unknown_key(tmp_path: Path):
    p = tmp_path / "bad.toml"
    p.write_text('unknown = "x"\n', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config_file(p)


def test_load_config_passes_wrong_type(tmp_path: Path):
    p = tmp_path / "bad2.toml"
    p.write_text('passes = "oops"\n', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config_file(p)
