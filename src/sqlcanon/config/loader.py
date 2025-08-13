from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

from .model import Config


class ConfigError(ValueError):
    pass


def _validate_table(data: Mapping[str, Any]) -> None:
    allowed = {"keyword_case", "identifier_case", "passes", "hash_strategy"}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise ConfigError(f"Unknown config keys: {sorted(unknown)}")


def load_config_file(path: str | Path) -> Config:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    if tomllib is None:  # pragma: no cover
        raise RuntimeError("tomllib not available; use Python 3.11+ or install `tomli`.")

    with p.open("rb") as f:
        raw = tomllib.load(f)

    if not isinstance(raw, dict):
        raise ConfigError("Top-level TOML must be a table/object.")

    # Support either top-level keys or a [sqlcanon] table
    table: Mapping[str, Any]
    if "sqlcanon" in raw and isinstance(raw["sqlcanon"], dict):
        table = raw["sqlcanon"]
    else:
        table = raw

    _validate_table(table)

    keyword_case = table.get("keyword_case", "upper")
    identifier_case = table.get("identifier_case", "as_is")
    passes = table.get("passes")
    hash_strategy = table.get("hash_strategy", "sha256")

    if passes is not None and not isinstance(passes, list):
        raise ConfigError("'passes' must be a list of strings")

    return Config(
        keyword_case=keyword_case,
        identifier_case=identifier_case,
        passes=passes,  # list[str] | None
        hash_strategy=hash_strategy,
    )
