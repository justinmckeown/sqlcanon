# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .model import Config

# Pick a TOML module: stdlib (3.11+) or backport (3.10)
toml_mod: Any | None = None
try:  # Python 3.11+
    import tomllib as _tomllib

    toml_mod = _tomllib
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as _tomli

        toml_mod = _tomli
    except ModuleNotFoundError:
        toml_mod = None  # no TOML parser available


class ConfigError(ValueError):
    pass


def _validate_table(data: Mapping[str, Any]) -> None:
    allowed = {"keyword_case", "identifier_case", "passes", "hash_strategy"}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise ConfigError(f"Unknown config keys: {sorted(unknown)}")


def _loads_toml_bytes(data: bytes) -> Mapping[str, Any]:
    if toml_mod is None:
        raise RuntimeError("TOML parser not available; install Python >=3.11 or 'tomli'.")
    return toml_mod.loads(data.decode("utf-8"))  # both tomllib and tomli expose `loads`


def load_config_file(path: str | Path) -> Config:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    raw = _loads_toml_bytes(p.read_bytes())
    if not isinstance(raw, dict):
        raise ConfigError("Top-level TOML must be a table/object.")

    section = raw.get("sqlcanon")
    table: Mapping[str, Any] = section if isinstance(section, dict) else raw

    _validate_table(table)

    keyword_case = table.get("keyword_case", "upper")
    identifier_case = table.get("identifier_case", "as_is")
    passes_val = table.get("passes")
    hash_strategy = table.get("hash_strategy", "sha256")

    passes: list[str] | None
    if passes_val is None:
        passes = None
    elif isinstance(passes_val, list) and all(isinstance(s, str) for s in passes_val):
        passes = passes_val
    else:
        raise ConfigError("'passes' must be a list of strings")

    return Config(
        keyword_case=keyword_case,
        identifier_case=identifier_case,
        passes=passes,
        hash_strategy=hash_strategy,
    )
