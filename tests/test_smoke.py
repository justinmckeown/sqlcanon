from sqlcanon import Canonicalizer


def test_basic_normalize():
    c = Canonicalizer()
    out = c.normalise("select a from t where a in (2,1) and b=1")
    assert "SELECT" in out
