# risk-equity-audit

**Auditing label-choice bias in healthcare risk-stratification models — and the mental-health blind spot it creates.**

`riskaudit` is a Python toolkit that audits *any* risk-stratification model for **label-choice bias**: the systematic error that appears when a model is trained on the wrong proxy for "need" (typically **healthcare spending**) instead of need itself. The repository pairs the toolkit with a reproducible case study on U.S. MEPS data and a descriptive gap module for Chile.

![status](https://img.shields.io/badge/status-in%20development%20(pre--v0.1.0)-orange)
![python](https://img.shields.io/badge/python-%E2%89%A53.11-blue)
![license](https://img.shields.io/badge/license-MIT-green)

> **Project status.** Active development, working toward release `v0.1.0`. Interfaces and findings below describe the target design; see [Roadmap](#roadmap--hoja-de-ruta) for what is implemented. Everything is being built phase by phase per [`PROTOCOL.md`](PROTOCOL.md) and [`PLAN.md`](PLAN.md).

*(Versión en español más abajo — [ir al español](#español).)*

---

## What this is

Health systems have limited budgets for expensive programs — case management, home visits, close follow-up — so a model decides **who gets prioritized**, usually by predicting who is "high risk." The catch is *how you define* high risk. Most deployed models define it as **"who will spend the most,"** because spending is recorded for everyone.

That choice has a blind spot. Consider someone in psychological distress who **does not seek care**: their observed spending is near zero, so a spend-trained model labels them *low risk* and ignores them — even though untreated distress tends to surface next year as non-psychiatric medical spending (ER visits, worsened physical illness). The need was there; the model was blind to it **by construction**.

This is **label-choice bias**. It is the same mechanism [Obermeyer et al. (2019, *Science*)](https://www.science.org/doi/10.1126/science.aax2342) documented in an algorithm used on millions of U.S. patients, which under-referred Black patients because it used cost as a proxy for need. This project applies that lens to **untreated mental-health need** and packages the audit as a reusable tool.

**Thesis in one sentence:** risk-stratification models trained on healthcare spending are blind *by construction* to people with psychological distress who do not seek care (observed spend = 0), even though that population generates non-psychiatric medical spending the following year — and this project measures it.

---

## What's in the box

1. **`riskaudit`** — an installable Python package that audits label-choice bias in any risk-stratification model. This is the core, reusable artifact; it does not depend on MEPS.
2. **MEPS 2021–2023 case study** — a reproducible pipeline (three targets, identical models, full audit) that demonstrates the thesis on real U.S. survey data.
3. **Chile gap module** — a descriptive triangulation of the mental-health treatment gap (measured symptoms vs. treatment vs. waiting lists vs. medical leave).
4. **End-to-end demo** — runs on synthetic data (Synthea) in under 10 minutes, with **no credentials and no PHI**, so anyone can see the tool working.

---

## The `riskaudit` toolkit

`riskaudit` does **not** train models or make predictions. It is an **auditor**: give it the scores a model assigned and an independent measure of real need, and it quantifies how much need the model leaves behind — with population weights and bootstrap confidence intervals.

| Function | Question it answers |
|---|---|
| `top_k_capture(scores, need, k, weights)` | Of all real need in the population, what fraction lands in the top-*k* the model prioritizes? |
| `reclassification(scores_a, scores_b, k, weights)` | If we switch the label from A to B, **who** enters and leaves the priority list? |
| `ablation(fit_fn, X, y, feature_groups, k, weights)` | If we remove a feature group and retrain, how much does *global performance* drop vs. how much does *capture of that group* collapse? |
| `label_choice_curve(scores, need, weights, bins)` | Obermeyer-style curve: score percentile vs. observed mean need. |
| `regression_to_mean(y_t, y_t1, scores_t, k, weights)` | How much of the top-*k* spending drop from year *t* to *t+1* is just regression to the mean? |
| `audit_report(results, out_html)` | Bundles everything into a self-contained HTML report. |

The headline result the audit is designed to surface: **removing all mental-health features barely changes a spend model's global AUC/R² — yet it collapses the model's capture of measured need.** That contrast, estimated on the whole weighted population, is the argument (not the small severe-untreated subgroup, which is reported descriptively only).

---

## Install

> Requires Python ≥ 3.11. Until the first release is published, install from source:

```bash
git clone https://github.com/<user>/risk-equity-audit.git
cd risk-equity-audit
pip install -e ".[dev]"
```

## Quickstart

Minimal end-to-end audit on your own model's scores:

```python
import numpy as np
from riskaudit.audit import top_k_capture, label_choice_curve, audit_report

rng = np.random.default_rng(2026)
n = 5_000
scores  = rng.random(n)            # what your risk model output per person
need    = rng.random(n)            # an independent measure of real need
weights = rng.random(n)            # survey / population weights

capture = top_k_capture(scores, need, k=0.10, weights=weights)
curve   = label_choice_curve(scores, need, weights=weights, bins=20)

print(f"Top-decile capture of need: {capture.value:.1%}")
audit_report({"capture": capture, "curve": curve}, out_html="audit.html")
```

To see the full pipeline without any real data, run the synthetic demo:

```bash
python demo/run_demo.py   # < 10 min, no PHI, produces demo_report.html
```

---

## Data sources

No data is stored in this repository. Only download scripts and checksums are versioned; everything under `data/` is git-ignored.

- **Core — MEPS (AHRQ, U.S.):** HC-233 (2021), HC-243 (2022), HC-251 (2023), and **HC-244 (Panel 26 Longitudinal 2021–2022)** — free, no registration. See [`PROTOCOL.md`](PROTOCOL.md) §3 for exact files, weights, and codebook references.
- **Chile module:** ENS 2016-17 (MINSAL), ACHS-UC Mental Health Thermometer, GES waiting lists (Glosa 06), DEIS, SUSESO, CASEN 2022 — public aggregates.
- **Synthetic (demo):** [Synthea](https://synthea.mitre.org/) — no real patients.

---

## Limitations

Honesty about limits is a feature of this project, not a footnote:

- **The severe untreated subgroup is small** (≈ 45 people in MEPS). It is reported **descriptively, with wide confidence intervals** — never modeled. The robust finding is the population-level mechanism, not an anecdote about invisible patients.
- **"Need" is a normative choice.** Calling a model "biased" requires asserting which target is the legitimate measure of need. That judgment is stated and defended in `docs/methods.md`, not assumed.
- **The Chile module is descriptive triangulation, not evidence.** No Chilean microdata links measured symptoms to individual spending (there is no "Chilean MEPS"). Chile *motivates* the problem and gives it local policy relevance; it does not validate the MEPS result.
- **Survey design is respected throughout** — final results always use sample weights and design-based variance (subpopulation/domain estimation), never unweighted or naïvely filtered.

---

## Roadmap · Hoja de ruta

Built phase by phase (see [`PLAN.md`](PLAN.md) for task-level detail and acceptance criteria):

- **Phase 0** — Scaffolding: package layout, CI, tooling.
- **Phase 1** — MEPS ETL: verified data dictionary, cleaned panel.
- **Phase 2** — Models + audit on MEPS.
- **Phase 3** — Stable `riskaudit.audit` API (≥ 90% coverage) + Synthea demo.
- **Phase 4** — Chile gap module.
- **Phase 5** — Release `v0.1.0` (bilingual README, CHANGELOG, Zenodo DOI).

## How to cite

A citation with a Zenodo DOI will be added at release. For now, please cite the repository URL and the author.

## License

[MIT](LICENSE) © Conrado — MD (PUC), MSc(c) Data Science (PUC).

---
---

<a name="español"></a>

# risk-equity-audit (español)

**Auditoría del sesgo por elección de etiqueta en modelos de estratificación de riesgo en salud — y el punto ciego de salud mental que produce.**

`riskaudit` es una herramienta en Python que audita *cualquier* modelo de estratificación de riesgo en busca de **sesgo por elección de la etiqueta** (*label-choice bias*): el error sistemático que aparece cuando el modelo se entrena con un proxy equivocado de "necesidad" (típicamente el **gasto sanitario**) en lugar de la necesidad misma. El repositorio acompaña la herramienta con un estudio reproducible sobre datos de MEPS (EE.UU.) y un módulo descriptivo de la brecha en Chile.

> **Estado del proyecto.** En desarrollo activo, avanzando hacia el release `v0.1.0`. Las interfaces y hallazgos que se describen abajo corresponden al diseño objetivo; ver la [hoja de ruta](#roadmap--hoja-de-ruta). Todo se construye por fases según [`PROTOCOL.md`](PROTOCOL.md) y [`PLAN.md`](PLAN.md).

## Qué es esto

Los sistemas de salud tienen presupuesto limitado para programas caros —gestión de caso, visitas domiciliarias, seguimiento cercano— así que un modelo decide **a quién se prioriza**, normalmente prediciendo quién es "de alto riesgo". El problema está en *cómo se define* ese alto riesgo. La mayoría de los modelos desplegados lo definen como **"quién va a gastar más"**, porque el gasto está registrado para todos.

Esa elección tiene un punto ciego. Pensemos en una persona con distrés psíquico que **no consulta**: su gasto observado es casi cero, así que un modelo entrenado con gasto la etiqueta como *bajo riesgo* y la ignora — aunque el distrés no tratado suele reaparecer al año siguiente como gasto médico no psiquiátrico (urgencias, enfermedades físicas agravadas). La necesidad estaba; el modelo fue ciego a ella **por construcción**.

Esto es el **sesgo por elección de la etiqueta**. Es el mismo mecanismo que [Obermeyer et al. (2019, *Science*)](https://www.science.org/doi/10.1126/science.aax2342) documentaron en un algoritmo usado en millones de pacientes en EE.UU., que sub-derivaba a pacientes negros por usar el costo como proxy de necesidad. Este proyecto aplica esa mirada a la **necesidad de salud mental no tratada** y empaqueta la auditoría como herramienta reutilizable.

**Tesis en una frase:** los modelos de estratificación de riesgo entrenados con gasto sanitario son ciegos *por construcción* a las personas con distrés psíquico que no consultan (gasto observado = 0), aunque esa población genera gasto médico no psiquiátrico al año siguiente — y este proyecto lo mide.

## Qué incluye

1. **`riskaudit`** — paquete Python instalable que audita el sesgo por elección de etiqueta en cualquier modelo de estratificación de riesgo. Es el núcleo reutilizable; no depende de MEPS.
2. **Estudio MEPS 2021–2023** — pipeline reproducible (tres targets, modelos idénticos, auditoría completa) que demuestra la tesis con datos reales de EE.UU.
3. **Módulo Chile** — triangulación descriptiva de la brecha de tratamiento en salud mental (síntomas medidos vs. tratamiento vs. listas de espera vs. licencias médicas).
4. **Demo end-to-end** — corre sobre datos sintéticos (Synthea) en menos de 10 minutos, **sin credenciales ni datos sensibles**.

## La herramienta `riskaudit`

`riskaudit` **no** entrena modelos ni predice. Es un **auditor**: le das los puntajes que asignó un modelo y una medida independiente de necesidad real, y cuantifica cuánta necesidad el modelo deja fuera — con pesos poblacionales e intervalos de confianza por bootstrap.

| Función | Pregunta que responde |
|---|---|
| `top_k_capture` | De toda la necesidad real de la población, ¿qué fracción cae en el top-*k* que prioriza el modelo? |
| `reclassification` | Si cambio la etiqueta de A a B, ¿**quién** entra y sale de la lista de prioridad? |
| `ablation` | Si quito un grupo de features y reentreno, ¿cuánto baja el *desempeño global* vs. cuánto se desploma la *captura* de ese grupo? |
| `label_choice_curve` | Curva estilo Obermeyer: percentil de score vs. necesidad observada media. |
| `regression_to_mean` | ¿Cuánto de la caída de gasto del top-*k* entre *t* y *t+1* es solo regresión a la media? |
| `audit_report` | Empaqueta todo en un informe HTML autocontenido. |

El resultado central que la auditoría busca revelar: **quitar todas las features de salud mental casi no cambia el AUC/R² global de un modelo de gasto — pero hunde la captura de la necesidad medida.** Ese contraste, estimado sobre toda la población ponderada, es el argumento (no el pequeño subgrupo severo no tratado, que se reporta solo descriptivamente).

## Instalación y quickstart

Igual que en la sección en inglés (Python ≥ 3.11, `pip install -e ".[dev]"`). El ejemplo mínimo de la API y el demo (`python demo/run_demo.py`) están arriba.

## Limitaciones

La honestidad sobre los límites es parte del proyecto, no una nota al pie:

- **El subgrupo severo no tratado es pequeño** (≈ 45 personas en MEPS): se reporta **descriptivamente, con IC anchos**, nunca se modela. El hallazgo robusto es el mecanismo poblacional, no la anécdota de "los invisibles".
- **"Necesidad" es una elección normativa.** Llamar "sesgado" a un modelo exige afirmar cuál es la vara legítima de necesidad. Ese juicio se declara y defiende en `docs/methods.md`.
- **El módulo Chile es triangulación descriptiva, no evidencia.** No hay microdato chileno que vincule síntomas medidos con gasto individual (no existe un "MEPS chileno"). Chile *motiva* el problema y le da relevancia local; no valida el resultado de MEPS.
- **El diseño muestral se respeta siempre:** los resultados finales usan pesos y varianza basada en el diseño (estimación de subpoblación/dominio).

## Licencia

[MIT](LICENSE) © Conrado — Médico (PUC), MSc(c) Data Science (PUC).
