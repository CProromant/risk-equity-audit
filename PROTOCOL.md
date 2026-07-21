# PROTOCOLO DE EJECUCIÓN — `risk-equity-audit`

**Documento de instrucciones para Claude Code.** Leer completo antes de escribir cualquier línea de código. Contiene: contexto, decisiones ya tomadas (no re-discutir), arquitectura, fuentes de datos verificadas, especificación de módulos, fases con criterios de aceptación y guardrails.

- Fuentes verificadas el: **17-jul-2026**
- Autor del proyecto: Conrado — MD (PUC), MSc(c) Data Science (PUC)
- Cómo usar este documento: guardarlo como `PROTOCOL.md` en la raíz de una carpeta vacía, crear un `CLAUDE.md` mínimo que diga "Lee y sigue PROTOCOL.md; ejecuta por fases; no avances de fase sin cumplir los criterios de aceptación", y arrancar Claude Code ahí con el prompt de la sección 8. Docs oficiales de Claude Code: https://docs.claude.com/en/docs/claude-code/overview

> **Estado (vivo · act. 21-jul-2026).** `v0.1.2` **publicado** (PyPI + Zenodo DOI). **El producto es la librería `riskaudit`** (10 funciones públicas; 8 en el último release v0.1.2); MEPS y el demo son *ejemplos*. Las secciones **§0–§8 son el registro del build v0.1**, ya ejecutado y entregado — se conservan como historia, no como pendientes. El **spec vivo de v0.2 es la §9** (abajo); su ejecución paso a paso vive en `PLAN.md`. Las decisiones fijas (§1 y §9) no se re-discuten.

---

## 0. Qué es esto y por qué existe

**La idea en una frase:** los modelos de estratificación de riesgo entrenados con gasto sanitario son ciegos *por construcción* a las personas con distrés psíquico que no consultan (gasto observado = 0), aunque esa población genera gasto médico no psiquiátrico al año siguiente. Este proyecto lo mide con MEPS y empaqueta la auditoría como herramienta reutilizable.

**Producto final (release v0.1.0):**
1. Paquete Python instalable **`riskaudit`**: auditoría de sesgo por elección de etiqueta (label-choice bias, estilo Obermeyer et al. 2019) aplicable a cualquier modelo de estratificación de riesgo.
2. Pipeline reproducible **MEPS 2021–2023** que implementa la idea: tres targets, modelos idénticos, auditoría completa.
3. **Demo end-to-end** sobre datos sintéticos (Synthea), ejecutable en <10 minutos, sin credenciales ni PHI.
4. Repo público con CI verde, README bilingüe (EN primero, ES después), DOI de Zenodo en el release.

**Usos del repo (contexto para resolver trade-offs):** proyecto personal / portafolio para cargos de gestión poblacional / RWE; trabajo público para afiliación ML Collective; base de un posible preprint. Prioridad ante cualquier conflicto: **correcto > reproducible > usable por terceros > bonito**.

---

## 1. Decisiones técnicas fijas (no re-discutir)

| Tema | Decisión |
|---|---|
| Lenguaje | Python ≥ 3.11 |
| Layout | `src/` layout, `pyproject.toml` (backend: hatchling) |
| Nombres | repo `risk-equity-audit`, paquete `riskaudit` |
| Datos | pandas + pyarrow; intermedios en Parquet bajo `data/processed/` |
| Lectura de PUFs | descargar formato Stata (`.dta`) y leer con `pyreadstat` |
| ML | LightGBM (API sklearn); scikit-learn para CV y calibración |
| Explicabilidad | `shap` |
| Diseño muestral | pesos SIEMPRE en resultados finales (`LONGWT`, `LSAQWT`, `PERWT*`, `SAQWT*`); varianza basada en el diseño sobre VARSTR/VARPSU (bootstrap de diseño —remuestreo de PSU dentro de estratos— o linearización de Taylor); método documentado en `docs/methods.md` |
| Tests | pytest; cobertura mínima de `riskaudit.audit`: 90% |
| Calidad | ruff (lint + format) + pre-commit |
| CI | GitHub Actions: lint + tests en Python 3.11 y 3.12 |
| Licencia | MIT |
| Idiomas | código, docstrings, commits: inglés. README bilingüe |
| Datos en git | **PROHIBIDO**. Todo `data/` en `.gitignore`; se versionan solo scripts de descarga y checksums (`data/checksums.txt`) |
| Determinismo | seed global = 2026; resultados finales reproducibles con `make all` |

---

## 2. Estructura del repositorio

