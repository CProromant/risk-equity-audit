import warnings
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass
class SurveyDesign:
    """Stratum and PSU labels for design-based (cluster) bootstrap resampling.

    Pass one to the CI-bearing audit functions to resample PSUs within strata
    (VARSTR/VARPSU) instead of individual rows, so the interval reflects the
    survey design. Strata with a single PSU are held fixed (their variance
    contribution is zero), and a warning is emitted when that happens.
    """

    strata: np.ndarray
    psu: np.ndarray

    def __post_init__(self):
        self.strata = np.asarray(self.strata)
        self.psu = np.asarray(self.psu)
        singles = sum(
            np.unique(self.psu[self.strata == s]).size < 2 for s in np.unique(self.strata)
        )
        if singles:
            warnings.warn(
                f"{singles} stratum(s) have a single PSU and are held fixed; their variance "
                "contribution is zero, so the CI is biased low. Consider collapsing strata.",
                stacklevel=2,
            )


def check_inputs(**arrays: ArrayLike) -> None:
    """Validate that public inputs are finite and equally long (fail at the boundary)."""
    n = None
    for name, a in arrays.items():
        arr = np.asarray(a, dtype=float)
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} contains NaN or inf")
        if n is None:
            n = arr.shape[0]
        elif arr.shape[0] != n:
            raise ValueError(f"length mismatch: {name} has {arr.shape[0]}, expected {n}")


def to_float(x: ArrayLike) -> np.ndarray:
    return np.asarray(x, dtype=float)


def weights_or_ones(weights: ArrayLike | None, n: int) -> np.ndarray:
    return np.ones(n) if weights is None else np.asarray(weights, dtype=float)


def topk_mask(scores: np.ndarray, weights: np.ndarray, k: float) -> np.ndarray:
    """Boolean mask of the highest-scoring units whose weight first reaches ``k``.

    Ties are broken by row order (stable sort), so with discretized scores the
    exact top-``k`` membership can depend on the input order.
    """
    order = np.argsort(-scores, kind="stable")
    cumw = np.cumsum(weights[order])
    j = int(np.searchsorted(cumw, k * cumw[-1]))
    mask = np.zeros(scores.shape[0], dtype=bool)
    mask[order[: j + 1]] = True
    return mask


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(w * x) / np.sum(w))


def rank01(x: np.ndarray) -> np.ndarray:
    """Ranks of ``x`` scaled to [0, 1], stable on ties (0 for a single element)."""
    r = np.empty(x.shape[0])
    r[np.argsort(x, kind="stable")] = np.arange(x.shape[0])
    return r / (x.shape[0] - 1) if x.shape[0] > 1 else r


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
    The seed is fixed, so CIs of different metrics in the same report share the
    same resamples (deterministic, but their sampling errors are correlated).
    """
    rng = np.random.default_rng(seed)

    def draw():
        return rng.integers(0, n, n) if design is None else _cluster_indices(rng, design)

    vals = np.array([stat(draw()) for _ in range(n_boot)])
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))
