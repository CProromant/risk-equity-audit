from dataclasses import dataclass

from numpy.typing import ArrayLike


@dataclass
class RTMResult:
    observed_drop: float
    rtm_expected_drop: float
    rtm_share: float
    ci: tuple[float, float]


def regression_to_mean(
    y_t: ArrayLike,
    y_t1: ArrayLike,
    scores_t: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    n_boot: int = 1000,
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
    raise NotImplementedError
