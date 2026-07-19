# Demo

A self-contained, end-to-end run of `riskaudit` on **synthetic data — no real
data and no PHI**. It exists to show the tool working without access to any
dataset.

```bash
python demo/run_demo.py   # a few seconds; writes demo_report.html
```

The script generates a generic risk-stratification scenario where some people
with real need do not consult, so their cost stays low. A model trained to
predict cost deprioritizes them; the audit — the same functions used on MEPS —
quantifies the need it leaves behind and writes a self-contained HTML report.

The data is invented in the script and deterministic (`seed=2026`); it is not
Synthea and not MEPS. The point is the auditor, which only ever sees scores, a
need measure, and weights.
