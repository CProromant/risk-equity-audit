import base64
import io
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from riskaudit.audit.ablation import AblationResult  # noqa: E402
from riskaudit.audit.capture import CaptureResult  # noqa: E402
from riskaudit.audit.curves import CurveResult  # noqa: E402
from riskaudit.audit.lift import LiftResult  # noqa: E402
from riskaudit.audit.rtm import RTMResult  # noqa: E402

_STYLE = (
    "body{font-family:system-ui,sans-serif;margin:2rem;max-width:820px;line-height:1.5}"
    "table{border-collapse:collapse;margin:.5rem 0}td,th{border:1px solid #ccc;padding:4px 10px}"
    "img{max-width:100%}"
)


def _fig_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=90)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _render(name: str, r: Any) -> str:
    if isinstance(r, CaptureResult):
        return (
            f"<p><b>{name}</b>: top-{r.k:.0%} capture = {r.value:.1%} "
            f"(95% CI {r.ci[0]:.1%}–{r.ci[1]:.1%})</p>"
        )
    if isinstance(r, RTMResult):
        return (
            f"<p><b>{name}</b>: observed drop {r.observed_drop:.3g}, RTM-expected "
            f"{r.rtm_expected_drop:.3g}, RTM share {r.rtm_share:.1%} "
            f"(95% CI {r.ci[0]:.1%}–{r.ci[1]:.1%})</p>"
        )
    if isinstance(r, LiftResult):
        return (
            f"<p><b>{name}</b>: incremental lift = {r.value:.3g} "
            f"(distressed residual {r.residual_distressed:.3g} vs "
            f"{r.residual_other:.3g}; 95% CI {r.ci[0]:.3g}–{r.ci[1]:.3g})</p>"
        )
    if isinstance(r, CurveResult):
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(r.percentile, r.need_mean, marker="o")
        ax.fill_between(r.percentile, r.need_lo, r.need_hi, alpha=0.2)
        ax.set_xlabel("score percentile")
        ax.set_ylabel("mean need")
        ax.set_title(name)
        return f'<img src="{_fig_uri(fig)}" alt="{name}">'
    if isinstance(r, AblationResult):
        return (
            f"<h3>{name}</h3><h4>global Δ</h4>{r.global_delta.to_html()}"
            f"<h4>capture Δ</h4>{r.capture_delta.to_html()}"
        )
    if isinstance(r, pd.DataFrame):
        return f"<h3>{name}</h3>{r.to_html()}"
    return f"<p><b>{name}</b>: {r}</p>"


def audit_report(results: dict[str, Any], out_html: str | Path) -> Path:
    """Render audit results into one self-contained HTML file.

    Takes the objects returned by the audit functions (keyed by name) and
    writes a single HTML document with every figure inlined as a data URI, so
    it opens with no external assets. Returns the written path.
    """
    body = "\n".join(_render(k, v) for k, v in results.items())
    html = (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>riskaudit report</title><style>{_STYLE}</style></head>"
        f"<body><h1>riskaudit report</h1>{body}</body></html>"
    )
    out = Path(out_html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