```
risk-equity-audit/
├── CLAUDE.md
├── PROTOCOL.md                # este documento
├── README.md                  # bilingüe: EN, luego ES
├── LICENSE
├── pyproject.toml
├── Makefile                   # download / etl / models / audit / demo / all / test
├── .gitignore                 # data/, artifacts/, *.dta, *.zip, *.parquet
├── .github/workflows/ci.yml
├── src/riskaudit/
│   ├── __init__.py
│   ├── etl/
│   │   ├── download.py        # descarga MEPS con verificación de checksum
│   │   ├── meps.py            # lectura, renombrado, panel t→t+1
│   │   └── dictionary.yml     # variable → archivo → página del codebook (VERIFICADO)
│   ├── features.py            # matriz X_t y los tres targets t+1
│   ├── models.py              # entrenamiento idéntico por target
│   └── audit/                 # ← EL PAQUETE PÚBLICO
│       ├── capture.py
│       ├── reclassification.py
│       ├── ablation.py
│       ├── curves.py          # label_choice_curve
│       ├── lift.py            # incremental_lift (métrica-contribución)
│       ├── rtm.py             # regresión a la media
│       └── report.py          # informe HTML autocontenido
├── scripts/                   # entrypoints finos que llaman al paquete
├── demo/
│   ├── run_demo.py            # Synthea → modelo de costo → auditoría → HTML
│   └── README.md
├── tests/
├── docs/
│   ├── methods.md             # definiciones matemáticas y decisiones estadísticas
│   └── decisions.md           # registro de desviaciones respecto a este protocolo
├── data/                      # NO versionado
│   ├── raw/ processed/ synthetic/
└── artifacts/                 # modelos, predicciones, figuras (NO versionado)
```

---

## 3. Fuentes de datos (verificadas 17-jul-2026)

### 3.1 Núcleo — MEPS (AHRQ, EE.UU.). Descarga libre, sin registro.

| Archivo | Contenido | Documentación |
|---|---|---|
| **HC-233** | Full-Year Consolidated 2021: gasto, utilización, SAQ (K6, PHQ-2) | https://meps.ahrq.gov/data_stats/download_data/pufs/h233/h233doc.shtml |
| **HC-243** | Full-Year Consolidated 2022 | https://meps.ahrq.gov/data_stats/download_data/pufs/h243/h243doc.pdf |
| **HC-251** | Full-Year Consolidated 2023 (publicado ago-2025) | https://meps.ahrq.gov/data_stats/download_data/pufs/h251/h251doc.shtml |
| **HC-244** | **Panel 26 Longitudinal 2021–2022** (2.737 variables; el archivo central del estudio MEPS; incluye `LONGWT` y el peso longitudinal del SAQ `LSAQWT`) | https://www.meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h244/h244doc.pdf |
| **HC-231** | 2021 Medical Conditions (`ICD10CDX`, `CCSR1X-3X`); define el proxy de tratamiento de salud mental | https://meps.ahrq.gov/data_stats/download_data/pufs/h231/h231doc.shtml |
| **HC-229A** | 2021 Prescribed Medicines (clase terapéutica Multum `TC1*`); psicofármacos para el proxy de tratamiento | https://meps.ahrq.gov/data_stats/download_data/pufs/h229a/h229adoc.shtml |

- Patrón de descarga de datos (formato Stata): `https://meps.ahrq.gov/mepsweb/data_files/pufs/{id}/{id}dta.zip` con `{id}` ∈ {h233, h243, h244, h251}. **Si un URL da 404, obtener el enlace desde la página de detalle del PUF; no adivinar.**
- Código de ejemplo oficial (R/SAS/Stata, incluye cómo cargar cada archivo): https://github.com/HHS-AHRQ/MEPS — usarlo como referencia de lectura y de nombres de variables.
- Explorador de variables: https://datatools.ahrq.gov/meps-hc#varExp
- Contexto de tamaño muestral (ya calculado en la fase de diseño): completan las 5 rondas del panel ≈ 5.700 personas; adultos con K6 en ambos años ≈ 2.900; K6 ≥ 13 ≈ 95; K6 ≥ 13 sin tratamiento ≈ 45. **Consecuencia de diseño (fija): el subgrupo severo se analiza descriptivamente, no se modela.** El target de salud mental es K6 continuo.

### 3.2 Sintéticos (para el demo)

| Fuente | Uso | Acceso |
|---|---|---|
| **Synthea** (MITRE) | Cohorte sintética CSV para el demo (muestra de 1.000 pacientes basta) | Descargas: https://synthea.mitre.org/downloads · Generador: https://github.com/synthetichealth/synthea |
| **CMS Synthetic Medicare** (opcional, backlog) | Claims sintéticos formato RIF | https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event |

