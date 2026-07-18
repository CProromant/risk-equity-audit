from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


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
    raise NotImplementedError
