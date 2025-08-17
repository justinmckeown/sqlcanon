import re

from sqlcanon import Canonicalizer


def test_normalise_literals_placeholders():
    c = Canonicalizer(passes=["normalise_literals"])
    q = "select * from t where a = 123 and b = 'Hello ''world'''"
    out = c.normalise(q)
    assert "__NUM__" in out
    assert "'__STR__'" in out


def test_sort_in_list_simple():
    c = Canonicalizer(passes=["sort_in_list"])
    q = "select * from t where a in (3, 1, 2)"
    out = c.normalise(q)
    assert "IN (1, 2, 3)" in out


def test_sort_in_list_mixed_types():
    c = Canonicalizer(passes=["sort_in_list"])
    q = "select * from t where a in ('b', 10, 'A', 2)"
    out = c.normalise(q)
    # numbers first sorted numerically, then strings case-insensitive
    assert "IN (2, 10, 'A', 'b')" in out


def test_normalise_predicates_and_only():
    c = Canonicalizer(passes=["normalise_predicates"])
    q = "select * from t where b=1 and a in (2,1) and c='x'"
    out = c.normalise(q)
    # terms sorted lexicographically
    assert re.search(
        r"\bwhere\b\s+a in \(2,1\)\s+and\s+b=1\s+and\s+c='x'",
        out,
        flags=re.IGNORECASE,
    )


def test_normalise_predicates_skips_when_or_present():
    c = Canonicalizer(passes=["normalise_predicates"])
    q = "select * from t where a=1 or b=2 and c=3"
    out = c.normalise(q)
    # Should not reorder when OR is present (safety)
    assert out.lower() == q.lower()
