import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import (
    SurveyDesign,
    boot_ci,
    check_inputs,
    rank01,
    to_float,
    topk_mask,
    weighted_capture,
    weights_or_ones,
)


def label_blend_frontier(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    need: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    groups: ArrayLike | None = None,
    alphas: ArrayLike | None = None,
    n_boot: int = 1000,
    design: SurveyDesign | None = None,
) -> pd.DataFrame:
    r"""Need capture (and top-``k`` composition) as two candidate labels are blended.

    Ranks units by the convex blend of two scores,
    :math:`\alpha\,\operatorname{rank}(a) + (1-\alpha)\,\operatorname{rank}(b)`,
    for each ``alpha`` and reports the resulting need capture. ``alpha = 1`` is
    pure ``scores_a``, ``alpha = 0`` pure ``scores_b``; the sweep is the
    label-choice trade-off frontier — Obermeyer et al.'s "relabel the target"
    remedy made executable. With ``groups`` it also returns each group's share of
    the selected top-``k``, so composition can be read along the frontier.

    Scores are rank-normalized to ``[0, 1]`` before blending, so the two labels
    combine on a common scale whatever their raw units (dollars vs. an index).

    Parameters
    ----------
    scores_a, scores_b : array-like of shape (n,)
        The two candidate model scores to blend.
    need : array-like of shape (n,)
        Independent need the blended ranking is scored against.
    k : float, default 0.10
        Top fraction, by weight, selected at each alpha.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    groups : array-like of shape (n,), optional
        Subgroup labels; adds a ``share_<level>`` column per group.
    alphas : array-like, optional
        Blend weights on ``scores_a`` in ``[0, 1]``; defaults to 11 points 0…1.
    n_boot : int, default 1000
        Bootstrap resamples for each alpha's capture CI.
    design : SurveyDesign, optional
        Resample PSUs within strata for design-based CIs.

    Returns
    -------
    pandas.DataFrame
        Indexed by ``alpha``, columns ``capture``, ``ci_lo``, ``ci_hi`` and, when
        ``groups`` is given, one ``share_<level>`` column per subgroup.
    """
    a = to_float(scores_a)
    b = to_float(scores_b)
    nd = to_float(need)
    w = weights_or_ones(weights, a.shape[0])
    check_inputs(scores_a=a, scores_b=b, need=nd, weights=w)
    ra, rb = rank01(a), rank01(b)
    alphas = np.linspace(0, 1, 11) if alphas is None else np.asarray(alphas, dtype=float)

    g = None if groups is None else np.asarray(groups)
    if g is not None and g.shape[0] != a.shape[0]:
        raise ValueError(f"length mismatch: groups has {g.shape[0]}, expected {a.shape[0]}")
    levels = [] if g is None else list(np.unique(g))

    rows = {}
    for al in alphas:
        blend = al * ra + (1 - al) * rb

        def stat(idx, blend=blend):
            return weighted_capture(blend[idx], nd[idx], w[idx], k)

        lo, hi = boot_ci(stat, a.shape[0], n_boot, SEED, design)
        row = {"capture": stat(np.arange(a.shape[0])), "ci_lo": lo, "ci_hi": hi}
        if g is not None:
            mask = topk_mask(blend, w, k)
            tot = w[mask].sum()
            for lvl in levels:
                row[f"share_{lvl}"] = float(w[mask & (g == lvl)].sum() / tot)
        rows[round(float(al), 6)] = row

    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "alpha"
    return out
