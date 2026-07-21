"""Controlled benchmark: riskaudit recovering a *known* label-choice bias.

Self-contained synthetic data — no real data, no PHI. The generator plants the
bias on purpose: a cost proxy that misses people who don't seek care, plus an
"underserved" subgroup that seeks care less often. Because the planted answer is
known, this doubles as a check that each function recovers it — every public
function in ``riskaudit.audit`` runs here, including the survey-design CI path.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from riskaudit.audit import (
    SurveyDesign,
    ablation,
    audit_report,
    group_capture,
    incremental_lift,
    label_blend_frontier,
    label_choice_curve,
    label_robustness,
    reclassification,
    regression_to_mean,
    top_k_capture,
)

SEED = 2026


def _synthetic(n: int, rng: np.random.Generator):
    underserved = rng.random(n) < 0.35
    need = rng.gamma(2.0, 1.0, n)  # true severity, unobserved by the cost model
    care_prob = np.where(underserved, 0.30, 0.75)  # planted access gap
    seeks = rng.random(n) < care_prob
    prior_cost = need * seeks * 1200 + rng.gamma(
        1.0, 250.0, n
    )  # spending proxy: misses non-seekers
    comorbidity = need * 0.5 + rng.normal(0, 1.2, n)  # a noisy need signal (weak cost predictor)
    age = rng.integers(18, 85, n).astype(float)
    # Future cost is mostly spending-persistence, with need surfacing on top and big noise —
    # so a cost-optimizing model leans on prior_cost and underweights the need signal.
    future_cost = np.clip(prior_cost * 0.8 + need * 1000 + rng.gamma(1.0, 1200.0, n), 0, None)
    need_measure = need + rng.normal(0, 0.3, n)  # independent measure of need

    strata = rng.integers(0, 4, n)  # 4 strata x 6 PSUs, for the design-based CI
    psu = strata * 6 + rng.integers(0, 6, n)
    weights = rng.uniform(0.5, 2.0, n)

    X = pd.DataFrame({"prior_cost": prior_cost, "comorbidity": comorbidity, "age": age})
    group = np.where(underserved, "underserved", "served")
    return X, future_cost, need_measure, weights, group, strata, psu


def main(
    out_html: str = "benchmark_report.html", n: int = 4000, seed: int = SEED, n_boot: int = 300
):
    rng = np.random.default_rng(seed)
    X, future_cost, need, w, group, strata, psu = _synthetic(n, rng)
    design = SurveyDesign(strata, psu)

    cost_model = LinearRegression().fit(X, future_cost)
    score = cost_model.predict(X)  # the deployed cost-proxy score
    need_score = need + rng.normal(0, 0.3, n)  # a second, need-oriented candidate label
    distress = (need > np.quantile(need, 0.8)).astype(int)

    cap_cost = top_k_capture(score, need, weights=w, n_boot=n_boot, design=design)
    cap_need = top_k_capture(need, need, weights=w, n_boot=n_boot)
    by_group = group_capture(score, need, group, weights=w, n_boot=n_boot, design=design)
    frontier = label_blend_frontier(
        score, need_score, need, weights=w, groups=group, alphas=[0.0, 0.5, 1.0], n_boot=n_boot
    )
    results = {
        "Top-decile capture — cost model": cap_cost,
        "Top-decile capture — need model": cap_need,
        "Capture by subgroup (cost model)": by_group,
        "Label-blend frontier (cost → need)": frontier,
        "Reclassification: cost vs need": reclassification(score, need, weights=w),
        "Label-choice curve (cost model)": label_choice_curve(score, need, weights=w),
        "Ablation (drop each feature group)": ablation(
            lambda Xt, yt: LinearRegression().fit(Xt, yt),
            X,
            future_cost,
            {"care_proxy": ["prior_cost"], "clinical": ["comorbidity"], "demo": ["age"]},
            need=need,
            weights=w,
        ),
        "Incremental lift (deprioritized tail)": incremental_lift(
            future_cost, cost_model.predict(X), distress, score, weights=w, n_boot=n_boot
        ),
        "Regression to the mean (cost top-k)": regression_to_mean(
            X["prior_cost"].to_numpy(), future_cost, score, weights=w, n_boot=n_boot
        ),
        "Label robustness (need stress-test)": label_robustness(score, need, weights=w),
    }
    out = audit_report(results, out_html)

    served = by_group.loc["served", "capture"]
    under = by_group.loc["underserved", "capture"]
    share_cost = frontier.loc[1.0, "share_underserved"]
    share_need = frontier.loc[0.0, "share_underserved"]
    print(f"need capture (top decile): cost {cap_cost.value:.1%} vs need {cap_need.value:.1%}")
    print(f"  by subgroup: served {served:.1%} vs underserved {under:.1%}")
    print(
        f"  underserved share of top-k: cost label {share_cost:.1%} -> need label {share_need:.1%}"
    )
    print(f"wrote {out}")
    return out, {
        "cap_cost": cap_cost,
        "cap_need": cap_need,
        "by_group": by_group,
        "frontier": frontier,
    }


if __name__ == "__main__":
    main()
