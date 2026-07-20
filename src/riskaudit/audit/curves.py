from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import (
    SurveyDesign,
    _cluster_indices,
    check_inputs,
    to_float,
    weights_or_ones,
)


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
    design: SurveyDesign | None = None,
    n_boot: int = 1000,
) -> CurveResult:
    r"""Mean observed need across score percentiles, Obermeyer-style.

    Units are grouped into ``bins`` equal-weight strata of the score, and each
    stratum's weighted mean need is reported,

    .. math::
        \bar{n}_b \;=\; \frac{\sum_{i \in b} w_i\, n_i}{\sum_{i \in b} w_i}.

    A model that ranks by true need yields a clean monotone rise; label-choice
    bias shows as units with high need sitting at low score percentiles. The band
    is a percentile bootstrap — a design-based cluster bootstrap when ``design``
    is given, otherwise a row bootstrap.

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
    design : SurveyDesign, optional
        When given, the band resamples PSUs within strata (VARSTR/VARPSU).
    n_boot : int, default 1000
        Bootstrap resamples for the band.

    Returns
    -------
    CurveResult
        Per-bin score percentile, mean need, and its 95% band.
    """
    s = to_float(scores)
    nd = to_float(need)
    w = weights_or_ones(weights, s.shape[0])
    check_inputs(scores=s, need=nd, weights=w)

    order = np.argsort(s, kind="stable")
    edges = np.linspace(0, w[order].sum(), bins + 1)
    label = np.empty(s.shape[0], dtype=int)
    label[order] = np.clip(
        np.searchsorted(edges, np.cumsum(w[order]), side="left") - 1, 0, bins - 1
    )

    def bin_means(idx: np.ndarray) -> np.ndarray:
        out = np.full(bins, np.nan)
        lab = label[idx]
        for b in range(bins):
            sel = idx[lab == b]
            if sel.size:
                out[b] = np.sum(w[sel] * nd[sel]) / np.sum(w[sel])
        return out

    mean = bin_means(np.arange(s.shape[0]))
    pct = (np.arange(bins) + 0.5) / bins * 100

    rng = np.random.default_rng(SEED)

    def draw():
        return (
            rng.integers(0, s.shape[0], s.shape[0])
            if design is None
            else _cluster_indices(rng, design)
        )

    boot = np.array([bin_means(draw()) for _ in range(n_boot)])
    lo = np.nanpercentile(boot, 2.5, axis=0)
    hi = np.nanpercentile(boot, 97.5, axis=0)
    return CurveResult(pct, mean, lo, hi)
