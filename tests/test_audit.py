import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

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


def test_capture_weighted_hand_value():
    # top 50% by weight = units {0,1,2} (cum weight 6 >= 5); weighted need 6 of 34.
    r = top_k_capture([10, 9, 8, 7], need=[1, 1, 1, 7], k=0.5, weights=[2, 2, 2, 4], n_boot=200)
    assert abs(r.value - 6 / 34) < 1e-9
    assert r.ci[0] <= r.ci[1] and np.isfinite(r.ci).all()


def test_capture_all_need_in_top_is_one():
    r = top_k_capture([3, 2, 1, 0], need=[1, 1, 0, 0], k=0.5, n_boot=50)
    assert abs(r.value - 1.0) < 1e-12


def test_reclassification_full_swap():
    df = reclassification([4, 3, 2, 1], [1, 2, 3, 4], k=0.5)
    assert df.loc["stay", "weight"] == 0
    assert df.loc["dropped", "weight"] == 2
    assert df.loc["added", "weight"] == 2
    assert df.loc["out", "weight"] == 0
    assert abs(df["share"].sum() - 1.0) < 1e-12


def test_curve_monotone_hand_values():
    c = label_choice_curve([1, 2, 3, 4], need=[0, 0, 1, 1], bins=2)
    assert list(c.percentile) == [25.0, 75.0]
    assert abs(c.need_mean[0] - 0.0) < 1e-12
    assert abs(c.need_mean[1] - 1.0) < 1e-12


def test_rtm_share_matches_formula():
    # top group y_t mean 4 -> predicted t+1 = mu_t1 + beta*(4-mu_t) = 2 + 0.5*2 = 3;
    # expected drop 1 equals observed drop 1 -> share 1.0.
    r = regression_to_mean(
        y_t=[0, 0, 4, 4], y_t1=[0, 2, 2, 4], scores_t=[1, 2, 3, 4], k=0.5, n_boot=100
    )
    assert abs(r.observed_drop - 1.0) < 1e-12
    assert abs(r.rtm_expected_drop - 1.0) < 1e-12
    assert abs(r.rtm_share - 1.0) < 1e-9


def test_capture_reports_floor_and_oracle():
    r = top_k_capture([4, 3, 2, 1], need=[1, 1, 1, 10], k=0.5, n_boot=50)
    assert r.baseline == 0.5  # random-score floor = k
    assert r.oracle >= r.value  # ranking by need itself is the ceiling


def test_design_single_psu_per_stratum_collapses_ci():
    # one PSU per stratum -> cluster resampling can't vary -> zero-width CI at value.
    design = SurveyDesign(strata=[1, 1, 2, 2, 3, 3], psu=[1, 1, 1, 1, 1, 1])
    r = top_k_capture([6, 5, 4, 3, 2, 1], need=[0, 0, 0, 1, 1, 1], k=0.5, design=design, n_boot=50)
    assert abs(r.ci[0] - r.value) < 1e-9 and abs(r.ci[1] - r.value) < 1e-9


def test_design_affects_ci_not_point_estimate():
    design = SurveyDesign(strata=[1, 1, 2, 2], psu=[1, 2, 1, 2])
    base = top_k_capture([4, 3, 2, 1], [1, 1, 1, 0], k=0.5, n_boot=80)
    des = top_k_capture([4, 3, 2, 1], [1, 1, 1, 0], k=0.5, n_boot=80, design=design)
    assert des.value == base.value
    assert np.isfinite(des.ci).all() and des.ci[0] <= des.ci[1]


def test_rtm_no_drop_returns_nan_share():
    # top-k outcome does not fall (y_t == y_t1) -> share is undefined, not a crash.
    r = regression_to_mean([1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], k=0.5, n_boot=20)
    assert r.observed_drop == 0.0
    assert math.isnan(r.rtm_share)


def test_ablation_relevant_group_dominates_global_loss():
    rng = np.random.default_rng(0)
    n = 400
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    y = 3 * x1 + 20  # only x1 carries signal; x2 is noise
    X = pd.DataFrame({"x1": x1, "x2": x2})
    res = ablation(
        lambda X, y: LinearRegression().fit(X, y),
        X,
        y,
        {"signal": ["x1"], "noise": ["x2"]},
    )
    assert res.global_delta.loc["signal", "delta"] > 0.9
    assert abs(res.global_delta.loc["noise", "delta"]) < 0.1


