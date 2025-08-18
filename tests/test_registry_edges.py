import pytest

from sqlcanon import Canonicalizer


def test_unknown_pass_raises():
    c = Canonicalizer(passes=["does_not_exist"])
    with pytest.raises(KeyError):
        c.normalise("select 1")


def test_uk_us_pass_alias_equivalence():
    uk = Canonicalizer(passes=["case_keywords", "sort_in_list", "normalise_predicates"])
    us = Canonicalizer(passes=["case_keywords", "sort_in_list", "normalize_predicates"])
    q = "select * from t where b=1 and a in (3,2,1) and c='x'"
    assert uk.normalise(q) == us.normalise(q)
