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
    ).fit(X, y)


if __name__ == "__main__":
    panel = load_panel()
    fm = build_features(panel)
    preds = pd.read_parquet(ARTIFACTS_DIR / "predictions.parquet")
    rows = panel.loc[fm.X.index]

    design = SurveyDesign(strata=rows.stratum.values, psu=rows.psu.values)
    w = fm.weights
    need = fm.targets["k6"]  # K6_{t+1}, continuous
    spend = preds["spend"]
    k6 = preds["k6"]
    distress = (fm.X.k6_t >= 13).astype(int)

    results = {
        "Top-decile capture of K6 need — spend model": top_k_capture(
            spend, need, weights=w, design=design, n_boot=500
        ),
        "Top-decile capture of K6 need — K6 model": top_k_capture(
            k6, need, weights=w, design=design, n_boot=500
        ),
        "Reclassification: spend vs K6 (top decile)": reclassification(spend, k6, weights=w),
        "Label-choice curve (spend model)": label_choice_curve(spend, need, weights=w),
        "Ablation of the spend model": ablation(
            _fit, fm.X, fm.targets["spend"], fm.feature_groups, weights=w
        ),
        "Regression to the mean (top-decile spend)": regression_to_mean(
            rows.totexp_t, rows.totexp_t1, spend, weights=w, design=design, n_boot=500
        ),
        "Incremental need lift (deprioritized tail)": incremental_lift(
            fm.targets["spend"], spend, distress, spend, weights=w, design=design, n_boot=500
        ),
    }
    out = audit_report(results, ARTIFACTS_DIR / "meps_audit.html")

    cap_s = results["Top-decile capture of K6 need — spend model"]
    cap_k = results["Top-decile capture of K6 need — K6 model"]
    lift = results["Incremental need lift (deprioritized tail)"]
    print(f"analytic N = {len(fm.X)} | severe-distress = {int(distress.sum())}")
    print(f"K6-need capture (top decile): spend {cap_s.value:.1%} vs K6 {cap_k.value:.1%}")
    print(f"incremental lift = {lift.value:+.3f} (95% CI {lift.ci[0]:+.3f}, {lift.ci[1]:+.3f})")
    print(f"wrote {out}")
