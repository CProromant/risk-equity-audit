# MEPS case study — methods

Statistical methods and modeling choices for the **MEPS worked example**
(`examples/meps`). The library's per-metric math lives in the `riskaudit.audit`
docstrings; this file gives the case-study reasoning — what counts as need, the
design-based estimation, model comparability — and the honest limits. Decisions
are logged in `docs/decisions.md`.

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

**Untreated-distress flag.** The mechanism is about people in distress the system has
not seen. A person is *treated for mental health* in year $t$ if the Conditions file
(HC-231) records a mental-health condition (ICD-10 `F01`–`F99`, or a CCSR `MBD*`
category) or the Prescribed Medicines file (HC-229A) records a psychotropic (Multum
classes for antidepressants, antipsychotics, anxiolytics/sedatives/hypnotics,
antimanic, ADHD agents and psychotherapeutics; broad CNS catch-all classes excluded).
The **untreated-distress** group is K6$_t \ge 13$ and not treated — a descriptive flag,
never a target (§6). In the panel it is ~63 people (40 in the K6-both-years analytic sample).

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
those with measured distress generated more of the outcome than the model
predicted. It is reported three ways, and the honest reading needs all three
(MEPS panel, design-based CIs):

- **Total spend, model *with* the mental-health features:** +0.77 log-dollars
  (95% CI excludes zero). Even given K6, PHQ-2 and the treatment flag, optimizing
  against spend deprioritizes distressed people and under-predicts their cost — so
  the bias is driven by the **label**, not by missing information.
- **Total spend, "blind" model *without* those features:** +1.05 (CI excludes
  zero). Larger, as expected — blindness by construction.
- **Avoidable utilization (ER + hospitalizations), non-psychiatric:** ≈ +0.04
  (95% CI includes zero) — **no effect**.

The third row is a genuine limitation, not a footnote. The mechanism this project
set out to show — untreated distress surfacing as *non-psychiatric* medical need —
is **not** demonstrated here: on total spend the lift is real but may be partly
mental-health spending (the residual circularity §1 warns about), and on the
non-psychiatric utilization outcome it vanishes (which may also reflect how coarse
a binary ER/hospitalization flag is). Settling it needs a non-psychiatric *spend*
target (total spend minus mental-health spend), which is backlog. What survives
cleanly: the spend model captures need barely above chance (§5) and under-serves
the distressed on its own currency of total cost.

Reported with a design-based confidence interval (§3); defaults $k = 0.10$, K6 $\ge 13$.

## 3. Design-based estimation (D4)

Everything reported is weighted (guardrail 3). Longitudinal quantities use
`LONGWT`, or `LSAQWT` for SAQ-derived quantities; pooled FYC descriptives use the
year's `PERWT*F`. Variance is by a **design-based (stratified cluster) bootstrap**
over `VARSTR`/`VARPSU` — nonparametric, because the audit statistics (capture,
lift) are nonlinear so Taylor linearization does not apply cleanly.

The analysis runs on the filtered analytic sample (panel completers ∩ valid K6 in
both years), and the cluster bootstrap resamples PSUs **within that domain**
(`SurveyDesign(strata=VARSTR, psu=VARPSU)`; each resample draws PSUs with
replacement within strata). This is valid as long as each stratum keeps ≥ 2 PSUs
in the domain; `SurveyDesign` **warns** when a stratum collapses to one PSU, whose
variance contribution is then zero (biasing the CI low). On the MEPS panel 3 strata
collapse — a small share. The stricter alternative — keep the full frame and enter
the domain through a 0/1 indicator (true domain estimation) — is cleaner and is
backlog. Omitting the design falls back to a plain row bootstrap for non-survey data.

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
- `ablation` — **cross-fit** with and without the `mental_health` group,
  contrasting Δ global performance (measured out-of-fold, not assumed) with
  Δ capture of an independent need measure passed as `need=`.
- `regression_to_mean` — the share of any top-$k$ outcome drop that is a
  statistical artifact; descriptive only (selection is on the score, not the
  outcome, and it is scale-dependent).
- `top_k_capture` also returns a **floor** (= $k$, a random score) and an
  **oracle** (ranking by need itself); a raw capture is read against both.

## 6. Two honesty constraints

- **T3 is near-tautological.** K6$_t$ dominates the prediction of K6$_{t+1}$, so a
  strong T3 model and its capture are not findings — they are a sanity check that
  the machinery works, and are reported as such.
- **The severe untreated subgroup is small** (n ≈ 40 in the K6-both-years analytic
  sample; ~63 in the full panel). It is described with wide design-based CIs and
  never modeled. The reported finding is the population-level incremental lift of
  §2, not this subgroup.
