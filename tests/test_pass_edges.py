from sqlcanon import Canonicalizer, Config


def test_sort_in_list_strings():
    c = Canonicalizer(passes=["sort_in_list"])
    out = c.normalise("select * from t where a in ('b','A','a') and b=1", Config(passes=["sort_in_list"]))
    assert "A', 'a', 'b" in out or "a', 'b', 'A" in out  # accept either case-insensitive order


def test_predicates_with_or_not_reordered():
    c = Canonicalizer(passes=["normalise_literals", "normalise_predicates"])
    q = "select * from t where a=1 or b=2 and c=3"
    out = c.normalise(q)
    s = out.lower()
    # NOTE: Should not reorder across OR, and literals should be scrubbed
    assert s.startswith("select * from t where a=__num__ or")
    assert " or b=__num__ and c=__num__" in s
    # assert "OR b=__NUM__ AND c=__NUM__" in out or "or b=__NUM__ and c=__NUM__" in out.lower()
