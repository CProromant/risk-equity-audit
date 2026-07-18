# Methods

Binding statistical reference for `risk-equity-audit`. Every metric in
`riskaudit.audit` and every modeling choice in the MEPS case study is defined or
justified here; the decisions themselves are logged in `docs/decisions.md`. Where
a function's docstring already carries the exact formula (PROTOCOL §4.4), this
file gives the reasoning and points to it rather than repeating it.

## 1. What counts as "need" (D2, D5)

**Normative stance (D2).** The primary argument is on **equity** grounds: a person
in measured psychological distress who does not seek care has genuine health need
whether or not that need has yet produced spending. A model that prioritizes by
spending under-serves legitimate need by construction. Measured distress (K6) is
therefore taken as the yardstick of need for the priority question.

This stance invites a circularity objection — *"need was defined as the very thing
the spend model does not predict, so of course it looks biased."* We answer it
empirically, not rhetorically, with the incremental-lift metric of §2, whose
outcome is realized future spending rather than K6.

**Operationalizing need (D5).** K6 is an ordinal 0–24 sum; summing it as a mass of
need treats the ordinal as cardinal. We therefore use two operationalizations and
report both, with the continuous one primary:

- **Primary** — K6 continuous. Capture and curve metrics use continuous need.
- **Robustness** — binary K6 ≥ 13 (severe-distress threshold).

A result is reported as a finding only if it holds under both.

## 2. Contribution metric — incremental need lift in the low-score tail

This is the original, non-Obermeyer contribution and the empirical spine of the
argument. Existing metrics (capture, curves, reclassification) describe *that* the
priority sets differ; this one shows the difference has consequences the spend
model itself would care about.

Let the deployed spend model produce a risk score $\hat s_i$ and a prediction
$\hat y_i$ of the future outcome it targets (T1: realized year-$t{+}1$ medical
spending, or T2 avoidable utilization). Rank by $\hat s_i$; the top-$k$ by weight
is the priority set, and its complement $L$ — the people the model denies the
program — is the **deprioritized tail**. Let $d_i \in \{0,1\}$ mark measured
distress at $t$ (K6$_t \ge 13$; continuous variant in robustness), and
$r_i = y_{i,t+1} - \hat y_i$ the realized residual: how much the model under- or
over-predicted each person's actual future outcome.

The incremental need lift is the weighted difference in mean residual between
distressed and non-distressed people **within** the deprioritized tail:

$$
\mathrm{Lift}_k \;=\;
\frac{\sum_{i \in L} w_i\, d_i\, r_i}{\sum_{i \in L} w_i\, d_i}
\;-\;
\frac{\sum_{i \in L} w_i\, (1-d_i)\, r_i}{\sum_{i \in L} w_i\, (1-d_i)} .
$$

$\mathrm{Lift}_k > 0$ means that among the people the spend model called low-risk,
those with measured distress went on to generate systematically more medical need
than the model predicted — need it was blind to. Because $y_{t+1}$ is realized
cost/utilization, the spend model's **own** currency and not K6, the result does
not presuppose the equity premise of §1: it holds even for a reader who cares only
about future spending. That is what defeats the circularity objection, and it
shows the blind spot is also an efficiency loss.

Reported with a design-based confidence interval (§3). The tail fraction $1-k$ and
the distress cutoff are parameters; defaults are $k = 0.10$ and K6 $\ge 13$.

## 3. Design-based estimation (D4)

Everything reported is weighted (guardrail 3). Longitudinal quantities use
`LONGWT`, or `LSAQWT` for SAQ-derived quantities; pooled FYC descriptives use the
year's `PERWT*F`. Variance is by Taylor linearization over `VARSTR`/`VARPSU`.

Subpopulations — panel completers ∩ valid K6 in both years — are handled by
**domain (subpopulation) estimation**: the full sampling frame is kept and the
domain enters through a 0/1 indicator. We never physically filter the dataset and
re-run the design on the subset; that understates variance and is the classic MEPS
trap. This is the project standard for every subgroup result, including the severe
subgroup of §6.

The audit package implements design-based variance as a **stratified cluster
bootstrap** (`SurveyDesign(strata=VARSTR, psu=VARPSU)`): each resample draws PSUs
with replacement within strata rather than individual rows. Omitting the design
falls back to a plain row bootstrap for non-survey data.

## 4. Model comparability (D3)

The three targets — T1 `log1p(TOTEXP_t1)`, T2 avoidable-utilization count and its
binary, T3 continuous K6$_{t+1}$ — share the **same estimator class (LightGBM)**
and the **same feature matrix** $X_t$. That identity is what makes the
prioritization comparison meaningful: only the outcome changes.

Hyperparameters are tuned **lightly per target** with one shared 5-fold CV routine
and then frozen, rather than forced identical across targets. Forcing identical HP
can handicap a target and bias the very prioritization contrast under study. The
tuning grid and the frozen values are persisted with each run.

## 5. Audit metrics

The exact formula for each lives in its docstring; their roles:

- `top_k_capture`, `label_choice_curve` — descriptive: how much measured need the
  priority set holds, and where high-need units sit on the score.
- `reclassification` — who enters and leaves the priority set when the label
  switches from A to B; the population cost of the label choice.
- `ablation` — drop the `mental_health` feature group and refit, contrasting
  Δ global performance (expected ≈ 0) with Δ capture. Focused on T1/T2.
- `regression_to_mean` — the share of any top-$k$ outcome drop that is a
  statistical artifact rather than a real effect.

## 6. Two honesty constraints

- **T3 is near-tautological.** K6$_t$ dominates the prediction of K6$_{t+1}$, so a
  strong T3 model and its capture are not findings — they are a sanity check that
  the machinery works, and are reported as such.
- **The severe untreated subgroup is small** (n ≈ 45). It is described with wide
  design-based CIs and never modeled. The reported finding is the population-level
  incremental lift of §2, not this subgroup.
