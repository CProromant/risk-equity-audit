import pandas as pd

from riskaudit._config import ARTIFACTS_DIR
from riskaudit.audit import (
    audit_report,
    label_choice_curve,
    reclassification,
    top_k_capture,
)
from riskaudit.etl.meps import load_panel
from riskaudit.features import build_features

if __name__ == "__main__":
    fm = build_features(load_panel())
    preds = pd.read_parquet(ARTIFACTS_DIR / "predictions.parquet")

    need = fm.targets["k6"]
    w = fm.weights
    results = {
        "capture_spend": top_k_capture(preds["spend"], need, weights=w),
        "curve_spend": label_choice_curve(preds["spend"], need, weights=w),
        "reclass_spend_vs_k6": reclassification(preds["spend"], preds["k6"], weights=w),
    }
    audit_report(results, ARTIFACTS_DIR / "meps_audit.html")
