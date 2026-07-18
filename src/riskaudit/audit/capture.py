from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import boot_ci, to_float, topk_mask, weights_or_ones


@dataclass
class CaptureResult:
    value: float
    ci: tuple[float, float]
    k: float


def top_k_capture(
    scores: ArrayLike,
    need: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    n_boot: int = 1000,
) -> CaptureResult:
    r"""Weighted share of total need captured by the top-``k`` of ``scores``.

    Units are ranked by ``scores`` descending and the top ``k`` fraction *by
    weight* is selected. The statistic is the weighted share of total need that
    falls in that group,

    .. math::
        C_k \;=\; \frac{\sum_{i \in T_k} w_i\, n_i}{\sum_i w_i\, n_i},

    where :math:`T_k` is the highest-scoring set whose cumulative weight first
    reaches a fraction :math:`k` of the total weight, :math:`n_i` is need and
    :math:`w_i` the survey weight. A model that ranks by true need attains a
    high :math:`C_k`; the gap between a spend-ranked and a need-ranked model is
    the label-choice cost this toolkit measures.

    Parameters
    ----------
    scores : array-like of shape (n,)
        Model score per unit; higher means higher predicted priority.
    need : array-like of shape (n,)
        Independent measure of realized need on the same units.
    k : float, default 0.10
        Top fraction, by weight, to select.
    weights : array-like of shape (n,), optional
        Survey weights; treated as all ones when omitted.
    n_boot : int, default 1000
        Weighted bootstrap resamples for the confidence interval.

    Returns
    -------
    CaptureResult
        ``value`` and its 95% weighted-bootstrap ``ci``.
    """
    s = to_float(scores)
    nd = to_float(need)
    w = weights_or_ones(weights, s.shape[0])

    def stat(idx: np.ndarray) -> float:
        mask = topk_mask(s[idx], w[idx], k)
        wn = w[idx] * nd[idx]
        return float(wn[mask].sum() / wn.sum())

    value = stat(np.arange(s.shape[0]))
    ci = boot_ci(stat, s.shape[0], n_boot, SEED)
    return CaptureResult(value, ci, k)
