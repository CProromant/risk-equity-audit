from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import KFold

from riskaudit._config import SEED
from riskaudit.audit._common import to_float, weighted_capture, weights_or_ones


@dataclass
class AblationResult:
    global_delta: pd.DataFrame
    capture_delta: pd.DataFrame


def _perf(y: np.ndarray, pred: np.ndarray, w: np.ndarray) -> float:
    if np.isin(np.unique(y), [0, 1]).all():
        return float(roc_auc_score(y, pred, sample_weight=w))
    return float(r2_score(y, pred, sample_weight=w))


def ablation(
    fit_fn: Callable[[pd.DataFrame, ArrayLike], object],
    X: pd.DataFrame,
    y: ArrayLike,
    feature_groups: Mapping[str, Sequence[str]],
    need: ArrayLike | None = None,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    cv: int = 5,
    seed: int = SEED,
) -> AblationResult:
    r"""Refit without each feature group; contrast global loss with capture loss.

    Predictions are **cross-fitted** (``cv``-fold): every row is scored by a model
    that did not train on it, so the deltas reflect generalization, not in-sample
    memorization. For each group :math:`g` the model is refit on :math:`X` with the
    columns of :math:`g` removed and compared to the full-feature model on:

    - :math:`\Delta\text{global}` — change in cross-fitted performance (R\ :sup:`2`
      or AUC) predicting the target :math:`y`;
    - :math:`\Delta\text{capture}` — change in weighted top-``k`` capture of
      ``need`` (the independent need measure; defaults to the target ``y``).

    The expected finding for a spend target with ``need`` set to measured distress:
    dropping the mental-health group barely moves :math:`\Delta\text{global}` yet
    collapses :math:`\Delta\text{capture}`.

    Parameters
    ----------
    fit_fn : callable ``(X, y) -> fitted model with .predict``
        Trains one model; called once per fold per ablation with the same settings.
    X : pandas.DataFrame of shape (n, p)
        Feature matrix.
    y : array-like of shape (n,)
        Target the model is trained on.
    feature_groups : mapping of str to sequence of str
        Group name to its column names in ``X``.
    need : array-like of shape (n,), optional
        Independent need measure for the capture delta; defaults to ``y``.
    k : float, default 0.10
        Top fraction for the capture comparison.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    cv : int, default 5
        Number of cross-fitting folds.
    seed : int, default SEED
        Fold shuffle seed.

    Returns
    -------
    AblationResult
        Per-group global and capture deltas.
    """
    w = weights_or_ones(weights, len(X))
    yv = np.asarray(y)
    nd = to_float(y if need is None else need)
    folds = list(KFold(max(2, min(cv, len(X))), shuffle=True, random_state=seed).split(X))

    def cross_fit(xd: pd.DataFrame) -> np.ndarray:
        pred = np.empty(len(xd))
        for tr, te in folds:
            model = fit_fn(xd.iloc[tr], yv[tr])
            pred[te] = np.asarray(model.predict(xd.iloc[te]), dtype=float)
        return pred

    p0 = cross_fit(X)
    g0, c0 = _perf(yv, p0, w), weighted_capture(p0, nd, w, k)

    gd, cd = {}, {}
    for name, cols in feature_groups.items():
        pg = cross_fit(X.drop(columns=list(cols)))
        gd[name] = g0 - _perf(yv, pg, w)
        cd[name] = c0 - weighted_capture(pg, nd, w, k)
    return AblationResult(pd.DataFrame({"delta": gd}), pd.DataFrame({"delta": cd}))
