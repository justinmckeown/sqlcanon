from __future__ import annotations

from pathlib import Path

from sqlcanon import Canonicalizer
from sqlcanon.config.loader import load_config_file


def test_load_config_top_level(tmp_path: Path):
    cfg_toml = tmp_path / "config.toml"
    cfg_toml.write_text(
        """
keyword_case = "lower"
passes = ["case_keywords", "sort_in_list"]
"""
    )

    cfg = load_config_file(cfg_toml)
    c = Canonicalizer()
    out = c.normalise("SELECT * FROM t WHERE a IN (3,1,2)", cfg)
    # lower-case keywords & sorted IN list
    assert "select" in out and "in (1, 2, 3)" in out.lower()


def test_load_config_under_table(tmp_path: Path):
    cfg_toml = tmp_path / "config2.toml"
    cfg_toml.write_text(
        """
[sqlcanon]
keyword_case = "upper"
passes = ["case_keywords"]
"""
    )

    cfg = load_config_file(cfg_toml)
    c = Canonicalizer()
    out = c.normalise("select * from t where a in (3,1,2)", cfg)
    # only case-folding pass active; IN list should remain unsorted
    assert "SELECT" in out
    assert "IN (3,1,2)" in out or "in (3,1,2)" in out
