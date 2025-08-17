from __future__ import annotations

from pathlib import Path

import pytest

from sqlcanon import Canonicalizer, Config


def _norm(c: Canonicalizer, sql: str, cfg: Config | None = None) -> str:
    if hasattr(c, "normalize"):
        return c.normalise(sql, cfg)
    return c.normalise(sql, cfg)  # type: ignore[attr-defined]


BASE = Path(__file__).parent / "golden"


@pytest.mark.parametrize("profile", ["default", "exec"])
def test_golden_profile(profile: str):
    inputs = BASE / profile / "inputs"
    expected = BASE / profile / "expected"
    cfg = (
        Config()
        if profile == "default"
        else Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])
    )
    canon = Canonicalizer()

    for in_path in sorted(inputs.glob("*.sql")):
        exp_path = expected / in_path.name
        assert exp_path.exists(), f"Missing expected for {in_path.name}"
        q = in_path.read_text(encoding="utf-8")
        out = _norm(canon, q, cfg)
        want = exp_path.read_text(encoding="utf-8")
        assert out == want, f"{in_path.name} did not match expected output.\nGot:\n{out}\nExpected:\n{want}"
