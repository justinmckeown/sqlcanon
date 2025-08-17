# 🚀 sqlcanon — SQL Query Canonicalizer

Normalise semantically equivalent SQL into a canonical form for diffing, caching, duplicate detection, and privacy research. Library + CLI. Built with Python, OOP, and SOLID design principles.

<p align="left">
  <a href="https://github.com/justinmckeown/sqlcanon/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?branch=main"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue">
  <img alt="Lint" src="https://img.shields.io/badge/lint-ruff-informational">
  <img alt="Types" src="https://img.shields.io/badge/types-mypy-informational">
  <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-green">
</p>


---

## 🧭 Overview

`sqlcanon` helps teams compare, deduplicate, and cache SQL by transforming queries into a **stable, canonical form**. It exposes both a **Python API** and a **CLI** so you can integrate it into apps, ETL jobs, or CI checks, or use it for privacy research.

**Use‑cases**  
- Detect duplicates across dashboards/ETL jobs  
- Drive query‑result caching keys  
- Normalize logs for privacy research (e.g., literal scrubbing)  
- Produce clean diffs in code review

---

## ✨ Features

- **Parser abstraction** via a lightweight adapter (swapable later)
- **Normalization pipeline** with focused passes (SRP):
  - `case_keywords` — standardize keyword case (UPPER/lower)
  - `normalise_literals` — replace string/numeric literals with placeholders
  - `sort_in_list` — deterministically sort `IN (...)` lists
  - `normalize_predicates` — sort top‑level `AND` terms (skips if `OR` is present for safety)
- **Configurable via TOML** (top-level keys or `[sqlcanon]` table)
- **Equivalence hash** (SHA‑256) over the canonical form
- **CLI + Python library** with clean interfaces
- **Quality gates**: ruff, mypy, pytest; CI workflow template

---

## ⚙️ Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .[dev]
```

> Requires Python **3.10+**.

---

## 🚀 Quickstart

### CLI

```bash
# Normalize a query
sqlcanon normalize "select a from t where a in (3,2,1) and b=1"

# Hash the canonical form
sqlcanon hash "select a from t where a in (1,3,2) and b=1"

# Use a config file
sqlcanon normalize -c .sqlcanon.toml "select a from t where a in (3,2,1)"
```

### Python API

```python
from sqlcanon import Canonicalizer, Config

canon = Canonicalizer()
cfg = Config()  # or load from TOML via the CLI

sql = "select a from t where b=1 and a in (3,2,1)"
print(canon.normalize(sql, cfg))
print(canon.hash(sql, cfg))
```

---

## 🧰 Configuration

Create `.sqlcanon.toml` at your project root. You can place keys at the top level or under a `[sqlcanon]` table.

**Top-level keys**

```toml
keyword_case = "lower"  # or "upper"
passes = ["case_keywords", "normalize_literals", "sort_in_list", "normalize_predicates"]
hash_strategy = "sha256"
```

**Under a table**

```toml
[sqlcanon]
keyword_case = "upper"
passes = ["case_keywords"]
```

Use via CLI:

```bash
sqlcanon normalize -c .sqlcanon.toml "select a from t where a in (3,2,1) and b=1"
```

---

## 🧩 Integrations (practical usage)

For a deeper guide, see **[docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)**. Highlights:

### SQLAlchemy (auto‑normalise before execution)
```python
from sqlalchemy import create_engine, event
from sqlcanon import Canonicalizer, Config

engine = create_engine("postgresql+psycopg://…")
canon = Canonicalizer()
cfg_exec = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])

@event.listens_for(engine, "before_cursor_execute")
def normalise_before_execute(conn, cursor, statement, parameters, context, executemany):
    statement = canon.normalize(statement, cfg_exec)
    return statement, parameters
```

### Psycopg / asyncpg helpers
```python
def exec_norm(cur, sql, params=None):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return cur.execute(canon.normalize(sql, cfg), params or ())

async def exec_norm_async(conn, sql, *args):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return await conn.execute(canon.normalize(sql, cfg), *args)
```

### FastAPI microservice endpoint
```python
from fastapi import FastAPI
from pydantic import BaseModel
from sqlcanon import Canonicalizer, Config

app = FastAPI()
canon = Canonicalizer()
cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])

class Payload(BaseModel):
    sql: str

@app.post("/normalise")
def normalise(payload: Payload):
    out = canon.normalize(payload.sql, cfg)
    return {"canonical_sql": out, "hash": canon.hash(payload.sql, cfg)}
