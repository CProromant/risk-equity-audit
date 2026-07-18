from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import (
    SurveyDesign,
    boot_ci,
    to_float,
    topk_mask,
    weights_or_ones,
    wmean,
)


@dataclass
class RTMResult:
    observed_drop: float
    rtm_expected_drop: float
    rtm_share: float
    ci: tuple[float, float]


def _wcorr(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    mx, my = wmean(x, w), wmean(y, w)
    cov = np.sum(w * (x - mx) * (y - my))
    denom = np.sqrt(np.sum(w * (x - mx) ** 2) * np.sum(w * (y - my) ** 2))
    return float(cov / denom) if denom > 0 else np.nan


def regression_to_mean(
    y_t: ArrayLike,
    y_t1: ArrayLike,
    scores_t: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    n_boot: int = 1000,
    design: SurveyDesign | None = None,
) -> RTMResult:
    r"""Share of the top-``k`` outcome drop attributable to regression to the mean.

    For units in the top ``k`` of ``scores_t``, the observed drop is
    :math:`\bar{y}_t - \bar{y}_{t+1}` (weighted). Under pure regression to the
    mean the expected next-period value of an extreme group shrinks toward the
    population mean by :math:`(1-\rho)`, giving an RTM-expected drop of

    .. math::
        \Delta_{\text{RTM}} \;=\; (1-\rho)\,(\bar{y}_t - \mu),

    where :math:`\rho` is the weighted year-to-year correlation of the outcome
    and :math:`\mu` its population mean. The reported ``rtm_share`` is
    :math:`\Delta_{\text{RTM}} / (\bar{y}_t - \bar{y}_{t+1})` — how much of the
    observed decline is a statistical artifact rather than a real effect.

    Parameters
    ----------
    y_t, y_t1 : array-like of shape (n,)
        Outcome at ``t`` and ``t+1`` for the same units.
    scores_t : array-like of shape (n,)
        Score at ``t`` used to define the top-``k`` group.
    k : float, default 0.10
        Top fraction, by weight.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    n_boot : int, default 1000
        Weighted bootstrap resamples for the confidence interval.

    Returns
    -------
    RTMResult
        Observed drop, RTM-expected drop, their ratio, and its 95% ``ci``.
    """
    yt = to_float(y_t)
    yt1 = to_float(y_t1)
    s = to_float(scores_t)
    w = weights_or_ones(weights, yt.shape[0])
    mu = wmean(yt, w)

    def stat(idx: np.ndarray) -> float:
        m = topk_mask(s[idx], w[idx], k)
        top_t = wmean(yt[idx][m], w[idx][m])
        denom = top_t - wmean(yt1[idx][m], w[idx][m])
        if abs(denom) < 1e-12:
            return np.nan
        rho = _wcorr(yt[idx], yt1[idx], w[idx])
        return (1 - rho) * (top_t - wmean(yt[idx], w[idx])) / denom

    top = topk_mask(s, w, k)
    observed = wmean(yt[top], w[top]) - wmean(yt1[top], w[top])
    rho = _wcorr(yt, yt1, w)
    expected = (1 - rho) * (wmean(yt[top], w[top]) - mu)
    ci = boot_ci(stat, yt.shape[0], n_boot, SEED, design)
    return RTMResult(float(observed), float(expected), float(expected / observed), ci)
