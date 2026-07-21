"""Reproduce the Obermeyer et al. (2019) label-choice audit with riskaudit's public API.

Run ``make validate-obermeyer`` (or ``python -m validation.obermeyer_2019.reproduce``).
The public dataset is synthetic, so magnitudes are attenuated versus the paper's
real-data figures; directions match. See COVERAGE.md — the discrepancy is documented,
not tuned away.
"""

import numpy as np
import pandas as pd

from riskaudit.audit import reclassification, top_k_capture

from .download import fetch

K_AUTO = 0.03  # auto-enroll tier: top ~3%, the paper's 97th-percentile threshold


def reproduce() -> dict[str, float]:
    df = pd.read_csv(fetch())
    score = df["risk_score_t"].to_numpy()  # deployed cost-based risk score
    need = df["gagne_sum_t"].to_numpy()  # active chronic conditions = health need
    black = (df["race"] == "black").to_numpy()

    c = top_k_capture(score, need, k=K_AUTO)
    cb = top_k_capture(score[black], need[black], k=K_AUTO)
    cw = top_k_capture(score[~black], need[~black], k=K_AUTO)

    top_cost = score >= np.quantile(score, 1 - K_AUTO)
    top_need = need >= np.quantile(need, 1 - K_AUTO)
    rc = reclassification(score, need, k=K_AUTO)

    return {
        "capture": c.value,
        "floor": c.baseline,
        "oracle": c.oracle,
        "capture_black": cb.value,
        "capture_white": cw.value,
        "black_share_cost": black[top_cost].mean(),
        "black_share_health": black[top_need].mean(),
        "illness_black": need[top_cost & black].mean(),
        "illness_white": need[top_cost & ~black].mean(),
        "turnover": rc.loc["dropped", "weight"]
        / (rc.loc["stay", "weight"] + rc.loc["dropped", "weight"]),
    }


def main() -> None:
    r = reproduce()
    rows = [
        ("top-3% capture of health need", f"below oracle {r['oracle']:.2f}", f"{r['capture']:.2f}"),
        (
            "  captured for Black vs White",
            "less for Black",
            f"{r['capture_black']:.2f} vs {r['capture_white']:.2f}",
        ),
        (
            "mean conditions at auto-enroll, Black vs White",
            "Black sicker",
            f"{r['illness_black']:.2f} vs {r['illness_white']:.2f}",
        ),
        (
            "Black share of tier: cost- vs health-label",
            "17.7% -> 46.5%",
            f"{r['black_share_cost']:.1%} -> {r['black_share_health']:.1%}",
        ),
        ("auto-enroll list turnover under relabeling", "substantial", f"{r['turnover']:.0%}"),
    ]
    print(f"{'audit metric':<48}{'paper (real)':>18}{'riskaudit (synthetic)':>24}")
    print("-" * 90)
    for name, paper, got in rows:
        print(f"{name:<48}{paper:>18}{got:>24}")


if __name__ == "__main__":
    main()
