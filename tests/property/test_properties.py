from __future__ import annotations

import re

from hypothesis import given
from hypothesis import strategies as st

from sqlcanon import Canonicalizer, Config


def _norm(c: Canonicalizer, sql: str, cfg: Config | None = None) -> str:
    # Support UK/US method names if the user renamed them
    if hasattr(c, "normalize"):
        return c.normalise(sql, cfg)
    return c.normalise(sql, cfg)  # type: ignore[attr-defined]


def _sql_identifier() -> st.SearchStrategy[str]:
    start = st.sampled_from(list("abcdefghijklmnopqrstuvwxyz_"))
    rest = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=0, max_size=8)
    return st.builds(lambda s, r: s + r, start, rest)


def _int_literal() -> st.SearchStrategy[str]:
    return st.integers(min_value=0, max_value=9999).map(str)


def _string_literal() -> st.SearchStrategy[str]:
    # simple single-quoted strings without backslashes; double single-quote escapes
    inner = st.text(alphabet=st.characters(blacklist_characters="'\n\r"), min_size=0, max_size=8)
    return inner.map(lambda s: "'" + s.replace("'", "''") + "'")


def _in_list(values: st.SearchStrategy[str]) -> st.SearchStrategy[str]:
    return st.lists(values, min_size=1, max_size=5).map(lambda xs: "(" + ", ".join(xs) + ")")


def _predicate(cols: st.SearchStrategy[str]) -> st.SearchStrategy[str]:
    simple_cmp = st.builds(lambda c, v: f"{c} = {v}", cols, st.one_of(_int_literal(), _string_literal()))
    in_clause = st.builds(
        lambda c, lst: f"{c} IN {lst}", cols, _in_list(st.one_of(_int_literal(), _string_literal()))
    )
    return st.one_of(simple_cmp, in_clause)


def _where_clause() -> st.SearchStrategy[str]:
    cols = _sql_identifier()
    term = _predicate(cols)
    # Build up to 4 AND-joined terms, optionally wrapped with an OR to test safety behaviour.
    and_chain = st.lists(term, min_size=1, max_size=4).map(lambda ts: " AND ".join(ts))
    maybe_or = st.one_of(
        and_chain,
        st.builds(lambda left, right: f"{left} OR {right}", and_chain, and_chain),
    )
    return maybe_or


def _select_query() -> st.SearchStrategy[str]:
    cols = st.lists(_sql_identifier(), min_size=1, max_size=3).map(lambda xs: ", ".join(xs))
    table = _sql_identifier()
    where = _where_clause()
    # allow noisy spacing and weird keyword casing
    kw_select = st.sampled_from(["select", "SELECT", "SeLeCt"])
    kw_from = st.sampled_from(["from", "FROM", "FrOm"])
    kw_where = st.sampled_from(["where", "WHERE", "WhErE"])
    spaces = st.text(alphabet=" ", min_size=1, max_size=3)
    return st.builds(
        lambda ks, c, sf, t, sw, w, s1, s2: f"{ks}{s1}{c}{s1}{sf}{s1}{t}{s2}{sw}{s1}{w}",
        kw_select,
        cols,
        kw_from,
        table,
        kw_where,
        where,
        spaces,
        spaces,
    )


def _upper_only_keywords(sql: str) -> str:
    # Upper-case only SQL keywords; leave identifiers & literals alone.
    KW = r"\b(select|from|where|and|or|in|group|by|order|limit|join|on|as)\b"
    return re.sub(KW, lambda m: m.group(1).upper(), sql, flags=re.IGNORECASE)


@given(_select_query())
def test_normalise_idempotent(query: str):
    c = Canonicalizer()
    cfg = Config()  # default passes
    once = _norm(c, query, cfg)
    twice = _norm(c, once, cfg)
    assert once == twice


@given(_select_query())
def test_hash_invariant_under_keyword_case(query: str):
    c = Canonicalizer()
    cfg = Config()
    # uppercase keywords version
    q_upper = _upper_only_keywords(query)
    assert c.hash(query, cfg) == c.hash(q_upper, cfg)


@given(st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=6))
def test_in_list_sorted_for_exec_profile(nums):
    # Build a simple query with an IN list of integers
    values = ", ".join(map(str, nums))
    q = f"select * from t where a in ({values})"
    c = Canonicalizer()
    cfg = Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])  # exec-safe

    out = _norm(c, q, cfg).lower()
    # Extract the part inside IN (...), split, and compare sorted numerically as strings
    import re

    m = re.search(r"in\s*\(([^()]*)\)", out, flags=re.IGNORECASE)
    assert m, out
    got = [x.strip() for x in m.group(1).split(",") if x.strip()]
    want = [str(x) for x in sorted(nums)]
    assert got == want
