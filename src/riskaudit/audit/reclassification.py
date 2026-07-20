import pandas as pd
from numpy.typing import ArrayLike

from riskaudit.audit._common import check_inputs, to_float, topk_mask, weights_or_ones


def reclassification(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
) -> pd.DataFrame:
    r"""Who enters and leaves the top-``k`` when the label switches from A to B.

    Let :math:`T_k^A` and :math:`T_k^B` be the top-``k`` sets (by weight) under
    scores A and B. The result is the weighted 2x2 contingency of membership,

    ==================  ================  ==================
    .                   in :math:`T_k^B`  not in :math:`T_k^B`
    ==================  ================  ==================
    in :math:`T_k^A`    stay              dropped
    not in :math:`T_k^A`  added           out
    ==================  ================  ==================

    ``added`` are the units a need-based label would prioritize that a
    spend-based one misses — the population cost of the label choice.

    Parameters
    ----------
    scores_a, scores_b : array-like of shape (n,)
        Scores under label A and label B for the same units.
    k : float, default 0.10
        Top fraction, by weight.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.

    Returns
    -------
    pandas.DataFrame
        Weighted counts and shares for stay / dropped / added / out.
    """
    a = to_float(scores_a)
    b = to_float(scores_b)
    w = weights_or_ones(weights, a.shape[0])
    check_inputs(scores_a=a, scores_b=b, weights=w)
    ta = topk_mask(a, w, k)
    tb = topk_mask(b, w, k)
    cells = {"stay": ta & tb, "dropped": ta & ~tb, "added": ~ta & tb, "out": ~ta & ~tb}
    total = w.sum()
    rows = {
        name: {"weight": float(w[m].sum()), "share": float(w[m].sum() / total)}
        for name, m in cells.items()
    }
    return pd.DataFrame(rows).T[["weight", "share"]]
