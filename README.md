# 🚀 sqlcanon — SQL Query Canonicalizer

Normalise semantically equivalent SQL into a canonical form for diffing, caching, duplicate detection, and privacy research. Library + CLI. Built with Python, OOP, and SOLID design principles.

[![CI](https://github.com/justinmckeown/sqlcanon/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/justinmckeown/sqlcanon/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
![Lint: ruff](https://img.shields.io/badge/lint-ruff-informational)
![Types: mypy](https://img.shields.io/badge/types-mypy-informational)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)


---




## 🧭 Overview

`sqlcanon` helps teams compare, deduplicate, and cache SQL by transforming queries into a **stable, canonical form**. It exposes both a **Python API** and a **CLI** so you can integrate it into apps, ETL jobs, or CI checks, or use it for privacy research.

**Use‑cases**  
- Detect duplicates across dashboards/ETL jobs  
- Drive query‑result caching keys  
- Normalise logs for privacy research (e.g., literal scrubbing)  
- Produce clean diffs in code review

---

## 🔒 Real‑world example: Privacy‑safe query caching & usage analytics

### The problem
Warehouses get hammered by *nearly identical* queries from BI tools and services. Tiny differences (keyword case, spacing, `IN (3,2,1)` vs `IN (1,3,2)`, literal values like emails or IDs) cause **cache misses** and **duplicate compute**. Storing raw SQL for dedupe/metrics is **privacy‑risky** because it may contain PII.

### The idea
Use `sqlcanon` to **normalise** each query into a canonical form and compute a **hash**.  
- Use the **hash** as a cache key (so equivalent queries share results).  
- Log **only** the hash (and optionally the canonical form with literals scrubbed to `__NUM__` / `'__STR__'`) for privacy‑safe analytics.

### Before → After (what normalisation does)
```
-- two “different” user queries:
select  a from t where  b=1  and a in (3,2,1) and c='alice@example.com'
SELECT A FROM T WHERE A IN (1, 3, 2) AND b = 1 AND c = 'ALICE@EXAMPLE.COM'

-- canonical (default profile)
SELECT a FROM t WHERE a IN (__NUM__, __NUM__, __NUM__) AND b=__NUM__ AND c='__STR__'

-- same SHA-256 hash for both (example)
e643d975db57…471fc
```

### Minimal integration (SQLAlchemy)
```python
from sqlalchemy import create_engine, event
from sqlcanon import Canonicalizer, Config

# Cache interface (pseudo); plug in Redis/Memcached/etc.
class Cache:
    def get(self, key: str): ...
    def set(self, key: str, value: bytes, ttl: int = 60): ...

cache = Cache()

canon = Canonicalizer()
# “hashing” profile: safe to store, not to execute
cfg_hash = Config(passes=["case_keywords", "normalize_literals", "sort_in_list", "normalize_predicates"])

engine = create_engine("postgresql+psycopg://…")

@event.listens_for(engine, "before_cursor_execute")
def maybe_cache(conn, cursor, statement, parameters, context, executemany):
    canonical = canon.normalise(statement, cfg_hash)
    key = canon.hash(statement, cfg_hash)

    hit = cache.get(key)
    if hit is not None:
        # (implementation-specific) stash cached rows on the context
        context._result_cache = hit
        return statement, parameters

    # Let DB run; in an "after execute" hook (or your data access layer),
    # store the result rows under `key` with a TTL, and log just the hash:
    #   cache.set(key, serialize(rows), ttl=60)
    #   log.info("sql_hash=%s canonical=%s", key, canonical)

    return statement, parameters
```

> ✅ **Privacy by design:** Logs contain only the **hash** and a **scrubbed** canonical (no raw literal values).  
> ✅ **Cost & latency:** Equivalent queries now **hit the same cache key** instead of re‑running.

### CLI demo (try locally)
```bash
# default normalisation (keywords, literal scrubbing, IN/AND ordering)
sqlcanon normalise "select * from t where b=1 and a in (3,2,1) and c='x'"

# exec‑safe profile (keep literals; still normalise structure)
# .sqlcanon.exec.toml:
# passes = ["case_keywords", "sort_in_list", "normalize_predicates"]
sqlcanon normalise -c .sqlcanon.exec.toml "select * from t where a in (3,1,2) and b=1"
```

### What you can measure (without raw SQL)
- **Unique queries** (by hash) and their **frequency**
- **Top query shapes** over time (scrubbed canonical forms)
- **Hot spots** (e.g., “IN list sort” fixes a flood of near‑duplicates)
- **Anomalies** (sudden surge in a canonical query)

> **Notes & guardrails**
> - Don’t **execute** canonical SQL from the hashing profile (placeholders change semantics). Use the exec‑safe profile for execution‑adjacent tooling.
> - You can optionally **salt** the hash before storage if you need to prevent cross‑dataset linkage.
> - For table/column stats, pair `sqlcanon` with a parser like `sqlglot` in a separate analytics step.

---

## ✨ Features

- **Parser abstraction** via a lightweight adapter (swappable later)
- **Normalisation pipeline** with focused passes (SRP):
  - `case_keywords` — standardise keyword case (UPPER/lower)
  - `normalize_literals` / `normalise_literals` — replace string/numeric literals with placeholders
  - `sort_in_list` — deterministically sort `IN (...)` lists
  - `normalize_predicates` / `normalise_predicates` — sort top‑level `AND` terms (skips if `OR` is present for safety)
- **Configurable via TOML** (top‑level keys or `[sqlcanon]` table)
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
# Normalise a query
sqlcanon normalise "select a from t where a in (3,2,1) and b=1"

# Hash the canonical form
sqlcanon hash "select a from t where a in (1,3,2) and b=1"

# Use a config file
sqlcanon normalise -c .sqlcanon.toml "select a from t where a in (3,2,1)"
```

### Python API

```python
from sqlcanon import Canonicalizer, Config

canon = Canonicalizer()
cfg = Config()  # or load from TOML via the CLI

sql = "select a from t where b=1 and a in (3,2,1)"
print(canon.normalise(sql, cfg))   # UK spelling (alias available)
print(canon.hash(sql, cfg))
```

---

## 🧰 Configuration

Create `.sqlcanon.toml` at your project root. You can place keys at the top level or under a `[sqlcanon]` table.

**Top‑level keys**
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
sqlcanon normalise -c .sqlcanon.toml "select a from t where a in (3,2,1) and b=1"
```

---

## 🧩 Integrations (practical usage)

For a deeper guide, see **docs/INTEGRATIONS.md**. Highlights:

### SQLAlchemy (auto‑normalise before execution)
```python
from sqlalchemy import create_engine, event
from sqlcanon import Canonicalizer, Config

engine = create_engine("postgresql+psycopg://…")
canon = Canonicalizer()
cfg_exec = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])

@event.listens_for(engine, "before_cursor_execute")
def normalise_before_execute(conn, cursor, statement, parameters, context, executemany):
    statement = canon.normalise(statement, cfg_exec)
    return statement, parameters
```

### Psycopg / asyncpg helpers
```python
def exec_norm(cur, sql, params=None):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return cur.execute(canon.normalise(sql, cfg), params or ())

async def exec_norm_async(conn, sql, *args):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return await conn.execute(canon.normalise(sql, cfg), *args)
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
    out = canon.normalise(payload.sql, cfg)
    return {"canonical_sql": out, "hash": canon.hash(payload.sql, cfg)}
```

> ⚠️ **Executing canonical SQL?** Exclude `normalize_literals` (otherwise placeholders like `__NUM__` / `'__STR__'` will change semantics). Include it for **hashing/deduplication**.

---

## 🇬🇧🇺🇸 UK/US spelling aliases

`sqlcanon` supports both spellings for developer ergonomics:

- **Methods**
  ```python
  canon.normalize(sql)   # US
  canon.normalise(sql)   # UK (alias of normalize)
  ```

- **CLI**
  ```bash
  sqlcanon normalize  "select * from t where …"
  sqlcanon normalise  "select * from t where …"  # alias of `normalize`
  ```

- **Pass names (config & code)**  
  Pass registry accepts either spelling where applicable:
  ```toml
  # .sqlcanon.toml (both work)
  passes = ["case_keywords", "sort_in_list", "normalize_predicates"]
  # or
  passes = ["case_keywords", "sort_in_list", "normalise_predicates"]
  ```

  ```python
  # Python (both work)
  Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
  Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])
  ```

**How it works:** pass names are resolved through a small alias map (e.g., `normalise_*` ↔ `normalize_*`) before lookup. If a name isn’t recognised after alias resolution, a clear `KeyError` is raised.

**Tip:** pick one spelling for your codebase (e.g., UK in source), and use whichever spelling feels natural in configs/CLI—both are accepted.

**Troubleshooting:**  
If you see `KeyError: 'normalize_predicates'` (or the UK equivalent):
- ensure the pass is registered in the project’s pass registry,
- check for typos, and
- update to the latest version if you recently added alias support.

---

## 🧪 Testing & Quality

```bash
# Run tests
pytest -q

# Lint (auto‑fix where possible) & format
ruff check . --fix
ruff format .

# Type‑check
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
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip
      - run: pip install -e .[dev] hypothesis pytest-cov pytest-benchmark
      - name: Ruff (lint & format check)
        run: |
          ruff check .
          ruff format --check .
      - name: Mypy
        run: mypy src/sqlcanon
      - name: Tests (with coverage)
        run: pytest -q --cov=src/sqlcanon --cov-report=term-missing --cov-fail-under=85
```

---

## 🧩 Pass Catalogue

- **`case_keywords`**  
  Upper‑ or lower‑cases SQL keywords (`SELECT`, `FROM`, `WHERE`, …).

- **`normalize_literals` / `normalise_literals`**  
  Replaces numeric literals with `__NUM__` and string literals with `'__STR__'`. This makes queries comparable without leaking literal values. Example:  
  `WHERE price = 9.99 AND note = 'Hello'` → `WHERE price = __NUM__ AND note = '__STR__'`

- **`sort_in_list`**  
  Sorts items inside `IN (...)` lists; handles quoted strings and numbers. Mixed types are ordered numerically first, then strings (case‑insensitive).

- **`normalize_predicates` / `normalise_predicates`**  
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
- Additional passes: identifier case, alias normalisation, commutativity for `OR` (structure‑aware)
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
 