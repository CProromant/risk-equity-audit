# risk-equity-audit

**Auditing label-choice bias in healthcare risk-stratification models.**

`riskaudit` is a Python library that audits *any* risk-stratification model for **label-choice bias** — how much real "need" a model leaves behind when it is trained on a convenient proxy (usually healthcare **spending**) instead of need itself. It works on any model's output: give it the `scores` a model assigned, an independent `need` measure, and population `weights`.

[![CI](https://github.com/CProromant/risk-equity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/CProromant/risk-equity-audit/actions/workflows/ci.yml)
![license](https://img.shields.io/badge/license-MIT-green)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21461268-blue)](https://doi.org/10.5281/zenodo.21461268)

<p align="center">
  <img src="https://raw.githubusercontent.com/CProromant/risk-equity-audit/main/docs/img/capture.png" width="720"
       alt="Top-decile capture of measured need on MEPS: oracle 41 percent, need-trained model 29 percent, spend-trained model 15 percent, random floor 10 percent.">
</p>

<p align="center"><sub><code>riskaudit</code>'s own output on the MEPS example: a deployed spend-trained model captures barely more measured need than a random score — and less than half of what ranking by need would.</sub></p>

*(Versión en español más abajo — [ir al español](#español).)*

---

## Install

```bash
pip install riskaudit
```

Python ≥ 3.11. The core is light (numpy, pandas, scikit-learn, matplotlib); the MEPS example's heavier stack is an extra: `pip install "riskaudit[meps]"`.

## Quickstart

Audit your own model's scores in a few lines — no training, no PHI:

```python
import numpy as np
from riskaudit.audit import top_k_capture

rng = np.random.default_rng(2026)
scores  = rng.random(5_000)   # what your risk model output per person
need    = rng.random(5_000)   # an independent measure of real need
weights = rng.random(5_000)   # population / survey weights

c = top_k_capture(scores, need, k=0.10, weights=weights)
print(f"top-decile capture: {c.value:.0%}  (floor {c.baseline:.0%}, oracle {c.oracle:.0%})")
# top-decile capture: 10%  (floor 10%, oracle 19%)   <- a random score sits at the floor
```

Every result carries a confidence interval (row or design-based) and reads against its **floor** (a random score) and **oracle** (ranking by need itself) — a capture number is meaningless without them. `audit_report(results, "audit.html")` bundles the whole set into a self-contained HTML report.

## What this is

Health systems have limited budgets for expensive programs, so a model decides **who gets prioritized** — usually by predicting who will "spend the most," because spending is recorded for everyone. That choice has a blind spot: someone in psychological distress who **does not seek care** has near-zero spending, so a spend-trained model calls them low risk and never looks. The need was there; the *label* never looked for it.

This is **label-choice bias** (Obermeyer et al., [2019](https://doi.org/10.1126/science.aax2342)) — an algorithm trained on cost as a proxy for need under-serves people whose need hasn't turned into spending. `riskaudit` measures it, on any model, without retraining.

## The toolkit

`riskaudit` does **not** train models or make predictions. It is an **auditor**: give it scores and an independent need measure, and it quantifies how much need the model leaves behind — weighted, with a row or design-based (VARSTR/PSU) confidence interval. Because it works purely on `scores` + `need` + `weights`, it is **domain- and country-agnostic**: the same functions audit a hospital's readmission model, an insurer's cost model, or a ministry's triage algorithm.

| Function | Question it answers |
|---|---|
| `top_k_capture(scores, need, k, weights)` | Of all real need, what fraction lands in the top-*k* the model prioritizes — vs. the random floor and the oracle ceiling? |
| `reclassification(scores_a, scores_b, k, weights)` | If we switch the label from A to B, **who** enters and leaves the priority list? |
| `label_choice_curve(scores, need, weights, bins)` | Where do the highest-need people sit on the score? |
| `ablation(fit_fn, X, y, feature_groups, need, k, weights)` | Cross-fitted: how much does *global performance* drop vs. how much does *capture of need* collapse when a feature group is removed? |
| `incremental_lift(y_t1, y_pred, distress, scores, k, weights)` | **The contribution metric:** among the deprioritized, do those in need generate *more future outcome than predicted*? Makes the argument non-circular. |
| `regression_to_mean(y_t, y_t1, scores_t, k, weights)` | How much of a top-*k* outcome drop is just regression to the mean? (descriptive) |
| `label_robustness(scores, need, weights, k)` | How wrong the `need` label would have to be to explain away the gap. |
| `group_capture(scores, need, groups, k, weights)` | Capture computed within each subgroup — **whose** need does the score rank worst? |
| `label_blend_frontier(scores_a, scores_b, need, k, weights, groups, alphas)` | Blend two candidate labels α·A+(1−α)·B and trace capture and top-*k* composition across the frontier. |
| `audit_report(results, out_html)` | Bundles everything into a self-contained HTML report. |

## The MEPS example

A worked example on U.S. MEPS 2021–2023 shows the tool finds real bias — a demonstration, not the point. The figure at the top is its headline; the curve below shows *where* the highest-need people land on each model's score.

<p align="center">
  <img src="https://raw.githubusercontent.com/CProromant/risk-equity-audit/main/docs/img/label_choice_curve.png" width="620"
       alt="Label-choice curve: the need-trained model's mean need rises steeply with its score percentile; the spend-trained model's is much shallower.">
</p>

**Findings** (weighted, design-based CIs): the spend model captures only ~15% of top-decile K6 need — barely above the ~10% random floor, far below the ~41% oracle; a need-trained model reaches ~29%. Among the people the spend model deprioritizes, those in distress run up more *total* future cost than it predicted (incremental lift +0.8 log-dollars with the mental-health features, +1.0 without — both 95% CIs exclude zero): the bias comes from the **label, not from missing information**.

**Honest limit.** That excess does **not** appear on non-psychiatric utilization (ER + hospitalizations; lift ≈ 0, CI includes zero), so I do *not* claim the distress surfaces specifically as non-psychiatric spending — the total-spend excess may be partly mental-health spending, and a clean test needs a non-psychiatric spend target (backlog). The severe-untreated subgroup (n ≈ 40) is descriptive only. The figures regenerate from the pipeline with `make figures`.

## Validation

`riskaudit`'s metrics reproduce the canonical label-choice audit — Obermeyer et al. ([2019](https://doi.org/10.1126/science.aax2342)) — on the authors' [public synthetic data](https://gitlab.com/labsysmed/dissecting-bias), using only the public API. Ranking by the deployed cost-score leaves health need behind (top-3% capture of active chronic conditions 0.12 vs. a 0.19 oracle) and captures less of it for Black patients (0.10) than White (0.12); re-ranking by health raises the Black share of the auto-enroll tier (20.0% → 23.3%) and turns over 64% of the list. Directions match the paper; magnitudes are attenuated because the data is synthetic — documented, not tuned away, in [`validation/obermeyer_2019/COVERAGE.md`](validation/obermeyer_2019/COVERAGE.md).

```bash
make validate-obermeyer   # downloads ~18 MB (pinned by SHA-256), prints the table, checks it
```

## Data sources

No data is stored in this repository. Only download scripts and checksums are versioned; everything under `data/` is git-ignored.

- **MEPS (AHRQ, U.S.):** HC-233/243/251 (FYC 2021–2023), **HC-244** (Panel 26 longitudinal), **HC-231** (Conditions) and **HC-229A** (Prescribed Medicines) for the treatment proxy — free, no registration, downloaded with SHA-256 checksums. See [`PROTOCOL.md`](PROTOCOL.md) §3.
- **Synthetic (benchmark):** generated in-script by [`examples/benchmark`](examples/benchmark/) — a controlled example that plants a known bias, no external data, no real patients.

## Limitations

Honesty about limits is a feature of this project, not a footnote:

- **The severe untreated subgroup is small** (~40 in the analytic sample) — reported descriptively with wide CIs, never modeled. The robust finding is the population-level mechanism, not an anecdote about invisible patients.
- **"Need" is a normative choice.** Calling a model "biased" asserts which target is legitimate need; that judgment is stated and defended in [`docs/methods.md`](docs/methods.md), not assumed. `label_robustness` stress-tests it.
- **Survey design is respected throughout** — sample weights and a stratified cluster bootstrap over VARSTR/VARPSU, never unweighted or naïvely filtered.

## Roadmap

`v0.2.0` released (on PyPI, archived on Zenodo). It reproduces the Obermeyer et al. (2019) audit on public data (see [`validation/`](validation/obermeyer_2019/COVERAGE.md)) and adds subgroup capture and the label-blend decision frontier. Next (see [`docs/roadmap-v2.md`](docs/roadmap-v2.md)): cost-of-blindness, worst-off capture, and stability of the priority list. Closed list, one function at a time.

## How to cite

> Proromant, C. (2026). *riskaudit: auditing label-choice bias in healthcare risk-stratification models* [Software]. Zenodo. https://doi.org/10.5281/zenodo.21461268

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff).

The label-choice framing follows Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. *Science*, 366(6464), 447–453. https://doi.org/10.1126/science.aax2342

## License

[MIT](LICENSE) © Conrado — MD (PUC), MSc(c) Data Science (PUC).

---
---

<a name="español"></a>

# risk-equity-audit (español)

**Auditoría del sesgo por elección de etiqueta en modelos de estratificación de riesgo en salud.**

`riskaudit` es una librería en Python que audita *cualquier* modelo de estratificación de riesgo en busca de **sesgo por elección de la etiqueta** — cuánta "necesidad" real deja fuera un modelo cuando se entrena con un proxy cómodo (típicamente el **gasto sanitario**) en lugar de la necesidad misma. Trabaja sobre la salida de cualquier modelo: le das los `scores` que asignó, una medida independiente de `need` (necesidad) y `weights` poblacionales.

<p align="center">
  <img src="https://raw.githubusercontent.com/CProromant/risk-equity-audit/main/docs/img/capture.png" width="720"
       alt="Captura de necesidad medida en el top-decil (MEPS): oráculo 41 por ciento, modelo de necesidad 29 por ciento, modelo de gasto 15 por ciento, piso al azar 10 por ciento.">
</p>

<p align="center"><sub>Salida de la propia <code>riskaudit</code> sobre el ejemplo MEPS: un modelo desplegado entrenado con gasto captura la necesidad apenas por encima del azar — y menos de la mitad de lo que capturaría rankeando por necesidad.</sub></p>

## Instalación

```bash
pip install riskaudit
```

Python ≥ 3.11. El core es liviano; para el ejemplo MEPS: `pip install "riskaudit[meps]"`.

## Quickstart

Audita los puntajes de tu propio modelo en pocas líneas — sin entrenar, sin datos sensibles:

```python
import numpy as np
from riskaudit.audit import top_k_capture

rng = np.random.default_rng(2026)
scores, need, weights = rng.random(5_000), rng.random(5_000), rng.random(5_000)
c = top_k_capture(scores, need, k=0.10, weights=weights)
print(f"captura top-decil: {c.value:.0%}  (piso {c.baseline:.0%}, oráculo {c.oracle:.0%})")
```

Cada resultado trae IC (de filas o de diseño) y se lee contra su **piso** (score al azar) y su **oráculo** (rankear por la propia necesidad) — un número de captura no significa nada sin ellos. `audit_report(results, "audit.html")` empaqueta todo en un informe HTML autocontenido.

## Qué es esto

Los sistemas de salud tienen presupuesto limitado, así que un modelo decide **a quién se prioriza** — normalmente prediciendo quién "va a gastar más", porque el gasto está registrado para todos. Esa elección tiene un punto ciego: alguien con distrés que **no consulta** tiene gasto casi cero, así que un modelo entrenado con gasto lo etiqueta como bajo riesgo y nunca lo mira. La necesidad estaba; la *etiqueta* nunca la buscó.

Esto es el **sesgo por elección de la etiqueta** (Obermeyer et al., [2019](https://doi.org/10.1126/science.aax2342)): un algoritmo entrenado con el costo como proxy de necesidad sub-atiende a quienes su necesidad aún no se tradujo en gasto. `riskaudit` lo mide, sobre cualquier modelo, sin reentrenar.

## La herramienta

`riskaudit` **no** entrena modelos ni predice. Es un **auditor**: le das scores y una medida independiente de necesidad, y cuantifica cuánta necesidad el modelo deja fuera — ponderado, con IC de filas o de diseño (VARSTR/PSU). Como trabaja solo con `scores` + `need` + `weights`, es **agnóstico al dominio y al país**: las mismas funciones auditan el modelo de reingresos de un hospital, el de gasto de una aseguradora o el algoritmo de priorización de un ministerio.

| Función | Pregunta que responde |
|---|---|
| `top_k_capture` | De toda la necesidad real, ¿qué fracción cae en el top-*k* — vs. el piso al azar y el oráculo? |
| `reclassification` | Si cambio la etiqueta de A a B, ¿**quién** entra y sale de la lista de prioridad? |
| `label_choice_curve` | ¿Dónde caen las personas de mayor necesidad en el score? |
| `ablation` | Cross-fitted: ¿cuánto baja el *desempeño global* vs. cuánto se desploma la *captura de necesidad* al quitar un grupo de features? |
| `incremental_lift` | **La métrica-contribución:** entre los deprioritizados, ¿los que tienen necesidad generan *más desenlace futuro del predicho*? Hace no-circular el argumento. |
| `regression_to_mean` | ¿Cuánto de una caída del top-*k* es solo regresión a la media? (descriptivo) |
| `label_robustness` | ¿Cuán equivocada tendría que estar la etiqueta `need` para explicar la brecha? |
| `group_capture` | Captura dentro de cada subgrupo — ¿de *quién* es la necesidad peor rankeada? |
| `label_blend_frontier` | Mezcla dos etiquetas α·A+(1−α)·B y traza captura y composición del top-*k* a lo largo de la frontera. |
| `audit_report` | Empaqueta todo en un informe HTML autocontenido. |

## El ejemplo MEPS

Un ejemplo sobre MEPS 2021–2023 (EE.UU.) muestra que la herramienta encuentra sesgo real — una demostración, no el objetivo. La figura de arriba es el titular; la curva de abajo muestra *dónde* caen las personas de mayor necesidad en el score de cada modelo.

<p align="center">
  <img src="https://raw.githubusercontent.com/CProromant/risk-equity-audit/main/docs/img/label_choice_curve.png" width="620"
       alt="Curva label-choice: la necesidad media del modelo de necesidad sube empinada con su percentil de score; la del modelo de gasto es mucho más superficial.">
</p>

**Hallazgos** (ponderado, IC de diseño): el modelo de gasto captura solo ~15% de la necesidad K6 del top-decil — apenas sobre el ~10% del azar, muy por debajo del ~41% del oráculo; un modelo de K6 llega a ~29%. Entre los deprioritizados por el modelo de gasto, los que están en distrés acumulan más gasto *total* futuro del predicho (lift +0.8 log-dólares con las features de salud mental, +1.0 sin ellas — ambos IC 95% excluyen el cero): el sesgo viene de la **etiqueta, no de falta de información**.

**Límite honesto.** Ese exceso **no** aparece en la utilización no-psiquiátrica (urgencias + hospitalizaciones; lift ≈ 0, IC incluye el cero), así que **no** afirmo que el distrés se manifieste específicamente como gasto no psiquiátrico — un test limpio necesita un target de gasto no-psiquiátrico (backlog). El subgrupo severo no tratado (n ≈ 40) es solo descriptivo.

## Validación

Las métricas de `riskaudit` reproducen la auditoría de label-choice más citada — Obermeyer et al. ([2019](https://doi.org/10.1126/science.aax2342)) — sobre los [datos sintéticos públicos](https://gitlab.com/labsysmed/dissecting-bias) de los autores, usando solo el API público. Rankear por el score de costo desplegado deja fuera la necesidad de salud (captura top-3% de condiciones crónicas 0.12 vs. oráculo 0.19) y captura menos la de pacientes negros (0.10) que blancos (0.12); re-rankear por salud sube su participación en el tramo auto-enroll (20.0% → 23.3%) y rota el 64% de la lista. Las direcciones coinciden con el paper; las magnitudes están atenuadas porque el dato es sintético — documentado, no maquillado, en [`validation/obermeyer_2019/COVERAGE.md`](validation/obermeyer_2019/COVERAGE.md).

```bash
make validate-obermeyer   # baja ~18 MB (fijado por SHA-256), imprime la tabla y la verifica
```

## Limitaciones

La honestidad sobre los límites es parte del proyecto, no una nota al pie:

- **El subgrupo severo no tratado es pequeño** (~40 en la muestra analítica): descriptivo, con IC anchos, nunca se modela. El hallazgo robusto es el mecanismo poblacional, no la anécdota de "los invisibles".
- **"Necesidad" es una elección normativa** — se declara y defiende en [`docs/methods.md`](docs/methods.md); `label_robustness` la somete a estrés.
- **El diseño muestral se respeta siempre:** pesos y bootstrap de clúster estratificado sobre VARSTR/VARPSU, nunca sin ponderar.

## Referencia

El encuadre de *label-choice bias* sigue a Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. *Science*, 366(6464), 447–453. https://doi.org/10.1126/science.aax2342

## Licencia

[MIT](LICENSE) © Conrado — Médico (PUC), MSc(c) Data Science (PUC).
