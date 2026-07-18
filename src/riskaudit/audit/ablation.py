from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd
from numpy.typing import ArrayLike


@dataclass
class AblationResult:
    global_delta: pd.DataFrame
    capture_delta: pd.DataFrame


def ablation(
    fit_fn: Callable[[pd.DataFrame, ArrayLike], object],
    X: pd.DataFrame,
    y: ArrayLike,
    feature_groups: Mapping[str, Sequence[str]],
    k: float = 0.10,
    weights: ArrayLike | None = None,
) -> AblationResult:
    r"""Refit without each feature group; contrast global loss with capture loss.

    For each group :math:`g`, the model is refit on :math:`X` with the columns
    of :math:`g` removed and compared to the full-feature model on two axes:

    - :math:`\Delta\text{global}` — change in overall performance (R\ :sup:`2`
      or AUC) predicting the target :math:`y`;
    - :math:`\Delta\text{capture}` — change in :func:`top_k_capture` of the
      need concentrated in group :math:`g`.

    The expected finding for a spend target: dropping the mental-health group
    barely moves :math:`\Delta\text{global}` yet collapses :math:`\Delta\text{capture}`
    — the group is nearly free to the loss but is what made those units visible.

    Parameters
    ----------
    fit_fn : callable ``(X, y) -> fitted model with .predict``
        Trains one model; called once per ablation with the same settings.
    X : pandas.DataFrame of shape (n, p)
        Feature matrix.
    y : array-like of shape (n,)
        Target.
    feature_groups : mapping of str to sequence of str
        Group name to its column names in ``X``.
    k : float, default 0.10
        Top fraction for the capture comparison.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.

    Returns
    -------
    AblationResult
        Per-group global and capture deltas.
    """
    raise NotImplementedError
