# 🧩 Integrations Guide

Practical patterns for using `sqlcanon` in real projects.

> **Profiles:**  
> - **Execution‑safe** (send to DB): ["case_keywords", "sort_in_list", "normalize_predicates"]  
> - **Cache/dedupe** (do not execute): add "normalize_literals"

---

## SQLAlchemy (event hook)

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

**Notes**
- Works with bound params (`:param`) untouched.
- Keep the `Canonicalizer` instance around; it’s stateless and cheap to reuse.

---

## Psycopg (sync) helper

```python
def exec_norm(cur, sql, params=None):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return cur.execute(canon.normalize(sql, cfg), params or ())
```

## asyncpg helper

```python
async def exec_norm_async(conn, sql, *args):
    from sqlcanon import Canonicalizer, Config
    canon = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    return await conn.execute(canon.normalize(sql, cfg), *args)
```

---

## FastAPI microservice

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

**Usage**
```bash
curl -X POST http://localhost:8000/normalise   -H "content-type: application/json"   -d '{"sql":"select * from t where a in (3,2,1) and b=1"}'
```

---

## Observability (timings)

```python
import logging
from time import perf_counter
from sqlcanon import Canonicalizer, Config

log = logging.getLogger("sqlcanon")

canon = Canonicalizer()
cfg = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])

def normalise_timed(sql: str) -> str:
    t0 = perf_counter()
    out = canon.normalize(sql, cfg)
    log.debug("normalise took %.2f ms", (perf_counter() - t0) * 1000.0)
    return out
```

---

## UK 🇬🇧 vs US 🇺🇸 spelling

Expose both spellings for ergonomics:

```python
class Canonicalizer:
    def normalise(self, sql, cfg=None):  # UK alias
        return self.normalize(sql, cfg)
```

CLI alias:
```bash
sqlcanon normalise "select ..."
# equals
sqlcanon normalize "select ..."
```

---

## Safety checklist

- ✅ Exclude `normalize_literals` when executing the output.  
- ✅ Keep transforms deterministic and conservative.  
- ✅ Add tests for idempotence & safety for any new pass.
