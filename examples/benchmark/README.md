# Controlled benchmark

A self-contained synthetic example where the label-choice bias is **planted on
purpose**, so you can watch `riskaudit` recover a known answer. No real data, no PHI.

The generator builds a cost proxy that misses people who don't seek care, plus an
`underserved` subgroup that seeks care less often. Ranking by predicted cost then
under-serves them even though their need is just as high. `run_benchmark.py` runs
**every** public function — capture, reclassification, the label-choice curve,
cross-fitted ablation, incremental lift, regression to the mean, label robustness,
subgroup capture, and the label-blend frontier — with a survey design, and writes a
self-contained HTML report.

```bash
python examples/benchmark/run_benchmark.py    # writes benchmark_report.html
```

Because the answer is known, this doubles as an end-to-end check: the cost score
captures less need than ranking by need, the underserved subgroup is captured worse
than the served one, and relabeling toward need raises the underserved share of the
priority list. For an audit of a *real* deployed model on public data, see
[`validation/obermeyer_2019`](../../validation/obermeyer_2019/COVERAGE.md).
