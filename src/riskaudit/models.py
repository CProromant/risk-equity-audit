import json
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from riskaudit._config import ARTIFACTS_DIR, SEED
from riskaudit.features import FeatureMatrix

# target -> "clf" (binary, scored by AUC) or "reg" (scored by weighted R^2)
_TASKS = {"spend": "reg", "avoidable_util_bin": "clf", "k6": "reg"}

# Same light grid for every target (D3: same routine, tuned per target, then frozen).
_GRID = [
    {"num_leaves": 15, "n_estimators": 300, "learning_rate": 0.05},
    {"num_leaves": 31, "n_estimators": 400, "learning_rate": 0.05},
    {"num_leaves": 31, "n_estimators": 600, "learning_rate": 0.03},
]
_FIXED = {"min_child_samples": 30, "n_jobs": -1, "verbose": -1}


def _estimator(task: str, params: dict, seed: int):
    cls = LGBMClassifier if task == "clf" else LGBMRegressor
    return cls(random_state=seed, **_FIXED, **params)


def _predict(model, X: pd.DataFrame, task: str) -> np.ndarray:
    return model.predict_proba(X)[:, 1] if task == "clf" else model.predict(X)


def _oof(X: pd.DataFrame, y: pd.Series, task: str, params: dict, folds, seed: int) -> np.ndarray:
    pred = np.empty(len(y))
    for tr, te in folds:
        model = _estimator(task, params, seed).fit(X.iloc[tr], y.iloc[tr])
        pred[te] = _predict(model, X.iloc[te], task)
    return pred


def _score(y: pd.Series, pred: np.ndarray, w: pd.Series, task: str) -> float:
    fn = roc_auc_score if task == "clf" else r2_score
    return float(fn(y, pred, sample_weight=w))


def _shap_importance(model, X: pd.DataFrame) -> dict:
    sv = shap.TreeExplainer(model).shap_values(X)
    if isinstance(sv, list):  # older shap: [class0, class1] -> positive class
        sv = sv[1]
    sv = np.asarray(sv)
    if sv.ndim == 3:  # newer shap: (n, features, classes) -> positive class
        sv = sv[:, :, 1]
    return dict(zip(X.columns, np.abs(sv).mean(axis=0).tolist(), strict=True))


def train_all(features: FeatureMatrix, out_dir: Path = ARTIFACTS_DIR, seed: int = SEED) -> Path:
    """Train the three same-class models and persist OOF predictions, metrics, SHAP.

    Predictions are 5-fold cross-fitted over the whole analytic sample (folds
    stratified by spend decile), so the audit runs on every row with a model
    that did not see it. Hyperparameters are tuned lightly per target over one
    shared grid and frozen (docs/decisions.md).
    """
    X, w = features.X, features.weights
    strata = pd.qcut(X.totexp_t.fillna(X.totexp_t.median()), 10, labels=False, duplicates="drop")
    folds = list(StratifiedKFold(5, shuffle=True, random_state=seed).split(X, strata))

    preds, metrics = {}, {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for target, task in _TASKS.items():
        y = features.targets[target]
        scored = [
            (_score(y, p := _oof(X, y, task, hp, folds, seed), w, task), p, hp) for hp in _GRID
        ]
        best_score, best_pred, best_hp = max(scored, key=lambda t: t[0])
        preds[target] = best_pred
        model = _estimator(task, best_hp, seed).fit(X, y)
        model.booster_.save_model(str(out_dir / f"model_{target}.txt"))
        metrics[target] = {
            "metric": "auc" if task == "clf" else "r2",
            "score": best_score,
            "params": best_hp,
            "shap_importance": _shap_importance(model, X),
        }

    pd.DataFrame(preds, index=X.index).to_parquet(out_dir / "predictions.parquet")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return out_dir / "predictions.parquet"