---

## 4. Especificación de módulos

### 4.1 `riskaudit.etl`

Tareas:
1. `download.py`: descarga los 4 zips MEPS a `data/raw/`, verifica checksum (calcular en la primera descarga y fijar en `data/checksums.txt`), descomprime.
2. `meps.py`: lee los `.dta`, aplica el diccionario, construye dos artefactos Parquet:
   - `panel26.parquet`: una fila por persona del Panel 26 con columnas `_t` (2021) y `_t1` (2022), desde HC-244.
   - `fyc_pooled.parquet`: FYC 2021–2023 apilados con columna `year` (para descriptivos y análisis de sensibilidad).
3. `dictionary.yml`: mapa `nombre_estandar → nombre_meps → archivo → sección del codebook`. Es el único lugar donde viven nombres crudos de MEPS.

**Variables candidatas** (verificar TODAS contra el codebook antes de usar; regla en sección 6):
- ID y diseño: `DUPERSID`, `PANEL`, `VARSTR`, `VARPSU`, `LONGWT`, `LSAQWT`, `PERWT21F/22F/23F`, `SAQWT*`
- Demografía: `AGELAST`, `SEX`, `RACETHX`, `REGION*`, `POVCAT*`, `INSCOV*`
- Salud mental (SAQ): suma K6 (`K6SUM42` o equivalente del año), PHQ-2 (`PHQ242` o equivalente), ítems individuales si están
- Gasto: `TOTEXP{yy}`, `TOTSLF{yy}`; componentes por tipo de evento si se necesitan
- Utilización: visitas de urgencia (`ERTOT{yy}`), hospitalizaciones (`IPDIS{yy}`), consultas (`OBTOTV{yy}`), recetas (`RXTOT{yy}`)
- Carga crónica: variables DX de condiciones prioritarias (hipertensión, diabetes, cardiopatía, asma, artritis, cáncer, ACV, colesterol) según el codebook del año
- Tratamiento de salud mental (para definir "sin tratamiento"): utilización/gasto en salud mental según archivos de condiciones o variables del FYC; definir operacionalización exacta en `docs/methods.md` tras leer el codebook

### 4.2 `riskaudit.features`

Matriz `X_t` (todo medido en t=2021) + tres targets en t+1=2022:
- **T1 — gasto**: `log1p(TOTEXP_t1)`. Regresión. (Two-part model: backlog.)
- **T2 — utilización evitable**: conteo `ER_t1 + hospitalizaciones_t1`; versión binaria `≥1` para clasificación. Reportar ambas.
- **T3 — necesidad**: `K6_t1` continuo. Regresión.
- El grupo `K6_t ≥ 13 & sin tratamiento en t` se construye como **flag descriptivo**, nunca como target.
- Los features de salud mental (K6_t, PHQ2_t, dx/tratamiento SM en t) van en un `feature_group="mental_health"` explícito: la ablación depende de ese etiquetado.

### 4.3 `riskaudit.models`

- Mismo estimador (LGBMRegressor / LGBMClassifier) y **mismas features** para los tres targets (eso da la comparabilidad); **HP tuneados ligeramente por target** con la misma rutina CV 5-fold, luego congelados. (D3 resuelta; ver `docs/decisions.md` y `docs/methods.md` §4.)
- Split: aleatorio 80/20 estratificado por decil de gasto_t (la validación temporal ya está implícita en el diseño features t → outcome t+1).
- Persistir en `artifacts/`: modelos, predicciones out-of-fold y de test, métricas (`metrics.json`), importancias SHAP.

### 4.4 `riskaudit.audit` — API pública v0.1

```python
top_k_capture(scores, need, k=0.10, weights=None) -> CaptureResult
# ¿Qué fracción (ponderada) de la necesidad real cae en el top-k del score?

reclassification(scores_a, scores_b, k=0.10, weights=None) -> pd.DataFrame
# Tabla 2x2: quién entra/sale del top-k al cambiar de target A a B.

ablation(fit_fn, X, y, feature_groups, k=0.10, weights=None) -> AblationResult
# Re-entrena sin cada grupo de features; reporta Δ performance global vs Δ captura del grupo de interés.
# El hallazgo esperado: quitar salud mental casi no mueve el AUC/R2 global pero hunde la captura.

label_choice_curve(scores, need, weights=None, bins=20) -> CurveResult
# Curva estilo Obermeyer: percentil de score vs necesidad observada media.

regression_to_mean(y_t, y_t1, scores_t, k=0.10, weights=None) -> RTMResult
# Qué fracción de la caída de gasto del top-k entre t y t+1 es atribuible a RTM.

incremental_lift(y_t1, y_pred, distress, scores, k=0.10, weights=None) -> LiftResult
# Contribución propia (no-Obermeyer): entre los deprioritizados (fuera del top-k),
# diferencia ponderada del residual del desenlace futuro entre personas con y sin
# distrés. Hace no-circular el argumento de equidad (methods.md §2).

audit_report(results, out_html) -> Path
# Informe HTML autocontenido con todas las figuras y tablas.
```

