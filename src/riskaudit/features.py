from dataclasses import dataclass

import pandas as pd


@dataclass
class FeatureMatrix:
    X: pd.DataFrame
    targets: dict[str, pd.Series]
    weights: pd.Series
    feature_groups: dict[str, list[str]]


def build_features(panel: pd.DataFrame) -> FeatureMatrix:
    """Assemble X_t (all measured at 2021) and the three t+1 targets.

    Targets: T1 log1p spend, T2 avoidable-utilization count and its binary,
    T3 continuous K6. Mental-health columns carry feature_group="mental_health"
    so ablation can drop them as a set (PROTOCOL §4.2).
    """
    raise NotImplementedError
