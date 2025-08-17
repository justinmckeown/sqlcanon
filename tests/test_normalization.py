from sqlcanon import Canonicalizer, Config


def test_idempotent_normalise():
    c = Canonicalizer()
    q = "select a from t where a in (2,1) and b=1"
    once = c.normalise(q)
    twice = c.normalise(once)
    assert twice == once


def test_hash_equal_for_case_insensitive_equivalents():
    c = Canonicalizer()
    q1 = "select a from t where b = 1"
    q2 = "SeLeCt a FROM t WHERE b = 1"
    assert c.hash(q1) == c.hash(q2)


def test_keyword_case_config_lower():
    c = Canonicalizer()
    out = c.normalise("SELECT A FROM T", Config(keyword_case="lower"))
    assert "select" in out and "from" in out
