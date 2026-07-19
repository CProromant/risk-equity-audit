"""End-to-end riskaudit demo on self-contained synthetic data — no real data, no PHI.

Shows the auditor on a generic risk-stratification scenario: a model trained to
predict cost systematically misses people with real need who did not consult, so
their spending stays low this year. The audit runs unchanged — it never sees what
the data is about.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from riskaudit.audit import (
    audit_report,
    incremental_lift,
    label_choice_curve,
    reclassification,
    top_k_capture,
)

SEED = 2026


def _synthetic(n: int, rng: np.random.Generator):
    need = rng.gamma(2.0, 1.0, n)  # true severity of need
    seeks_care = rng.random(n) < 0.6  # not everyone consults
    prior_cost = need * seeks_care * 1000 + rng.gamma(1.0, 400.0, n)  # low if no care
    future_cost = np.clip(need * 1500 + rng.normal(0, 400, n), 0, None)  # need surfaces anyway
    need_measure = need + rng.normal(0, 0.3, n)  # an independent measure of need
    X = pd.DataFrame({"prior_cost": prior_cost, "age": rng.integers(18, 85, n).astype(float)})
    weights = rng.uniform(0.5, 2.0, n)
    return X, future_cost, need_measure, weights


def main(out_html: str = "demo_report.html", n: int = 5000, seed: int = SEED):
    rng = np.random.default_rng(seed)
    X, future_cost, need, weights = _synthetic(n, rng)

    # A cost-trained model predicts spending from what it can see — never "need".
    cost_model = LinearRegression().fit(X, future_cost)
    score = cost_model.predict(X)
    distress = (need > np.quantile(need, 0.8)).astype(int)

    results = {
        "Top-decile capture of need — cost model": top_k_capture(score, need, weights=weights),
        "Top-decile capture of need — need model": top_k_capture(need, need, weights=weights),
        "Reclassification: cost vs need (top decile)": reclassification(
            score, need, weights=weights
        ),
        "Label-choice curve (cost model)": label_choice_curve(score, need, weights=weights),
        "Incremental need lift (deprioritized tail)": incremental_lift(
            future_cost, cost_model.predict(X), distress, score, weights=weights
        ),
    }
    out = audit_report(results, out_html)
    cap_c = results["Top-decile capture of need — cost model"].value
    cap_n = results["Top-decile capture of need — need model"].value
    print(f"need capture (top decile): cost model {cap_c:.1%} vs need model {cap_n:.1%}")
    print(f"wrote {out}")
    return out


if __name__ == "__main__":
    main()
