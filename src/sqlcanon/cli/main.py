from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .. import Canonicalizer, Config
from ..config.loader import load_config_file

app = typer.Typer(help="sqlcanon — SQL Query Canonicalizer")


def _load_cfg(config_path: Optional[Path], keyword_case: Optional[str]) -> Config:
    if config_path:
        cfg = load_config_file(config_path)
    else:
        cfg = Config()

    # Allow a simple CLI override for keyword case
    if keyword_case in {"upper", "lower"}:
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
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to a TOML config"),
    keyword_case: Optional[str] = typer.Option(
        None, "--keyword-case", "-k", help="Override: 'upper' or 'lower'"
    ),
):
    """Normalize a SQL query to canonical form."""
    cfg = _load_cfg(config, keyword_case)
    canon = Canonicalizer()
    print(canon.normalize(query, cfg))


@app.command("normalise")
def normalise_cmd(
    query: str,
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    keyword_case: Optional[str] = typer.Option(None, "--keyword-case", "-k"),
):
    cfg = _load_cfg(config, keyword_case)
    canon = Canonicalizer()
    print(canon.normalize(query, cfg))



@app.command()
def hash(  # noqa: A003 (function name collides with built-in)
    query: str,
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to a TOML config"),
    keyword_case: Optional[str] = typer.Option(
        None, "--keyword-case", "-k", help="Override: 'upper' or 'lower'"
    ),
):
    """Compute a stable equivalence hash for a SQL query."""
    cfg = _load_cfg(config, keyword_case)
    canon = Canonicalizer()
    print(canon.hash(query, cfg))


def run():
    app()


if __name__ == "__main__":
    run()
