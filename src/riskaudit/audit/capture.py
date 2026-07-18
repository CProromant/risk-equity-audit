from dataclasses import dataclass

from numpy.typing import ArrayLike


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
    raise NotImplementedError