Requisitos: docstring con definición matemática exacta de cada métrica; soporte de `weights` en todas; tests unitarios con datos sintéticos de resultado conocido a mano; IC por bootstrap donde aplique —de diseño (remuestreo de PSU dentro de estratos VARSTR/VARPSU) en los resultados MEPS.

### 4.5 `demo/`

Guion de `run_demo.py`, ejecutable end-to-end en <10 min:
1. Descarga (o usa cacheada) la muestra Synthea de 1.000 pacientes en CSV.
2. Construye un dataset persona-año con costo simulado y un flag de "necesidad" (p. ej., condición de salud mental sin encuentros).
3. Entrena un modelo de costo de juguete.
4. Corre la auditoría completa de `riskaudit.audit` y emite `demo_report.html`.
Propósito: que un tercero (un jefe de gestión poblacional, por ejemplo) vea la herramienta funcionando sin acceso a datos reales. El README del demo lo dice explícitamente.

---

## 5. Fases y criterios de aceptación (AC)

**Fase 0 — Andamiaje (½ día).** Estructura completa, `pyproject.toml`, CI, pre-commit, Makefile, README esqueleto.
AC: `pip install -e ".[dev]"` funciona; `pytest` verde (con tests placeholder); CI verde en el primer push.

**Fase 1 — ETL MEPS (3–4 días).** Descarga, diccionario verificado, `panel26.parquet` y `fyc_pooled.parquet`.
AC: N del panel ≈ 5.700 ± razonable y documentado; `dictionary.yml` con referencia de codebook por variable; tests de esquema y de rangos (edades, gastos ≥ 0, K6 ∈ [0,24]); notebook/script de perfilado en `artifacts/`.

**Fase 2 — Modelos + auditoría MEPS (4–5 días).** Tres modelos idénticos, auditoría completa, informe.
AC: `make models && make audit` reproduce `metrics.json` y las figuras con seed fijo; el informe HTML contiene: captura top-decil por target, tabla de reclasificación gasto vs K6, ablación, curva label-choice, RTM; todo ponderado; grupo severo (n≈45–95) reportado solo descriptivamente con IC.

**Fase 3 — Paquete + demo (3–4 días).** API `riskaudit.audit` estable, docstrings, demo Synthea.
AC: cobertura ≥90% en `audit/`; `python demo/run_demo.py` corre limpio en un entorno recién creado y produce el HTML; README documenta la API con un ejemplo mínimo de 15 líneas.

**Fase 4 — Release (1–2 días).**
AC: README bilingüe completo (qué es, instalación, quickstart, hallazgos con 2 figuras, datos, limitaciones, cita); CHANGELOG; tag `v0.1.0`; instrucciones de archivado en Zenodo escritas (la cuenta la conecta el humano); sección "How to cite".

---

## 6. Guardrails para Claude Code

1. **Nombres de variables MEPS: nunca inventar.** Flujo obligatorio: buscar la variable en la documentación descargada (h244doc, h251doc) o en el Variable Explorer → registrarla en `dictionary.yml` con su referencia → recién entonces usarla. Si una variable esperada no existe en el año, detenerse, anotar en `docs/decisions.md` y proponer alternativa.
2. **Si los datos contradicen el plan** (tamaños muestrales, distribuciones, missingness), no forzar: documentar en `docs/decisions.md`, proponer ajuste y seguir. La honestidad estadística es un feature del proyecto.
3. **Pesos y varianza siempre** en resultados finales. Está permitido explorar sin pesos, prohibido reportar sin pesos.
4. **No sobre-afirmar con n chico**: el grupo severo lleva IC anchos y lenguaje descriptivo.
5. **Nada de datos en git**: ni microdatos, ni parquets, ni zips. Revisar `.gitignore` antes de cada commit.
6. **Sitios que bloquean o con formato caótico**: descargas simples con `requests`; si un sitio bloquea o el formato es caótico, pedir descarga manual al humano en vez de scraping agresivo.
7. **Commits convencionales** en inglés (`feat:`, `fix:`, `docs:`, `test:`); commits pequeños por unidad lógica.
8. **Al cerrar cada fase**: resumen de lo hecho, AC cumplidos, pendientes y decisiones tomadas. No avanzar de fase con AC en rojo.
9. **Volumen**: los archivos MEPS son de decenas de MB; procesar en memoria con pandas está bien; no introducir Spark/Dask.

