import numpy as np
from numpy.typing import ArrayLike


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


def boot_ci(stat, n: int, n_boot: int, seed: int) -> tuple[float, float]:
    """Percentile CI from a row-resampling bootstrap of ``stat`` (seeded, reproducible)."""
    rng = np.random.default_rng(seed)
    vals = np.array([stat(rng.integers(0, n, n)) for _ in range(n_boot)])
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))
