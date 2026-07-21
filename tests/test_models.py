import json

import numpy as np
import pandas as pd
from meps.features import FeatureMatrix
from meps.models import train_all


def _features(n=250):
    rng = np.random.default_rng(0)
    X = pd.DataFrame(
        {
            "totexp_t": rng.gamma(2, 1000, n),
            "age_t": rng.integers(18, 85, n).astype(float),
            "k6_t": rng.integers(0, 24, n).astype(float),
            "rx_t": rng.integers(0, 20, n).astype(float),
        }
    )
    targets = {
        "spend": np.log1p(X.totexp_t * rng.uniform(0.5, 1.5, n)),
        "avoidable_util_bin": (X.k6_t + rng.normal(0, 3, n) > 12).astype(int),
        "k6": X.k6_t + rng.normal(0, 2, n),
    }
    w = pd.Series(rng.uniform(500, 5000, n))
    return FeatureMatrix(X, targets, w, {}, pd.Series([False] * n))


def test_train_all_writes_predictions_and_metrics(tmp_path):
    p = train_all(_features(), out_dir=tmp_path, seed=2026)
    preds = pd.read_parquet(p)
    assert set(preds.columns) == {"spend", "avoidable_util_bin", "k6"}
    assert len(preds) == 250
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    assert set(metrics) == {"spend", "avoidable_util_bin", "k6"}
    assert metrics["spend"]["metric"] == "r2"
    assert "shap_importance" in metrics["k6"]