def test_incremental_lift_hand_value():
    # top-50% by weight = the 3 highest scores; tail = scores 7,6,5 (indices 3,4,5).
    # tail residuals: distressed {2,4} mean 3, non-distressed {1} mean 1 -> lift 2.
    r = incremental_lift(
        y_t1=[0, 0, 0, 2, 4, 1],
        y_pred=[0, 0, 0, 0, 0, 0],
        distress=[0, 0, 0, 1, 1, 0],
        scores=[10, 9, 8, 7, 6, 5],
        k=0.5,
        n_boot=100,
    )
    assert abs(r.value - 2.0) < 1e-12
    assert abs(r.residual_distressed - 3.0) < 1e-12
    assert abs(r.residual_other - 1.0) < 1e-12


def test_ablation_binary_target_uses_auc():
    rng = np.random.default_rng(1)
    n = 200
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    y = (x1 > 0).astype(int)  # binary -> ablation scores it with AUC
    X = pd.DataFrame({"x1": x1, "x2": x2})
    res = ablation(
        lambda X, y: LinearRegression().fit(X, y),
        X,
        y,
        {"signal": ["x1"], "noise": ["x2"]},
    )
    assert res.global_delta.loc["signal", "delta"] > res.global_delta.loc["noise", "delta"]


def test_ablation_cross_fit_detects_overfit_signal():
    from lightgbm import LGBMRegressor

    rng = np.random.default_rng(2026)
    n = 1500
    noise = rng.normal(size=(n, 8))
    sig = rng.normal(size=(n, 2))
    y = sig[:, 0] + 0.2 * noise[:, :3].sum(1) + rng.normal(0, 0.5, n)
    X = pd.DataFrame(np.hstack([noise, sig]), columns=[f"n{i}" for i in range(8)] + ["s0", "s1"])

    def fit(X, y):
        return LGBMRegressor(
            random_state=2026, num_leaves=63, n_estimators=250, learning_rate=0.1, verbose=-1
        ).fit(X, y)

    res = ablation(fit, X, y, {"signal": ["s0", "s1"], "noise": ["n0", "n1"]}, cv=4)
    # cross-fitting recovers the real drop; in-sample refit would report ~0
    assert res.global_delta.loc["signal", "delta"] > 0.1
    assert res.global_delta.loc["signal", "delta"] > res.global_delta.loc["noise", "delta"]


def test_audit_report_renders_every_result_type(tmp_path):
    fit = lambda X, y: LinearRegression().fit(X, y)  # noqa: E731
    results = {
        "capture": top_k_capture([3, 2, 1, 0], [1, 1, 0, 0], k=0.5, n_boot=50),
        "reclass": reclassification([4, 3, 2, 1], [1, 2, 3, 4], k=0.5),
        "curve": label_choice_curve([1, 2, 3, 4], [0, 0, 1, 1], bins=2),
        "rtm": regression_to_mean([0, 0, 4, 4], [0, 2, 2, 4], [1, 2, 3, 4], k=0.5, n_boot=50),
        "lift": incremental_lift(
            [0, 0, 0, 2, 4, 1],
            [0] * 6,
            [0, 0, 0, 1, 1, 0],
            [10, 9, 8, 7, 6, 5],
            k=0.5,
            n_boot=50,
        ),
        "ablation": ablation(
            fit,
            pd.DataFrame({"a": [1.0, 2, 3, 4], "b": [4.0, 3, 2, 1]}),
            [1.0, 2, 3, 4],
            {"g": ["a"]},
        ),
        "note": "plain text",
    }
    out = audit_report(results, tmp_path / "r.html")
    html = out.read_text(encoding="utf-8")
    assert out.exists()
    assert "capture" in html and "<table" in html and "data:image/png" in html
    assert "RTM share" in html and "global Δ" in html and "plain text" in html
    assert "incremental lift" in html
