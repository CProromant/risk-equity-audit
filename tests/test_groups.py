import numpy as np

from riskaudit.audit import group_capture


def test_group_capture_separates_well_and_poorly_ranked_groups():
    # "aligned": score tracks need -> high capture; "reversed": score fights need -> low.
    scores = [4, 3, 2, 1, 1, 2, 3, 4]
    need = [4, 3, 2, 1, 4, 3, 2, 1]
    groups = ["aligned"] * 4 + ["reversed"] * 4
    df = group_capture(scores, need, groups, k=0.5, n_boot=200)

    # top-2 of each group by weight: aligned keeps units {0,1} (need 7/10), reversed
    # keeps the two lowest-need units (3/10). Both graded against the same 0.7 oracle.
    assert df.loc["aligned", "capture"] == 0.7
    assert df.loc["reversed", "capture"] == 0.3
    assert df.loc["aligned", "oracle"] == df.loc["reversed", "oracle"] == 0.7
    assert (df["floor"] == 0.5).all()
    assert df.loc["aligned", "n"] == 4


def test_group_capture_singleton_group_ci_is_finite():
    # A one-member group exercises the domain-bootstrap path where a resample misses it.
    scores = [5, 4, 3, 2, 1]
    need = [1, 2, 3, 4, 5]
    groups = ["big", "big", "big", "big", "solo"]
    df = group_capture(scores, need, groups, k=0.5, n_boot=300)
    assert df.loc["solo", "n"] == 1
    assert df.loc["solo", "capture"] == 1.0  # its own need is all of its need
    assert np.isfinite(df.loc["solo", "ci_lo"]) and np.isfinite(df.loc["solo", "ci_hi"])


def test_group_capture_length_mismatch_raises():
    import pytest

    with pytest.raises(ValueError, match="length mismatch"):
        group_capture([1, 2, 3], [1, 2, 3], ["a", "b"], k=0.5)
