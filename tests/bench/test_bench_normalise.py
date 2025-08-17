from __future__ import annotations

import random

from sqlcanon import Canonicalizer, Config


def _norm(c: Canonicalizer, sql: str, cfg: Config | None = None) -> str:
    # UK/US compatibility
    if hasattr(c, "normalize"):
        return c.normalize(sql, cfg)
    return c.normalise(sql, cfg)  # type: ignore[attr-defined]


SEED_QUERIES = [
    "select a from t where b=1 and a in (3,2,1) and c='x'",
    "SeLeCt * FROM orders WHERE status IN ('new','processing','cancelled') AND total > 100",
    "select id, name from users where lower(email) IN ('a@x.com','b@x.com','c@x.com')",
    "select * from t where a=1 or b=2 and c=3",  # OR to exercise safety path
] + [
    # Generate some larger IN lists
    "select * from big where id in (" + ", ".join(map(str, range(n, n + 25))) + ") and shard=1"
    for n in range(50, 100, 10)
]


def test_bench_normalise_default(benchmark):
    c = Canonicalizer()
    cfg = Config()  # default pipeline (includes literal scrubbing)
    data = SEED_QUERIES * 20  # repeat to get a bit more work
    random.shuffle(data)

    def run():
        out = ""
        for q in data:
            out = _norm(c, q, cfg)
        return out  # return something so benchmark can’t skip

    benchmark(run)


def test_bench_normalise_exec_profile(benchmark):
    c = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])
    data = SEED_QUERIES * 20
    random.shuffle(data)

    def run():
        out = ""
        for q in data:
            out = _norm(c, q, cfg)
        return out

    benchmark(run)
