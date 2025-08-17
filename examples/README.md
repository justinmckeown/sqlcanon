# 🧪 sqlcanon — Examples

Practical, runnable examples that show how to use `sqlcanon` in real projects.

## Setup

From your **repo root**:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install the library in editable mode
pip install -e .

# (Optional) Install example-specific deps
pip install -r examples/fastapi_service/requirements.txt
pip install -r examples/psycopg_and_asyncpg/requirements.txt
pip install -r examples/sqlalchemy_hook/requirements.txt
```

> Note: The examples use `canon.normalize(...)`. If you've renamed to UK spelling (`normalise`), swap the call accordingly.

---

## 1) SQLAlchemy Hook (SQLite, zero external deps)

Run:
```bash
python examples/sqlalchemy_hook/app.py
```

What it does:
- Registers a `before_cursor_execute` event that normalises SQL just before execution.
- Uses in-memory SQLite for a no-setup demo.
- Prints the transformed SQL when it changes.

---

## 2) FastAPI Service

Run:
```bash
pip install -r examples/fastapi_service/requirements.txt
uvicorn examples.fastapi_service.app:app --reload
```

Test:
```bash
curl -X POST http://127.0.0.1:8000/normalise   -H "content-type: application/json"   -d '{"sql":"select * from t where a in (3,2,1) and b=1"}'
```

---

## 3) Psycopg & Asyncpg

These show thin wrappers that normalise SQL before execution. They require a running Postgres.

Start Postgres via Docker:
```bash
docker run --rm --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=demo -p 5432:5432 postgres:16
```

Set DSNs (PowerShell):
```powershell
$env:POSTGRES_DSN="postgresql://postgres:postgres@localhost:5432/demo"
$env:ASYNC_PG_DSN="postgres://postgres:postgres@localhost:5432/demo"
```

Run the demos:
```bash
pip install -r examples/psycopg_and_asyncpg/requirements.txt

python examples/psycopg_and_asyncpg/psycopg_example.py
python examples/psycopg_and_asyncpg/asyncpg_example.py
```

Both scripts print the *normalised* SQL and attempt a simple call if the DSN is available.
