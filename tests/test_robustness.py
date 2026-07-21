import numpy as np

from riskaudit.audit import label_robustness


def test_label_robustness_gap_closes_toward_model():
    # the model ranks the one needy unit LAST -> large clean gap
    r = label_robustness(scores=[4, 3, 2, 1], need=[0, 0, 0, 1], k=0.5)
    assert r.gap[0] > r.gap[-1]  # blending need toward the model shrinks the gap
    assert r.model_capture[-1] >= r.model_capture[0]
    assert 0 < r.breakdown <= 1


def test_label_robustness_no_gap_when_scores_equal_need():
    r = label_robustness(scores=[1, 2, 3, 4], need=[1, 2, 3, 4], k=0.5)
    assert abs(r.gap[0]) < 1e-9
    assert np.isnan(r.breakdown)  # nothing to explain away
