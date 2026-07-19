import numpy as np
import pandas as pd

from riskaudit.features import build_features

_CONST = [
    "age_t",
    "sex",
    "race_eth",
    "region_t",
    "poverty_t",
    "insurance_t",
    "htn_t",
    "chd_t",
    "other_heart_t",
    "stroke_t",
    "emphysema_t",
    "high_chol_t",
    "cancer_t",
    "diabetes_t",
    "arthritis_t",
    "asthma_t",
    "office_visits_t",
    "er_t",
    "ip_disch_t",
    "rx_t",
    "totexp_t",
    "totslf_t",
    "phq2_t",
]


def _panel():
    df = pd.DataFrame({c: [1.0] * 4 for c in _CONST})
    df["k6_t"] = [20, 18, 4, 10]
    df["k6_t1"] = [15, 10, 3, 30]  # last row: K6 out of range -> dropped
    df["weight_saq_long"] = [1000.0, 1000.0, 1000.0, 1000.0]
    df["treated_mh"] = [0, 1, 0, 0]
    df["totexp_t1"] = [100.0, 50.0, 0.0, 5.0]
    df["er_t1"] = [2, 0, 0, 0]
    df["ip_disch_t1"] = [0, 1, 0, 0]
    return df


def test_build_features_restricts_to_valid_k6_and_positive_weight():
    assert len(build_features(_panel()).X) == 3


def test_build_features_targets_groups_and_flag():
    fm = build_features(_panel())
    assert set(fm.targets) == {"spend", "avoidable_util", "avoidable_util_bin", "k6"}
    assert fm.feature_groups["mental_health"] == ["k6_t", "phq2_t", "treated_mh"]
    assert abs(fm.targets["spend"].iloc[0] - np.log1p(100.0)) < 1e-12
    assert fm.targets["avoidable_util_bin"].tolist() == [1, 1, 0]
    assert fm.severe_untreated.tolist() == [True, False, False]
