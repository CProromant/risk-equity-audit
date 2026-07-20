from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import (
    SurveyDesign,
    boot_ci,
    check_inputs,
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


def _wcov(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    mx, my = wmean(x, w), wmean(y, w)
    return float(np.sum(w * (x - mx) * (y - my)) / np.sum(w))


def _expected_drop(yt, yt1, top, w) -> float:
    var_t = _wcov(yt, yt, w)
    beta = _wcov(yt, yt1, w) / var_t if var_t > 0 else np.nan
    top_t = wmean(yt[top], w[top])
    predicted_t1 = wmean(yt1, w) + beta * (top_t - wmean(yt, w))
    return top_t - predicted_t1


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
    :math:`\bar y_{t,\text{top}} - \bar y_{t+1,\text{top}}` (weighted). The
    RTM-expected next-period value of the top group is the population regression
    line evaluated at the group's mean,

    .. math::
        \widehat{y}_{t+1,\text{top}} \;=\; \mu_{t+1}
        + \beta\,(\bar y_{t,\text{top}} - \mu_t), \qquad
        \beta = \frac{\operatorname{cov}_w(y_t, y_{t+1})}{\operatorname{var}_w(y_t)},

    so the RTM-expected drop is :math:`\bar y_{t,\text{top}} -
    \widehat{y}_{t+1,\text{top}}` and ``rtm_share`` is its ratio to the observed
    drop.

    **Caveats.** Classic RTM assumes selection on :math:`y_t` itself; here the
    top group is chosen by ``scores_t``, so this is an approximation. The result
    is scale-dependent — run it in the same units the claim is made in (e.g.
    ``log1p`` spend, not raw dollars, if the model is on the log scale). Treat it
    as descriptive.

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
    design : SurveyDesign, optional
        When given, the CI resamples PSUs within strata for a design-based interval.

    Returns
    -------
    RTMResult
        Observed drop, RTM-expected drop, their ratio, and its 95% ``ci``.
    """
    yt = to_float(y_t)
    yt1 = to_float(y_t1)
    s = to_float(scores_t)
    w = weights_or_ones(weights, yt.shape[0])
    check_inputs(y_t=yt, y_t1=yt1, scores_t=s, weights=w)

    def stat(idx: np.ndarray) -> float:
        top = topk_mask(s[idx], w[idx], k)
        observed = wmean(yt[idx][top], w[idx][top]) - wmean(yt1[idx][top], w[idx][top])
        if abs(observed) < 1e-12:
            return np.nan
        return _expected_drop(yt[idx], yt1[idx], top, w[idx]) / observed

    top = topk_mask(s, w, k)
    observed = wmean(yt[top], w[top]) - wmean(yt1[top], w[top])
    expected = _expected_drop(yt, yt1, top, w)
    share = float(expected / observed) if abs(observed) > 1e-12 else float("nan")
    ci = boot_ci(stat, yt.shape[0], n_boot, SEED, design)
    return RTMResult(float(observed), float(expected), share, ci)
