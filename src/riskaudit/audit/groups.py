import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from riskaudit._config import SEED
from riskaudit.audit._common import (
    SurveyDesign,
    boot_ci,
    check_inputs,
    to_float,
    weighted_capture,
    weights_or_ones,
)


def group_capture(
    scores: ArrayLike,
    need: ArrayLike,
    groups: ArrayLike,
    k: float = 0.10,
    weights: ArrayLike | None = None,
    n_boot: int = 1000,
    design: SurveyDesign | None = None,
) -> pd.DataFrame:
    r"""Top-``k`` need capture computed within each subgroup — the equity axis.

    Runs the :func:`top_k_capture` statistic separately for every level of
    ``groups`` and returns one row per group: its within-group capture, graded
    against the same floor (``= k``) and its own oracle, with a bootstrap CI.
    Comparing capture across groups answers *whose* need the score ranks worst —
    the disaggregation the label-choice literature (Obermeyer et al., 2019) turns on.

    The CI is a domain (subpopulation) bootstrap: rows — or PSUs within strata
    when ``design`` is given — are resampled over the whole frame and the group's
    statistic is recomputed on each resample, so the interval reflects the design
    instead of filtering the group out first (which would understate variance).

    Parameters
    ----------
    scores, need : array-like of shape (n,)
        Model score and independent need per unit.
    groups : array-like of shape (n,)
        Subgroup label per unit; any dtype.
    k : float, default 0.10
        Top fraction, by weight, within each group.
    weights : array-like of shape (n,), optional
        Survey weights; all ones when omitted.
    n_boot : int, default 1000
        Bootstrap resamples for each group's CI.
    design : SurveyDesign, optional
        Resample PSUs within strata for a design-based CI.

    Returns
    -------
    pandas.DataFrame
        Indexed by group, columns ``capture``, ``ci_lo``, ``ci_hi``, ``floor``
        (``= k``), ``oracle``, ``weight`` (group weight total) and ``n``.
    """
    s = to_float(scores)
    nd = to_float(need)
    w = weights_or_ones(weights, s.shape[0])
    check_inputs(scores=s, need=nd, weights=w)
    g = np.asarray(groups)
    if g.shape[0] != s.shape[0]:
        raise ValueError(f"length mismatch: groups has {g.shape[0]}, expected {s.shape[0]}")

    rows = {}
    for lvl in np.unique(g):
        m = g == lvl

        def stat(idx, m=m):
            gm = m[idx]
            return weighted_capture(s[idx][gm], nd[idx][gm], w[idx][gm], k) if gm.any() else np.nan

        lo, hi = boot_ci(stat, s.shape[0], n_boot, SEED, design)
        rows[lvl] = {
            "capture": weighted_capture(s[m], nd[m], w[m], k),
            "ci_lo": lo,
            "ci_hi": hi,
            "floor": k,
            "oracle": weighted_capture(nd[m], nd[m], w[m], k),
            "weight": float(w[m].sum()),
            "n": int(m.sum()),
        }
    return pd.DataFrame.from_dict(rows, orient="index")