```

> ⚠️ **Executing canonical SQL?** Exclude `normalize_literals` (otherwise placeholders like `__NUM__` / `'__STR__'` will change semantics). Include it for **hashing/deduplication**.

---

## 🇬🇧 Spelling: “normalise” vs “normalize”

To keep the API friendly in both dialects:

- Library: add a UK alias:
  ```python
  def normalise(self, sql: str, cfg: Config | None = None) -> str:
      return self.normalize(sql, cfg)
  ```
- CLI: add a command alias `normalise` that calls the same implementation as `normalize`.
- Internally, prefer a single canonical spelling in identifiers for consistency; export the other spelling as an alias to avoid breaking changes.

---

## 🏗️ Design & Architecture

- **SOLID**  
  - **S**ingle Responsibility: each normalization pass does one thing.  
  - **O**pen/Closed: add passes without modifying core; register via config.  
  - **L**iskov: any `NormalizationPass` implementation is interchangeable.  
  - **I**nterface Segregation: small, focused protocols (`QueryParser`, `NormalizationPass`, `HashComputer`).  
  - **D**ependency Inversion: `Canonicalizer` depends on abstractions, not concretions.

- **Key abstractions**
  - `QueryParser.parse(sql) -> AstNode`
  - `NormalizationPass.apply(ast, cfg) -> AstNode`
  - `HashComputer.digest(ast, cfg) -> str`
  - `Canonicalizer` (facade): parser → passes → hash

- **Pass pipeline**  
  Deterministic sequence of passes. The default pipeline is:
  `["case_keywords", "normalize_literals", "sort_in_list", "normalize_predicates"]`

---

## 🗂️ Project Layout

```
repo-root/
  pyproject.toml
  src/
    sqlcanon/
      __init__.py
      protocols.py
      parsing/
        __init__.py
        sqlparse_adapter.py
      passes/
        __init__.py
        base.py
        case_keywords.py
        normalize_literals.py
        sort_in_list.py
        normalize_predicates.py
      hashing/
        __init__.py
        sha256_hash.py
      config/
        __init__.py
        model.py
        loader.py
      cli/
        __init__.py
        main.py
  tests/
    test_smoke.py
    test_normalization_basics.py
    test_passes.py
    test_config_loader.py
```
## 🇬🇧🇺🇸 UK/US spelling aliases
sqlcanon supports both spellings for developer ergonomics:

### Methods

```bash
canon.normalize(sql)   # US
canon.normalise(sql)   # UK (alias of normalize)
```

### CLI

```bash
sqlcanon normalize  "select * from t where …"
sqlcanon normalise  "select * from t where …"  # alias of `normalize`
```

### Pass names (config & code)
Pass registry accepts either spelling where applicable:

```toml
# .sqlcanon.toml (both work)
passes = ["case_keywords", "sort_in_list", "normalize_predicates"]
# or
passes = ["case_keywords", "sort_in_list", "normalise_predicates"]
```

Both of the following work

```python
# Python (both work)
Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])
```

How it works: pass names are resolved through a small alias map (e.g., normalise_* ↔ normalize_*) before lookup. If a name isn’t recognised after alias resolution, a clear KeyError is raised.

**Tip:** pick one spelling for your codebase (e.g., UK in source), and use whichever spelling feels natural in configs/CLI—both are accepted.

#### Troubleshooting:
If you see KeyError: `normalise_predicates` (or the US equivalent):

- ensure the pass is registered in the project’s pass registry,
- check for typos, and
- update to the latest version of this package if you recently added alias support.


---
## 🧪 Testing & Quality

```bash
# Run tests
pytest -q

# Lint (auto-fix where possible) & format
ruff check . --fix
ruff format .

# Type-check
mypy src/sqlcanon
```

### CI (GitHub Actions)

Create `.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip
      - run: pip install -e .[dev]
      - run: ruff check .
      - run: mypy src/sqlcanon
      - run: pytest -q
```

---

## 🧩 Pass Catalog

- **`case_keywords`**  
  Upper‑ or lower‑cases SQL keywords (`SELECT`, `FROM`, `WHERE`, …).

- **`normalize_literals`**  
  Replaces numeric literals with `__NUM__` and string literals with `'__STR__'`. This makes queries comparable without leaking literal values. Example:  
  `WHERE price = 9.99 AND note = 'Hello'` → `WHERE price = __NUM__ AND note = '__STR__'`

- **`sort_in_list`**  
  Sorts items inside `IN (...)` lists; handles quoted strings and numbers. Mixed types are ordered numerically first, then strings (case‑insensitive).

- **`normalize_predicates`**  
  Sorts top‑level `AND` terms in the `WHERE` clause for deterministic order. **Skips** reordering if a top‑level `OR` exists to avoid changing semantics.

> 🛡️ Safety: Passes are designed to be conservative. Aggressive transforms (e.g., JOIN reordering) can be added later under opt‑in flags.

---

## 🔢 Equivalence Hash

The CLI/library computes a SHA‑256 digest of the canonical SQL string. This gives a **stable key** for deduplicating queries that differ only in formatting or literal values.

```bash
sqlcanon hash "select a from t where a in (1,3,2) and b=1"
```

---

## 🛣️ Roadmap

- Parser dialect plugins (Postgres/MySQL/SQLite)
- Additional passes: identifier case, alias normalization, commutativity for `OR` (structure‑aware)
- Property‑based tests (Hypothesis)
- Golden tests against sample corpora
- Optional FastAPI microservice + OpenTelemetry tracing

---

## 🤝 Contributing

See **CONTRIBUTING.md** for development workflow, style, and PR checklist.

---

## 📄 License

Apache License 2.0 — see `LICENSE`

---

## 🙌 Acknowledgements

- Built with ❤️ using Python, Typer, Ruff, Mypy, and Pytest.
- Inspired by real‑world needs in data engineering and privacy research.
