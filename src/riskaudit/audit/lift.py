from dataclasses import dataclass

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
class LiftResult:
    value: float
    ci: tuple[float, float]
    residual_distressed: float
    residual_other: float


def incremental_lift(
    y_t1: ArrayLike,
    y_pred: ArrayLike,
    distress: ArrayLike,
    scores: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    n_boot: int = 1000,
    design: SurveyDesign | None = None,
) -> LiftResult:
    r"""Incremental need lift in the low-score tail (the contribution metric).

    Among the units a model *deprioritizes* — those outside the top ``k`` of
    ``scores`` — this contrasts how much more future need distressed people
    generated than the model predicted, versus everyone else in that tail:

    .. math::
        \text{Lift}_k \;=\;
        \frac{\sum_{i \in L} w_i d_i r_i}{\sum_{i \in L} w_i d_i}
        \;-\;
        \frac{\sum_{i \in L} w_i (1-d_i) r_i}{\sum_{i \in L} w_i (1-d_i)},

    where :math:`L` is the deprioritized tail, :math:`d_i` marks measured
    distress, and :math:`r_i = y_{i,t+1} - \hat y_i` is the realized residual of
    the outcome the model targets. A positive lift means the model was blind to
    real downstream need concentrated in the distressed — the non-circular core
    of the argument, since :math:`y_{t+1}` is the model's own currency, not the
    distress measure (``docs/methods.md`` §2).

    Parameters
    ----------
    y_t1 : array-like of shape (n,)
        Realized outcome at ``t+1`` (the spending/utilization the model targets).
    y_pred : array-like of shape (n,)
        The model's prediction of that outcome.
    distress : array-like of shape (n,)
        1 where measured need is present, 0 otherwise.
    scores : array-like of shape (n,)
        Model risk score defining the priority set.
    k : float, default 0.10
        Top fraction, by weight; its complement is the deprioritized tail.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    n_boot : int, default 1000
        Bootstrap resamples for the confidence interval.
    design : SurveyDesign, optional
        When given, the CI resamples PSUs within strata (VARSTR/VARPSU) instead
        of rows, for a design-based interval.

    Returns
    -------
    LiftResult
        The lift, its 95% ``ci``, and the two tail residual means.
    """
    y = to_float(y_t1)
    p = to_float(y_pred)
    d = to_float(distress)
    s = to_float(scores)
    w = weights_or_ones(weights, y.shape[0])
    r = y - p

    def stat(idx) -> float:
        tail = ~topk_mask(s[idx], w[idx], k)
        di = d[idx]
        one, zero = tail & (di == 1), tail & (di == 0)
        return wmean(r[idx][one], w[idx][one]) - wmean(r[idx][zero], w[idx][zero])

    tail = ~topk_mask(s, w, k)
    one, zero = tail & (d == 1), tail & (d == 0)
    rd = wmean(r[one], w[one])
    ro = wmean(r[zero], w[zero])
    ci = boot_ci(stat, y.shape[0], n_boot, SEED, design)
    return LiftResult(float(rd - ro), ci, float(rd), float(ro))
