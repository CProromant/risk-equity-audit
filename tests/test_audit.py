import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from riskaudit.audit import (
    ablation,
    audit_report,
    label_choice_curve,
    reclassification,
    regression_to_mean,
    top_k_capture,
)


def test_capture_weighted_hand_value():
    # top 50% by weight = units {0,1,2} (cum weight 6 >= 5); weighted need 6 of 34.
    r = top_k_capture([10, 9, 8, 7], need=[1, 1, 1, 7], k=0.5, weights=[2, 2, 2, 4], n_boot=200)
    assert r.value == round(6 / 34, 10) or abs(r.value - 6 / 34) < 1e-9
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
    r = regression_to_mean(
        y_t=[0, 0, 4, 4], y_t1=[0, 2, 2, 4], scores_t=[1, 2, 3, 4], k=0.5, n_boot=100
    )
    assert abs(r.observed_drop - 1.0) < 1e-12
    assert abs(r.rtm_share - 0.585786) < 1e-4


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


def test_audit_report_renders_every_result_type(tmp_path):
    fit = lambda X, y: LinearRegression().fit(X, y)  # noqa: E731
    results = {
        "capture": top_k_capture([3, 2, 1, 0], [1, 1, 0, 0], k=0.5, n_boot=50),
        "reclass": reclassification([4, 3, 2, 1], [1, 2, 3, 4], k=0.5),
        "curve": label_choice_curve([1, 2, 3, 4], [0, 0, 1, 1], bins=2),
        "rtm": regression_to_mean([0, 0, 4, 4], [0, 2, 2, 4], [1, 2, 3, 4], k=0.5, n_boot=50),
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
