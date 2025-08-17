from fastapi import FastAPI
from pydantic import BaseModel

from sqlcanon import Canonicalizer, Config

app = FastAPI(title="sqlcanon normalise API")

canon = Canonicalizer()
cfg = Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])


class Payload(BaseModel):
    sql: str


@app.post("/normalise")
def normalise(payload: Payload):
    out = canon.normalise(payload.sql, cfg)
    return {"canonical_sql": out, "hash": canon.hash(payload.sql, cfg)}
