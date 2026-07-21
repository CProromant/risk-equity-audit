from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from riskaudit.audit._common import (
    check_inputs,
    rank01,
    to_float,
    weighted_capture,
    weights_or_ones,
)


@dataclass
class RobustnessResult:
    epsilon: np.ndarray
    model_capture: np.ndarray
    oracle_capture: np.ndarray
    gap: np.ndarray
    breakdown: float  # smallest epsilon that halves the clean capture gap (nan if no gap)


def label_robustness(
    scores: ArrayLike,
    need: ArrayLike,
    weights: ArrayLike | None = None,
    k: float = 0.10,
    grid: ArrayLike | None = None,
) -> RobustnessResult:
    r"""How wrong the ``need`` label would have to be to explain away the capture gap.

    Every other metric treats ``need`` as ground truth, but ``need`` is itself a proxy
    (K6, a claims flag, …). This is a worst-case sensitivity bound: it blends ``need``
    toward the model's own ranking — the direction most favorable to the model — and
    measures how far it must move before the gap between the model's capture and the
    oracle shrinks to half its original size,

    .. math::
        \text{need}_\varepsilon \;=\; (1-\varepsilon)\,\operatorname{rank}(\text{need})
        + \varepsilon\,\operatorname{rank}(\text{scores}).

    A small ``breakdown`` means the finding is fragile to error in the need measure; a
    large one means you would have to be very wrong about need for the model to look
    good. It answers *"with what certainty"* at the level reviewers actually attack — not
    sampling noise (that is the bootstrap CI), but the truth of the label.

    Parameters
    ----------
    scores : array-like of shape (n,)
        Model score per unit.
    need : array-like of shape (n,)
        The (proxy) need measure being stress-tested.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    k : float, default 0.10
        Top fraction, by weight, for the capture.
    grid : array-like, optional
        Perturbation fractions in [0, 1]; defaults to 11 points 0…1.

    Returns
    -------
    RobustnessResult
        The grid, model and oracle capture along it, the gap, and the half-gap
        ``breakdown`` epsilon.
    """
    s = to_float(scores)
    n = to_float(need)
    w = weights_or_ones(weights, s.shape[0])
    check_inputs(scores=s, need=n, weights=w)
    grid = np.linspace(0, 1, 11) if grid is None else np.asarray(grid, dtype=float)

    nr, sr = rank01(n), rank01(s)
    perturbed = [(1 - e) * nr + e * sr for e in grid]
    model = np.array([weighted_capture(s, p, w, k) for p in perturbed])
    oracle = np.array([weighted_capture(p, p, w, k) for p in perturbed])
    gap = oracle - model

    hit = np.where(gap <= 0.5 * gap[0])[0]
    breakdown = float(grid[hit[0]]) if gap[0] > 1e-12 and hit.size else float("nan")
    return RobustnessResult(grid, model, oracle, gap, breakdown)
