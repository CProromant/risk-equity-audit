import numpy as np

from riskaudit.audit import label_blend_frontier, top_k_capture


def test_blend_extremes_recover_each_label():
    need = [4, 3, 2, 1]
    a = [4, 3, 2, 1]  # ranks need well
    b = [1, 2, 3, 4]  # ranks need backwards
    df = label_blend_frontier(a, b, need, k=0.5, alphas=[0.0, 1.0], n_boot=100)

    assert df.loc[1.0, "capture"] == top_k_capture(a, need, k=0.5).value == 0.7
    assert df.loc[0.0, "capture"] == top_k_capture(b, need, k=0.5).value == 0.3


def test_blend_group_shares_sum_to_one():
    need = [4, 3, 2, 1, 4, 3, 2, 1]
    a = [8, 7, 6, 5, 4, 3, 2, 1]
    b = [1, 2, 3, 4, 5, 6, 7, 8]
    groups = ["x", "x", "y", "y", "x", "y", "x", "y"]
    df = label_blend_frontier(a, b, need, k=0.5, groups=groups, alphas=[0.0, 0.5, 1.0], n_boot=50)

    shares = df[["share_x", "share_y"]].sum(axis=1)
    assert np.allclose(shares, 1.0)
    assert {"share_x", "share_y"} <= set(df.columns)


def test_blend_groups_length_mismatch_raises():
    import pytest

    with pytest.raises(ValueError, match="length mismatch"):
        label_blend_frontier([1, 2, 3], [3, 2, 1], [1, 2, 3], k=0.5, groups=["a", "b"])
