import pandas as pd
from numpy.typing import ArrayLike


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
    raise NotImplementedError
