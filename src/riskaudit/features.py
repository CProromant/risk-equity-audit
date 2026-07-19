from dataclasses import dataclass

import numpy as np
import pandas as pd

_DEMO = ["age_t", "sex", "race_eth", "region_t", "poverty_t", "insurance_t"]
_CHRONIC = [
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
]
_UTIL = ["office_visits_t", "er_t", "ip_disch_t", "rx_t"]
_SPEND = ["totexp_t", "totslf_t"]
_MENTAL = ["k6_t", "phq2_t", "treated_mh"]
_CATEGORICAL = ["sex", "race_eth", "region_t", "poverty_t", "insurance_t"]


@dataclass
class FeatureMatrix:
    X: pd.DataFrame
    targets: dict[str, pd.Series]
    weights: pd.Series
    feature_groups: dict[str, list[str]]
    severe_untreated: pd.Series


def build_features(panel: pd.DataFrame) -> FeatureMatrix:
    """Assemble X_t (all measured at 2021) and the three t+1 targets.

    Restricted to the K6 analytic domain — a valid K6 in both years and a
    positive SAQ longitudinal weight — the sample on which the three models are
    comparable. Targets: T1 log1p spend, T2 avoidable-utilization count and its
    binary, T3 continuous K6. Mental-health columns carry
    feature_group="mental_health" so ablation can drop them as a set. Rows keep
    the panel index, so the caller can recover stratum/PSU for a design-based CI.
    """
    d = panel[panel.k6_t.between(0, 24) & panel.k6_t1.between(0, 24) & (panel.weight_saq_long > 0)]

    X = d[_DEMO + _CHRONIC + _UTIL + _SPEND + _MENTAL].copy()
    X[_CATEGORICAL] = X[_CATEGORICAL].astype("category")

    avoidable = d.er_t1 + d.ip_disch_t1
    targets = {
        "spend": np.log1p(d.totexp_t1),
        "avoidable_util": avoidable,
        "avoidable_util_bin": (avoidable >= 1).astype(int),
        "k6": d.k6_t1,
    }
    groups = {
        "demographics": _DEMO,
        "chronic": _CHRONIC,
        "utilization": _UTIL,
        "spend": _SPEND,
        "mental_health": _MENTAL,
    }
    severe_untreated = (d.k6_t >= 13) & (d.treated_mh == 0)
    return FeatureMatrix(X, targets, d.weight_saq_long, groups, severe_untreated)
