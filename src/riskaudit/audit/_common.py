from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass
class SurveyDesign:
    """Stratum and PSU labels for design-based (cluster) bootstrap resampling.

    Pass one to the CI-bearing audit functions to resample PSUs within strata
    (VARSTR/VARPSU) instead of individual rows, so the interval reflects the
    survey design. Strata with a single PSU are held fixed.
    """

    strata: np.ndarray
    psu: np.ndarray

    def __post_init__(self):
        self.strata = np.asarray(self.strata)
        self.psu = np.asarray(self.psu)


def to_float(x: ArrayLike) -> np.ndarray:
    return np.asarray(x, dtype=float)


def weights_or_ones(weights: ArrayLike | None, n: int) -> np.ndarray:
    return np.ones(n) if weights is None else np.asarray(weights, dtype=float)


def topk_mask(scores: np.ndarray, weights: np.ndarray, k: float) -> np.ndarray:
    """Boolean mask of the highest-scoring units whose weight first reaches ``k``."""
    order = np.argsort(-scores, kind="stable")
    cumw = np.cumsum(weights[order])
    j = int(np.searchsorted(cumw, k * cumw[-1]))
    mask = np.zeros(scores.shape[0], dtype=bool)
    mask[order[: j + 1]] = True
    return mask


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(w * x) / np.sum(w))


def weighted_capture(scores: np.ndarray, need: np.ndarray, weights: np.ndarray, k: float) -> float:
    """Weighted share of total need falling in the top-``k`` (by weight) of ``scores``."""
    mask = topk_mask(scores, weights, k)
    wn = weights * need
    return float(wn[mask].sum() / wn.sum())


def _cluster_indices(rng, design: SurveyDesign) -> np.ndarray:
    parts = []
    for st in np.unique(design.strata):
        rows = np.where(design.strata == st)[0]
        psus = np.unique(design.psu[rows])
        if psus.size < 2:
            parts.append(rows)
            continue
        for c in rng.choice(psus, size=psus.size, replace=True):
            parts.append(rows[design.psu[rows] == c])
    return np.concatenate(parts)


def boot_ci(stat, n: int, n_boot: int, seed: int, design: SurveyDesign | None = None):
    """Percentile CI from a seeded bootstrap of ``stat``.

    Resamples rows uniformly, or PSUs within strata when a ``design`` is given.
    """
    rng = np.random.default_rng(seed)

    def draw():
        return rng.integers(0, n, n) if design is None else _cluster_indices(rng, design)

    vals = np.array([stat(draw()) for _ in range(n_boot)])
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))
