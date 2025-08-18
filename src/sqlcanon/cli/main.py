from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer

from .. import Canonicalizer, Config
from ..config.loader import load_config_file

app = typer.Typer(help="sqlcanon — SQL Query Canonicalizer")

KeywordCase = Literal["upper", "lower"]


# helper to coerce/narrow a str|None into our KeywordCase|None - mypy is quite strict
def _coerce_keyword_case(val: str | None) -> KeywordCase | None:
    if val is None:
        return None
    v = val.lower()
    if v == "upper":
        return "upper"
    if v == "lower":
        return "lower"
    raise typer.BadParameter("keyword-case must be 'upper' or 'lower'")


def _load_cfg(config_path: Path | None, keyword_case: KeywordCase | None) -> Config:
    cfg = load_config_file(config_path) if config_path else Config()
    if keyword_case is not None:
        cfg = Config(
            keyword_case=keyword_case,
            identifier_case=cfg.identifier_case,
            passes=cfg.passes,
            hash_strategy=cfg.hash_strategy,
        )
    return cfg


@app.command()
def normalize(
    query: str,
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to a TOML config"),
    keyword_case: str | None = typer.Option(
        None, "--keyword-case", "-k", help="Override: 'upper' or 'lower'"
    ),
):
    """Normalize (UK spelling supported internally) a SQL query to canonical form."""
    cfg = _load_cfg(config, _coerce_keyword_case(keyword_case))
    canon = Canonicalizer()
    print(canon.normalise(query, cfg))  # call the UK method you implemented


@app.command("normalise")
def normalise_cmd(
    query: str,
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to a TOML config"),
    keyword_case: str | None = typer.Option(
        None, "--keyword-case", "-k", help="Override: 'upper' or 'lower'"
    ),
):
    """Normalise a SQL query to canonical form."""
    cfg = _load_cfg(config, _coerce_keyword_case(keyword_case))
    canon = Canonicalizer()
    print(canon.normalise(query, cfg))


@app.command()  # noqa: A003
def hash(
    query: str,
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to a TOML config"),
    keyword_case: str | None = typer.Option(
        None, "--keyword-case", "-k", help="Override: 'upper' or 'lower'"
    ),
):
    """Compute a stable equivalence hash for a SQL query."""
    cfg = _load_cfg(config, _coerce_keyword_case(keyword_case))
    canon = Canonicalizer()
    print(canon.hash(query, cfg))


def run():
    app()


if __name__ == "__main__":
    run()
