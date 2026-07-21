# Validation coverage — Obermeyer et al. (2019)

> Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias
> in an algorithm used to manage the health of populations. *Science* 366(6464), 447–453.
> https://doi.org/10.1126/science.aax2342

Goal: check that `riskaudit`'s public-API metrics **surface the bias the paper found**, on
the authors' own [public synthetic dataset](https://gitlab.com/labsysmed/dissecting-bias)
(`data_new.csv`, SHA-256 `5341f90f…`, 48 784 rows). Reproduce with `make validate-obermeyer`.

## Mapping

- **`scores`** = `risk_score_t` (the deployed algorithm's cost-based risk score).
- **`need`** = `gagne_sum_t` (count of active chronic conditions — the health measure the paper
  argues the algorithm *should* track).
- **tier** = top 3% by score (the paper's 97th-percentile auto-enroll threshold, `k=0.03`).
- Race split is a plain slice of the same arrays; `group_capture` (v0.2 Fase B) will fold it in.

## Results

| Paper claim (real data) | riskaudit metric | Reproduced (synthetic) | Verdict |
|---|---|---|---|
| The score tracks cost, leaving health need behind | `top_k_capture` | capture **0.12** vs oracle 0.19, floor 0.03 | direction ✓ |
| At the same risk score, Black patients are sicker | mean `gagne_sum_t` in the tier | Black **6.62** vs White **5.21** conditions | direction ✓ |
| Less of Black patients' need is captured | `top_k_capture` within race | Black **0.10** < White **0.12** | direction ✓ |
| Black share of the tier rises when ranked by health (17.7% → 46.5%) | share, cost- vs health-label top-*k* | **20.0% → 23.3%** | direction ✓, magnitude attenuated |
| Relabeling reshuffles who is prioritized | `reclassification` | **64%** of the auto-enroll list turns over | ✓ |

## The magnitude discrepancy (documented, not tuned away)

The **directions all reproduce**; the **magnitudes are smaller** than the paper's real-data
figures — most visibly, the Black-share shift is 20.0%→23.3% here versus 17.7%→46.5% in the
paper. The public dataset is **synthetic**: the authors generated it to let others run their
code, and it reproduces the qualitative structure with attenuated racial signal (only 11.4%
of rows are coded Black, and the cost score already correlates with illness). Per the project's
hard rule, this discrepancy is recorded rather than absorbed by widening a tolerance. The
protected test therefore asserts **directions only** — it would catch a metric that stopped
detecting the bias, not a magnitude that drifts with the data.

What this validates: the API computes the audit quantities that make label-choice bias
visible. What it does **not** claim: a numeric replication of the paper (impossible without the
real claims data, which is not public).
