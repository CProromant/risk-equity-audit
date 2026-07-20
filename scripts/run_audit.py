import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from riskaudit._config import ARTIFACTS_DIR, SEED
from riskaudit.audit import (
    SurveyDesign,
    ablation,
    audit_report,
    incremental_lift,
    label_choice_curve,
    reclassification,
    regression_to_mean,
    top_k_capture,
)
from riskaudit.etl.meps import load_panel
from riskaudit.features import build_features


def _fit(X, y):
    return LGBMRegressor(
        random_state=SEED,
        num_leaves=15,
        n_estimators=300,
        learning_rate=0.05,
        min_child_samples=30,
        n_jobs=-1,
        verbose=-1,
        deterministic=True,
        force_row_wise=True,
    ).fit(X, y)


if __name__ == "__main__":
    panel = load_panel()
    fm = build_features(panel)
    # reindex aligns predictions to the current analytic sample by label, not order
    preds = pd.read_parquet(ARTIFACTS_DIR / "predictions.parquet").reindex(fm.X.index)
    rows = panel.loc[fm.X.index]

    design = SurveyDesign(strata=rows.stratum.values, psu=rows.psu.values)
    w = fm.weights
    need = fm.targets["k6"]  # K6_{t+1}, continuous
    spend = preds["spend"]  # spend model, has mental-health features
    spend_blind = preds["spend_no_mh"]  # spend model without them
    k6 = preds["k6"]
    distress = (fm.X.k6_t >= 13).astype(int)
    log_spend_t1 = fm.targets["spend"]  # realized log1p spend
    util_t1 = fm.targets["avoidable_util_bin"]  # realized ER+hospitalization (non-psychiatric)

    results = {
        "Top-decile capture of K6 need — spend model": top_k_capture(
            spend, need, weights=w, design=design, n_boot=500
        ),
        "Top-decile capture of K6 need — K6 model": top_k_capture(
            k6, need, weights=w, design=design, n_boot=500
        ),
        "Reclassification: spend vs K6 (top decile)": reclassification(spend, k6, weights=w),
        "Label-choice curve (spend model)": label_choice_curve(
            spend, need, weights=w, design=design, n_boot=500
        ),
        "Ablation of the spend model (capture of K6 need)": ablation(
            _fit, fm.X, log_spend_t1, fm.feature_groups, need=need, weights=w
        ),
        "Regression to the mean (top-decile log spend)": regression_to_mean(
            np.log1p(rows.totexp_t),
            np.log1p(rows.totexp_t1),
            spend,
            weights=w,
            design=design,
            n_boot=500,
        ),
        "Incremental lift — spend model WITH mental-health features (log $)": incremental_lift(
            log_spend_t1, spend, distress, spend, weights=w, design=design, n_boot=500
        ),
        "Incremental lift — spend model WITHOUT them (blind, log $)": incremental_lift(
            log_spend_t1, spend_blind, distress, spend_blind, weights=w, design=design, n_boot=500
        ),
        "Incremental lift — avoidable utilization, non-psychiatric": incremental_lift(
            util_t1,
            preds["avoidable_util_bin"],
            distress,
            spend,
            weights=w,
            design=design,
            n_boot=500,
        ),
    }
    out = audit_report(results, ARTIFACTS_DIR / "meps_audit.html")

    cap_s = results["Top-decile capture of K6 need — spend model"]
    cap_k = results["Top-decile capture of K6 need — K6 model"]
    with_mh = results["Incremental lift — spend model WITH mental-health features (log $)"]
    blind = results["Incremental lift — spend model WITHOUT them (blind, log $)"]
    util = results["Incremental lift — avoidable utilization, non-psychiatric"]
    print(f"analytic N = {len(fm.X)} | severe-distress = {int(distress.sum())}")
    print(
        f"K6-need capture (top decile): spend {cap_s.value:.1%} vs K6 {cap_k.value:.1%} "
        f"(floor {cap_s.baseline:.1%}, oracle {cap_s.oracle:.1%})"
    )
    for label, r in [("with MH", with_mh), ("blind", blind), ("avoid.util", util)]:
        print(f"lift ({label:>10}) = {r.value:+.3f} (CI {r.ci[0]:+.3f}, {r.ci[1]:+.3f})")
    print(f"wrote {out}")
