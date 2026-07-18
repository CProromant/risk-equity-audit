from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit.audit._common import to_float, weights_or_ones


@dataclass
class CurveResult:
    percentile: np.ndarray
    need_mean: np.ndarray
    need_lo: np.ndarray
    need_hi: np.ndarray


def label_choice_curve(
    scores: ArrayLike,
    need: ArrayLike,
    weights: ArrayLike | None = None,
    bins: int = 20,
) -> CurveResult:
    r"""Mean observed need across score percentiles, Obermeyer-style.

    Units are grouped into ``bins`` equal-weight strata of the score, and each
    stratum's weighted mean need is reported,

    .. math::
        \bar{n}_b \;=\; \frac{\sum_{i \in b} w_i\, n_i}{\sum_{i \in b} w_i}.

    A model that ranks by true need yields a clean monotone rise; label-choice
    bias shows as units with high need sitting at low score percentiles.

    Parameters
    ----------
    scores : array-like of shape (n,)
        Model score per unit.
    need : array-like of shape (n,)
        Observed need on the same units.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    bins : int, default 20
        Number of equal-weight score strata.

    Returns
    -------
    CurveResult
        Per-bin score percentile, mean need, and its 95% band.
    """
    s = to_float(scores)
    nd = to_float(need)
    w = weights_or_ones(weights, s.shape[0])
    order = np.argsort(s, kind="stable")
    nd, w = nd[order], w[order]
    cumw = np.cumsum(w)
    edges = np.linspace(0, cumw[-1], bins + 1)
    binof = np.clip(np.searchsorted(edges, cumw, side="left") - 1, 0, bins - 1)

    pct, mean, lo, hi = (np.full(bins, np.nan) for _ in range(4))
    for b in range(bins):
        sel = binof == b
        pct[b] = (b + 0.5) / bins * 100
        if not sel.any():
            continue
        ww, nn = w[sel], nd[sel]
        m = float(np.sum(ww * nn) / np.sum(ww))
        var = float(np.sum(ww * (nn - m) ** 2) / np.sum(ww))
        se = np.sqrt(var * np.sum(ww**2)) / np.sum(ww)
        mean[b], lo[b], hi[b] = m, m - 1.96 * se, m + 1.96 * se
    return CurveResult(pct, mean, lo, hi)
