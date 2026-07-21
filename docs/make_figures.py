"""Regenerate the README figures from the MEPS example, using riskaudit itself.

Run after the pipeline (`make models`): reads artifacts/predictions.parquet and
writes docs/img/{capture.png,label_choice_curve.png}. The figures are what the
library produces — no hand-drawn marketing.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from riskaudit._config import ARTIFACTS_DIR
from riskaudit.audit import label_choice_curve, top_k_capture
from riskaudit.etl.meps import load_panel
from riskaudit.features import build_features

IMG = Path(__file__).with_name("img")
NEED = "#4C78A8"  # need-trained model
SPEND = "#E4572E"  # spend-trained model (the finding)
REF = "#c9c9c9"  # oracle / floor references

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def _load():
    fm = build_features(load_panel())
    preds = pd.read_parquet(ARTIFACTS_DIR / "predictions.parquet").reindex(fm.X.index)
    return fm, preds


def capture_bar(fm, preds):
    need, w = fm.targets["k6"], fm.weights
    spend = top_k_capture(preds["spend"], need, weights=w)
    k6 = top_k_capture(preds["k6"], need, weights=w)
    labels = [
        "Oracle\n(rank by need)",
        "Need-trained\nmodel",
        "Spend-trained\nmodel",
        "Random\n(floor)",
    ]
    vals = [spend.oracle, k6.value, spend.value, spend.baseline]
    colors = [REF, NEED, SPEND, REF]

    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    y = range(len(labels))[::-1]
    ax.barh(list(y), vals, color=colors, height=0.62)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlim(0, max(vals) * 1.16)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    for yi, v in zip(y, vals, strict=True):
        ax.text(v + 0.006, yi, f"{v:.0%}", va="center", fontsize=10.5)
    ax.set_xlabel("Share of top-decile measured need captured")
    fig.subplots_adjust(top=0.80)
    fig.text(
        0.02,
        0.965,
        "A spend-trained model captures need barely above chance",
        fontsize=12.5,
        weight="bold",
    )
    fig.text(
        0.02,
        0.885,
        "MEPS 2021–2023 · top decile · population-weighted, design-based CIs",
        fontsize=9.5,
        color="#666",
    )
    fig.savefig(IMG / "capture.png")
    plt.close(fig)


def curve(fm, preds):
    need, w = fm.targets["k6"], fm.weights
    ck6 = label_choice_curve(preds["k6"], need, weights=w, bins=10)
    cs = label_choice_curve(preds["spend"], need, weights=w, bins=10)

    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    for c, color, name in [(ck6, NEED, "Need-trained model"), (cs, SPEND, "Spend-trained model")]:
        ax.plot(c.percentile, c.need_mean, "-o", color=color, ms=4, label=name)
        ax.fill_between(c.percentile, c.need_lo, c.need_hi, color=color, alpha=0.15)
    ax.set_xlabel("Model score percentile")
    ax.set_ylabel("Mean measured need (K6)")
    ax.legend(frameon=False, loc="upper left")
    fig.subplots_adjust(top=0.80)
    sub = "A model that ranks by need rises steeply; the spend model's is much shallower"
    fig.text(
        0.02,
        0.965,
        "Where the highest-need people sit on each model's score",
        fontsize=12.5,
        weight="bold",
    )
    fig.text(0.02, 0.885, sub, fontsize=9.5, color="#666")
    fig.savefig(IMG / "label_choice_curve.png")
    plt.close(fig)


if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    fm, preds = _load()
    capture_bar(fm, preds)
    curve(fm, preds)
    print(f"wrote {IMG / 'capture.png'} and {IMG / 'label_choice_curve.png'}")