---

## 7. Backlog explícito (NO hacer en v0.1)

Pooling de paneles 24–27; two-part models / GLM gamma para gasto; integración con `fairlearn`; CLI (`riskaudit audit ...`); conversión del demo a CMS Synthetic RIF; sitio de docs (mkdocs); manuscrito/preprint en Quarto. Anotarlos como issues de GitHub al final de la Fase 4.

---

## 8. Prompt inicial sugerido para Claude Code

> Lee PROTOCOL.md completo. Es la especificación del proyecto y sus decisiones son vinculantes. Ejecuta la Fase 0 (andamiaje) exactamente como la define la sección 5, respetando la estructura de la sección 2 y las decisiones de la sección 1. Cuando los criterios de aceptación de la Fase 0 estén verdes, muéstrame el resumen de cierre de fase (guardrail 8) y detente para que revise antes de autorizar la Fase 1.

Después, autorizar fase por fase. Para la Fase 1, recordarle el guardrail 1 (verificación de variables contra codebook) en el prompt de arranque.

---

## 9. v0.2 — alcance vinculante (vivo)

`v0.1.2` está publicado; el build v0.1 (§0–§8) está entregado. Esta sección extiende el spec hacia v0.2 sin re-discutir lo anterior.

**Producto y API.** El producto es la librería `riskaudit`. API pública actual (**10 funciones**): `top_k_capture`, `reclassification`, `label_choice_curve`, `ablation`, `regression_to_mean`, `incremental_lift`, `label_robustness`, `group_capture`, `label_blend_frontier`, `audit_report` — más `SurveyDesign` y los dataclasses de resultado. (Las 8 primeras salieron en v0.1.2; `group_capture` y `label_blend_frontier` son la Fase B, aún sin release.) MEPS y el demo son ejemplos, no el producto.

**Decisiones fijas nuevas (no re-discutir):**

| Tema | Decisión |
|---|---|
| Versión | **Fuente única** — hatchling dynamic desde `src/riskaudit/__init__.py`; nunca duplicar la versión a mano (pyproject/CITATION/test la leen o la verifican). |
| Release | **Checklist obligatorio antes de cada tag:** `ruff check . && ruff format --check . && pytest --cov=riskaudit.audit --cov-fail-under=90`. El tag `v*` dispara `publish.yml` (PyPI). |
| API | **Lista cerrada** — ninguna función nueva fuera de la planificada (`docs/roadmap-v2.md`) sin al menos un usuario externo que la pida. El riesgo dominante es la dispersión de un autor solo. |
| Tipos | `py.typed` en el paquete, para exponer los type hints a quien instale. |

**Alcance v0.2** (detalle conceptual en `docs/roadmap-v2.md`, ejecución en `PLAN.md`):

1. **Fase 0 — pulcritud/bookkeeping** (antes que nada): versión de fuente única, `CITATION.cff` al día, `py.typed`, cerrar el hueco de cobertura de `RobustnessResult`, docs consistentes.
2. **Fase A — validación Obermeyer 2019** sobre su sintético público, usando solo el API: el ancla de credibilidad ("verificable", no "confía en el autor"). **Regla dura:** una discrepancia se documenta con hipótesis de causa; no se ajusta la tolerancia.
3. **Fase B — expansión:** `group_capture` (equidad por subgrupo) y `label_blend_frontier` (frontera de reetiquetado α·A+(1−α)·B). `label_robustness` ya se entregó en 0.1.2; `oracle_capture` ya vive como `baseline`/`oracle` en `CaptureResult`.

Del **backlog §7** (fairlearn, CLI, mkdocs, preprint) nada entra en v0.2: sigue diferido. v0.2 es solo validación + equidad.

**Guardrails que siguen vigentes:** pesos y varianza de diseño siempre (guardrail 3); honestidad sobre límites (el nulo no-psiquiátrico se reporta, no se esconde); nombres MEPS verificados contra codebook (guardrail 1); nada de datos en git (guardrail 5); cobertura de `riskaudit.audit` ≥ 90%.
