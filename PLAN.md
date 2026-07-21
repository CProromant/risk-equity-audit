# PLAN DE EJECUCIÓN — `risk-equity-audit`

> **Qué es este documento.** El `PROTOCOLO_risk-equity-audit.md` define *qué* y *por qué* (la especificación vinculante). Este `PLAN.md` define *cómo*, *en qué orden* y *cómo sé que terminé cada cosa*. Es la lista de tareas ejecutable, con "definición de hecho" (DoD) por tarea, comandos concretos y decisiones abiertas a resolver.
>
> **Regla de oro:** cada casilla `[ ]` es verificable de forma objetiva (un comando corre, un test pasa, un archivo existe con tal contenido). No se marca hecho por "creo que está".
>
> **Prioridad ante conflictos (del protocolo):** correcto > reproducible > usable por terceros > bonito.
>
> **Seed global:** `2026`. **Python:** ≥ 3.11.
>
> **Estado (vivo · act. 21-jul-2026).** `v0.1.2` publicado. Las **Fases 0–4 (v0.1) están completas** — son el registro de abajo (secciones FASE 0…5 y el checklist maestro §5). El **plan vivo es la sección `v0.2` al final** de este documento. El spec vinculante de v0.2 está en `PROTOCOL.md §9`; el detalle conceptual en `docs/roadmap-v2.md`.

---

## 0. Cómo se usa este plan

1. Ejecutar **fase por fase**, en orden. No empezar una fase sin cerrar los AC de la anterior (guardrail 8).
2. Al cerrar cada fase: escribir el **resumen de cierre** (qué se hizo, AC en verde, pendientes, decisiones) y **detenerse** para autorización humana antes de la siguiente.
3. Toda desviación respecto del protocolo o de este plan se registra en `docs/decisions.md` con fecha y motivo.
4. Toda variable cruda de MEPS se registra en `dictionary.yml` **antes** de usarse (guardrail 1). Nunca inventar nombres.
5. Los ítems marcados **[DECISIÓN]** requieren que el humano elija antes de avanzar; están reunidos en la sección 2.

---

## 1. Estado y convenciones

- **Nomenclatura de commits:** convencionales, en inglés (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `build:`, `ci:`). Un commit por unidad lógica.
- **Ramas:** trabajo en `main` directo salvo que se pida PR (repo personal). Cada fase puede ir en su propio commit-set.
- **Idioma:** código, docstrings, commits, nombres de archivo → inglés. `README` bilingüe (EN primero). Este `PLAN.md` y `docs/decisions.md` → español (documento de trabajo del autor).
- **Antes de cada commit:** correr `ruff check`, `ruff format`, `pytest`, y revisar que `.gitignore` cubre `data/`, `artifacts/`, `*.dta`, `*.zip`, `*.parquet`.
- **Determinismo:** todo script que use aleatoriedad recibe `seed=2026` desde un único lugar (`riskaudit._config.SEED`).

---

## 2. Decisiones abiertas a resolver [DECISIÓN]

> Estas deben quedar resueltas y registradas en `docs/decisions.md`. Las que afectan el modelado (D2, D3, D4) **bloquean la Fase 2**, no la Fase 0/1. Doy recomendación en cada una.
>
> **Estado (2026-07-18): D1–D5 RESUELTAS** y registradas en `docs/decisions.md` (detalle matemático en `docs/methods.md`). D2=equidad como argumento central; contribución = `incremental_lift`; D3=tuning por target; D4=estimación de dominio; D5=K6 continuo + umbral. **D6: el módulo Chile se descartó por completo** (ver `docs/decisions.md`). Las casillas de abajo quedan como referencia histórica.

- [ ] **D1 — Nombre y ubicación del protocolo.** El protocolo asume llamarse `PROTOCOL.md`; hoy es `PROTOCOLO_risk-equity-audit.md`. **Recomendación:** renombrar a `PROTOCOL.md` y crear `CLAUDE.md` mínimo (ver Fase 0, tarea 0.1). *No bloquea nada, pero conviene cerrarlo primero.*
- [ ] **D2 — El juicio normativo: ¿cuál es el label "correcto"?** Llamar "sesgado" a un modelo exige afirmar cuál es la vara de necesidad legítima. **Recomendación:** el label defendible NO es "K6 en abstracto", sino **gasto/utilización futura del grupo con distrés medido** (la idea: distrés no tratado → gasto no psiquiátrico en t+1). K6 se usa como *definición del grupo* y como uno de los targets de comparación, no como "la verdad" única. Documentar esta postura explícitamente en `docs/methods.md` **antes** de correr la auditoría. *(Deriva de la crítica: sin esto, un revisor marca el argumento como circular.)*
- [ ] **D3 — Hiperparámetros: ¿idénticos o por target?** El protocolo pide HP idénticos para los 3 targets. **Recomendación:** mantener **misma clase de modelo y mismas features** (eso es lo que da comparabilidad), pero **tunear HP ligeramente por target** con la misma rutina de CV. Forzar HP idénticos puede handicapear un target y sesgar la comparación que es el núcleo del trabajo. Si se conserva la regla del protocolo, justificar por qué en `methods.md`. *(Deriva de la crítica.)*
- [ ] **D4 — Estimación de subpoblación (dominio), no filtrar-y-repesar.** Al analizar el subconjunto "panel completo ∩ SAQ ambos años ∩ K6 válido", NO filtrar el dataset y correr el diseño muestral sobre lo filtrado (rompe la varianza). Usar **domain/subpopulation estimation** manteniendo el marco muestral completo. **Recomendación:** fijarlo como método estándar del proyecto en `methods.md`. *(Deriva de la crítica; trampa clásica de MEPS.)*
- [ ] **D5 — "Necesidad" ordinal vs cardinal.** Sumar K6 como "masa de necesidad" en `top_k_capture` trata lo ordinal como cardinal. **Recomendación:** reportar dos operacionalizaciones de necesidad — (a) K6 continuo y (b) umbral K6≥13 (binaria) — como análisis de robustez. Decidir cuál es la principal.
- [x] **D6 — Alcance de v0.1 (resuelta).** El módulo Chile se descartó por completo (no aportaba evidencia al claim central; el producto es la herramienta). Orden de sacrificio si aprieta el tiempo → primero posponer análisis avanzados (backlog), luego el demo Synthea, nunca tocar `riskaudit.audit` ni el estudio MEPS.

---

## 3. Mapa de dependencias entre fases

```
F0 Andamiaje ─┬─> F1 ETL MEPS ──> F2 Modelos+Auditoría ─┐
              │                                          ├─> F4 Release
              └─> F3 Paquete+Demo (audit + Synthea) ─────┘
```

- **F3 (paquete `audit` + demo)** puede empezar en paralelo a F1/F2 porque `riskaudit.audit` se desarrolla y testea con **datos sintéticos de resultado conocido**, sin depender de MEPS. *Recomendación:* desarrollar `audit/` temprano; F2 solo lo *consume*.

---

# FASE 0 — Andamiaje

**Objetivo:** repo instalable, CI verde, tooling de calidad, esqueleto de estructura. Sin lógica de negocio.
**AC de la fase:** `pip install -e ".[dev]"` funciona · `pytest` verde (placeholders) · CI verde en el primer push · pre-commit instalado.

### 0.1 Documentos raíz y decisión D1
- [ ] Renombrar `PROTOCOLO_risk-equity-audit.md` → `PROTOCOL.md` (registrar en `docs/decisions.md`).
- [ ] Crear `CLAUDE.md` mínimo: "Lee y sigue `PROTOCOL.md` y `PLAN.md`. Ejecuta por fases. No avances de fase sin cumplir los AC. Verifica variables MEPS contra codebook antes de usarlas (guardrail 1)."
- [ ] `LICENSE` = MIT (autor: Conrado).
- **DoD:** los tres archivos existen; `PROTOCOL.md` referenciado desde `CLAUDE.md`.

### 0.2 `pyproject.toml` (hatchling, src-layout)
- [ ] Backend `hatchling`; `project.name = "riskaudit"`; `requires-python = ">=3.11"`.
- [ ] Dependencias runtime: `pandas`, `pyarrow`, `numpy`, `scipy`, `pyreadstat`, `lightgbm`, `scikit-learn`, `shap`, `pyyaml`, `requests`, `jinja2` (informe HTML), `matplotlib`. Diseño muestral: `samplics` (o `statsmodels`; decidir en F2, dejar ambos disponibles).
- [ ] `project.optional-dependencies.dev`: `pytest`, `pytest-cov`, `ruff`, `pre-commit`.
- [ ] Config de `ruff` (lint + format), `pytest` (`testpaths=["tests"]`, `--cov=riskaudit.audit`), `coverage` (fail_under solo se activa en F3).
- **DoD:** `pip install -e ".[dev]"` termina sin error en un venv limpio.

### 0.3 Estructura de paquetes (esqueleto)
- [ ] Crear el árbol de la sección 2 del protocolo con `__init__.py` en cada subpaquete y funciones/clases *stub* que hagan `raise NotImplementedError` o retornen tipos vacíos, con firma y docstring ya escritos.
- [ ] `src/riskaudit/_config.py` con `SEED = 2026` y rutas base (`DATA_DIR`, `ARTIFACTS_DIR`) leídas de forma portable (Windows/Linux).
- [ ] `data/` con subcarpetas `raw/ processed/ synthetic/` y un `.gitkeep` en cada una (las carpetas se versionan vacías; el contenido no).
- **DoD:** `python -c "import riskaudit; import riskaudit.audit; import riskaudit.etl"` corre sin error.

### 0.4 `.gitignore`
- [ ] Ignorar `data/`, `artifacts/`, `*.dta`, `*.zip`, `*.parquet`, además de lo estándar Python (`__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `.venv/`), y `desktop.ini`, `Thumbs.db` (entorno Windows/OneDrive).
- [ ] Excepción explícita: NO ignorar `data/checksums.txt` ni los `.gitkeep`.
- **DoD:** `git status` no lista ningún dato/artefacto; `git check-ignore data/raw/foo.dta` responde afirmativo.

### 0.5 `Makefile`
- [ ] Targets: `download`, `etl`, `models`, `audit`, `demo`, `all`, `test`, `lint`, `format`. Cada uno llama a un entrypoint fino en `scripts/`.
- [ ] `all = download etl models audit` (demo aparte). `test = pytest`. En Windows documentar alternativa (`make` vía Git Bash, o un `tasks.ps1` espejo si hace falta — decidir en 0.5).
- **DoD:** `make test` (o equivalente) corre pytest; `make lint` corre ruff.

### 0.6 Pre-commit
- [ ] `.pre-commit-config.yaml` con hooks de `ruff` (lint + format) y chequeos básicos (trailing-whitespace, end-of-file, check-yaml, check-added-large-files con límite bajo para atajar datos).
- [ ] `pre-commit install`.
- **DoD:** un commit de prueba dispara los hooks y pasan.

### 0.7 CI (GitHub Actions)
- [ ] `.github/workflows/ci.yml`: matriz Python **3.11 y 3.12**; pasos = checkout → setup-python → `pip install -e ".[dev]"` → `ruff check` → `ruff format --check` → `pytest`.
- [ ] CI **no** descarga datos MEPS (no hay datos en git). Solo prueba `audit` sintético, utilidades y el demo cuando exista.
- **DoD:** primer push → workflow verde en ambas versiones.

### 0.8 Tests placeholder + README esqueleto
- [ ] `tests/test_smoke.py`: importa el paquete y verifica `SEED == 2026`.
- [ ] `README.md` esqueleto bilingüe con secciones vacías: What / Qué, Install, Quickstart, Findings, Data, Limitations, How to cite.
- **DoD:** `pytest` verde; README con encabezados de ambas lenguas.

### 🔒 Cierre Fase 0
- [ ] Resumen de cierre (guardrail 8) + **detener** para autorización.

---

# FASE 1 — ETL MEPS

**Objetivo:** de los PUFs crudos a dos Parquet limpios y documentados: `panel26.parquet` y `fyc_pooled.parquet`.
**AC de la fase:** N del panel ≈ 5.700 (± documentado) · `dictionary.yml` con referencia de codebook por variable · tests de esquema y rango (edad, gasto ≥ 0, K6 ∈ [0,24]) · script de perfilado en `artifacts/`.

> ⚠️ **Guardrail 1 activo en toda la fase:** ninguna variable cruda se usa sin estar antes en `dictionary.yml` con su referencia de codebook.

### 1.1 `etl/download.py`
- [ ] Descargar los 4 zips a `data/raw/` desde el patrón `https://meps.ahrq.gov/mepsweb/data_files/pufs/{id}/{id}dta.zip`, `{id} ∈ {h233, h243, h244, h251}`.
- [ ] Si un URL da 404: **detenerse**, no adivinar; obtener el enlace desde la página de detalle del PUF y registrar el cambio en `docs/decisions.md`.
- [ ] Calcular checksum SHA-256 en la primera descarga, escribir/verificar contra `data/checksums.txt`. Descomprimir a `data/raw/`.
- **DoD:** los 4 `.dta` presentes; `data/checksums.txt` versionado; re-correr no re-descarga si el checksum coincide.

### 1.2 `etl/dictionary.yml` (verificación de variables)
- [ ] Para cada variable candidata del protocolo §4.1, verificar existencia y nombre exacto en el codebook del año (h244doc, h251doc, h233/h243) o en el Variable Explorer de AHRQ, y registrar: `nombre_estandar → nombre_meps → archivo → sección/página del codebook`.
- [ ] Grupos a cubrir: **IDs/diseño** (`DUPERSID`, `PANEL`, `VARSTR`, `VARPSU`, `LONGWT`, `LSAQWT`, `PERWT*F`, `SAQWT*`), **demografía** (`AGELAST`, `SEX`, `RACETHX`, `REGION*`, `POVCAT*`, `INSCOV*`), **salud mental SAQ** (K6 suma, PHQ-2, ítems), **gasto** (`TOTEXP{yy}`, `TOTSLF{yy}`), **utilización** (`ERTOT{yy}`, `IPDIS{yy}`, `OBTOTV{yy}`, `RXTOT{yy}`), **crónicos** (dx prioritarios), **tratamiento SM**.
- [ ] Toda variable esperada que NO exista en un año → registrar en `docs/decisions.md` y proponer alternativa. No seguir sin resolver.
- **DoD:** `dictionary.yml` completo y comentado; ningún nombre crudo de MEPS aparece fuera de este archivo en el código.

### 1.3 `etl/meps.py` — lectura eficiente
- [ ] Leer `.dta` con `pyreadstat`. Para HC-244 (2.737 variables): leer **metadata primero**, luego solo `usecols` del diccionario (no cargar todo en memoria).
- [ ] Mapear nombres crudos → estándar según `dictionary.yml`. Tipar (categóricas como `category`, pesos como float).
- **DoD:** función que devuelve un DataFrame por archivo con nombres estándar y tipos correctos.

### 1.4 `panel26.parquet` (el archivo central)
- [ ] Desde HC-244: una fila por persona del Panel 26, columnas sufijadas `_t` (2021) y `_t1` (2022).
- [ ] Incluir pesos `LONGWT` y `LSAQWT`, estratos/PSU (`VARSTR`, `VARPSU`).
- [ ] Documentar el N resultante y compararlo con el esperado (~5.700 completers; ~2.900 adultos con K6 ambos años; ~95 con K6≥13; ~45 K6≥13 sin tratamiento). Discrepancias → `docs/decisions.md`.
- **DoD:** Parquet escrito en `data/processed/`; N documentado en el script de perfilado.

### 1.5 `fyc_pooled.parquet`
- [ ] FYC 2021–2023 (HC-233/243/251) apilados con columna `year`; armonizar nombres entre años vía diccionario (los sufijos de variables cambian por año).
- **DoD:** Parquet con `year ∈ {2021,2022,2023}` y esquema consistente entre años.

### 1.6 Tests de esquema y rango
- [ ] `tests/test_etl_schema.py`: columnas esperadas presentes; tipos correctos; claves únicas por `DUPERSID`.
- [ ] `tests/test_etl_ranges.py`: `AGELAST` plausible, `TOTEXP* ≥ 0`, `K6 ∈ [0,24]`, pesos ≥ 0. *(Estos tests corren sobre un fixture sintético mínimo, no sobre MEPS real, para que CI funcione sin datos.)*
- **DoD:** tests verdes en local y CI.

### 1.7 Perfilado
- [ ] `scripts/profile_meps.py`: genera a `artifacts/` un resumen (N por subgrupo, missingness por variable clave, distribución de K6 y de gasto, tabla del subgrupo severo). No versionado (está en `artifacts/`).
- **DoD:** el artefacto se genera; los N clave quedan documentados.

### 🔒 Cierre Fase 1
- [ ] Resumen de cierre + **detener**.

---

# FASE 2 — Modelos + Auditoría MEPS

**Objetivo:** tres modelos comparables, auditoría completa ponderada, informe HTML reproducible.
**AC de la fase:** `make models && make audit` reproduce `metrics.json` y figuras con seed fijo · informe con captura top-decil por target, reclasificación gasto vs K6, ablación, curva label-choice, RTM · todo ponderado · subgrupo severo (n≈45–95) solo descriptivo con IC.

> **Bloqueada hasta resolver D2, D3, D4, D5.**

### 2.1 `features.py` — matriz X_t y los 3 targets
- [ ] `X_t`: todo medido en t=2021 (demografía, crónicos, utilización_t, gasto_t, features de salud mental_t).
- [ ] Etiquetar el grupo de features de salud mental con `feature_group="mental_health"` explícito (la ablación depende de esto).
- [ ] Targets t+1=2022: **T1** `log1p(TOTEXP_t1)` (regresión); **T2** conteo `ER_t1 + hosp_t1` y su binaria `≥1` (reportar ambas); **T3** `K6_t1` continuo (regresión).
- [ ] Flag descriptivo `severe_untreated = (K6_t ≥ 13) & (sin tratamiento SM en t)` — **nunca** target.
- **DoD:** función que devuelve `X_t`, los targets, los pesos y el mapa de `feature_groups`. Tests de construcción con fixture sintético.

### 2.2 `models.py` — entrenamiento comparable
- [ ] Mismo estimador (`LGBMRegressor`/`LGBMClassifier`) y mismas features para los 3 targets. HP según **D3** (recomendado: tuning ligero por target con misma rutina CV 5-fold; congelar).
- [ ] Split 80/20 estratificado por decil de gasto_t, `random_state=SEED`.
- [ ] Persistir en `artifacts/`: modelos, predicciones out-of-fold y de test, `metrics.json`, importancias SHAP.
- **DoD:** `make models` reproduce `metrics.json` bit-a-bit con seed fijo.

### 2.3 `riskaudit.audit` — implementación (si no se hizo ya en F3)
- [ ] Ver Fase 3, tareas 3.1–3.6. En F2 se **consumen** estas funciones; conviene tenerlas ya testeadas.

### 2.4 Auditoría end-to-end sobre MEPS
- [ ] Correr las 6 funciones sobre los scores de los 3 modelos con **pesos siempre** (guardrail 3) y IC por bootstrap ponderado.
- [ ] **Ablación** enfocada en T1/T2 (gasto/utilización): mostrar Δ desempeño global ≈ 0 vs Δ captura del grupo con distrés (evitar leer T3 como "hallazgo": es semi-tautológico porque K6_t predice K6_t1 — documentarlo).
- [ ] **Necesidad** operacionalizada según **D5** (continuo + umbral).
- [ ] **Subgrupo severo** (n≈45–95): solo descriptivo, IC anchos, lenguaje prudente (guardrail 4). No modelar.
- [ ] Varianza por linearización de Taylor sobre **subpoblación (dominio)** según **D4**; documentar método en `docs/methods.md`.
- **DoD:** todos los resultados se generan con pesos e IC; `make audit` es reproducible.

### 2.5 `docs/methods.md`
- [ ] Definición matemática exacta de cada métrica de `audit`.
- [ ] Justificación del juicio normativo (**D2**), del método de varianza/dominio (**D4**), de HP (**D3**).
- **DoD:** cada métrica del informe tiene su definición trazable aquí.

### 2.6 Informe HTML MEPS
- [ ] `audit_report` produce un HTML autocontenido con: captura top-decil por target, tabla reclasificación gasto vs K6, ablación, curva label-choice, RTM, y el bloque descriptivo del subgrupo severo.
- **DoD:** el HTML abre en navegador sin dependencias externas; todas las figuras presentes.

### 🔒 Cierre Fase 2
- [ ] Resumen de cierre + **detener**.

---

# FASE 3 — Paquete `riskaudit.audit` + Demo

**Objetivo:** API pública estable, documentada y testeada al 90%, + demo Synthea sin PHI.
**AC de la fase:** cobertura ≥ 90% en `audit/` · `python demo/run_demo.py` corre limpio en entorno nuevo y produce HTML · README documenta la API con ejemplo mínimo de ~15 líneas.

> Recomendado empezar esta fase **temprano/en paralelo** a F1–F2 (ver §3): la API se desarrolla con datos sintéticos de resultado conocido, sin MEPS.

Para cada función: firma estable, docstring con **definición matemática exacta**, soporte de `weights`, IC por bootstrap ponderado donde aplique, y **test unitario con datos sintéticos de resultado calculado a mano**.

### 3.1 `audit/capture.py` → `top_k_capture(scores, need, k=0.10, weights=None) -> CaptureResult`
- [ ] Fracción (ponderada) de la necesidad real dentro del top-k del score. **DoD:** test con caso a mano donde el resultado es conocido; verifica el path con y sin `weights`.

### 3.2 `audit/reclassification.py` → `reclassification(scores_a, scores_b, k=0.10, weights=None) -> DataFrame`
- [ ] Tabla 2×2 de entrada/salida del top-k al cambiar de target A→B. **DoD:** test con reordenamiento conocido.

### 3.3 `audit/ablation.py` → `ablation(fit_fn, X, y, feature_groups, k=0.10, weights=None) -> AblationResult`
- [ ] Reentrena sin cada grupo; reporta Δ desempeño global vs Δ captura del grupo de interés. **DoD:** test con `fit_fn` de juguete donde quitar un grupo tiene efecto predecible.

### 3.4 `audit/curves.py` → `label_choice_curve(scores, need, weights=None, bins=20) -> CurveResult`
- [ ] Percentil de score vs necesidad observada media (estilo Obermeyer). **DoD:** test de monotonía/valores en datos construidos.

### 3.5 `audit/rtm.py` → `regression_to_mean(y_t, y_t1, scores_t, k=0.10, weights=None) -> RTMResult`
- [ ] Fracción de la caída de gasto del top-k atribuible a RTM. **DoD:** test con proceso simulado de RTM conocido.

### 3.6 `audit/report.py` → `audit_report(results, out_html) -> Path`
- [ ] Informe HTML autocontenido (Jinja2 + figuras embebidas como data-URI). **DoD:** genera un HTML válido a partir de resultados de ejemplo.

### 3.7 Cobertura y API pública
- [ ] `riskaudit.audit.__init__` exporta las 6 funciones y los dataclasses de resultado.
- [ ] Activar `--cov-fail-under=90` para `riskaudit.audit` en pytest/CI.
- **DoD:** `pytest --cov=riskaudit.audit` ≥ 90%.

### 3.8 Demo Synthea (`demo/run_demo.py`, < 10 min)
- [ ] Descargar/usar cacheada la muestra Synthea de ~1.000 pacientes (CSV) a `data/synthetic/`.
- [ ] Construir dataset persona-año con costo simulado y un flag de "necesidad" (p. ej., condición de salud mental sin encuentros).
- [ ] Entrenar un modelo de costo de juguete → correr la auditoría completa → emitir `demo_report.html`.
- [ ] `demo/README.md` dice explícitamente: "esto corre sin datos reales ni PHI; muestra la herramienta funcionando".
- **DoD:** en un venv recién creado, `python demo/run_demo.py` termina en < 10 min y produce el HTML.

### 3.9 README — sección API
- [ ] Ejemplo mínimo (~15 líneas) que importa `riskaudit.audit`, arma scores+need sintéticos y llama a `top_k_capture` + `audit_report`.
- **DoD:** el ejemplo del README corre copiado tal cual.

### 🔒 Cierre Fase 3
- [ ] Resumen de cierre + **detener**.

---

# FASE 4 — Release v0.1.0

**Objetivo:** repo publicable, README bilingüe completo, tag y archivado.
**AC de la fase:** README bilingüe completo (qué es, instalación, quickstart, hallazgos con 2 figuras, datos, limitaciones, cómo citar) · CHANGELOG · tag `v0.1.0` · instrucciones de archivado Zenodo escritas · sección "How to cite".

### 4.1 README bilingüe final
- [ ] EN primero, ES después. Secciones: What it is / Install / Quickstart / **Findings (con 2 figuras clave)** / Data (fuentes y que NO van en git) / **Limitations** (n del subgrupo severo, label choice es un juicio normativo) / How to cite.
- **DoD:** un tercero puede instalar y correr el demo solo con el README.

### 4.2 CHANGELOG y versión
- [ ] `CHANGELOG.md` con la v0.1.0. Versión en `pyproject.toml` = `0.1.0`.
- **DoD:** versión consistente entre changelog, pyproject y tag.

### 4.3 Zenodo + cita
- [ ] Instrucciones de archivado en Zenodo escritas (la cuenta/DOI la conecta el humano). Sección "How to cite" con formato de cita provisional (DOI a completar).
- **DoD:** documentado; nada que requiera credenciales queda a cargo de Claude Code.

### 4.4 Backlog → issues
- [ ] Crear issues de GitHub para el backlog del protocolo §7 (pooling paneles 24–27; two-part/GLM gamma; `fairlearn`; CLI; CMS Synthetic RIF; mkdocs; preprint Quarto).
- **DoD:** issues creados y etiquetados.

### 4.5 Tag y verificación final
- [ ] `make all` reproduce resultados MEPS con seed fijo; CI verde; `.gitignore` confirmado sin datos.
- [ ] Tag `v0.1.0`.
- **DoD:** release listo; checklist de AC de todas las fases en verde.

### 🔒 Cierre Fase 4
- [ ] Resumen final del proyecto.

---

## 4. Registro de riesgos (vivo)

| # | Riesgo | Señal temprana | Mitigación |
|---|---|---|---|
| R1 | Nombres/años de variables MEPS distintos de lo esperado | variable no existe en un año | guardrail 1: verificar en codebook, registrar alternativa en `decisions.md` |
| R2 | Subgrupo severo aún más chico que ~45 | N tras filtros | reforzar "solo descriptivo, IC anchos"; nunca modelar; ajustar narrativa |
| R3 | Varianza mal estimada por filtrar-y-repesar | IC implausiblemente angostos | D4: estimación de dominio con marco completo |
| R4 | Ablación de T3 leída como hallazgo (circular) | AUC de K6_t1 dominado por K6_t | enfocar el claim en T1/T2; documentar la tautología de T3 |
| R5 | Alcance v0.1 se pasa de tiempo | fases atrasadas | D6: sacrificar el demo antes que nada, nunca `audit`/MEPS |
| R6 | Datos filtrados a git | `git status` lista `.dta`/`.parquet` | revisar `.gitignore` antes de cada commit (guardrail 5) |
| R7 | Sobre-afirmar el "encontramos invisibles" | lenguaje causal fuerte con n chico | encuadre: hallazgo = mecanismo poblacional, no anécdota |

## 5. Checklist maestro de AC (una vista)

- [x] F0: `pip install -e ".[dev]"` ok · `pytest` verde · pre-commit activo · CI (confirmar verde en Actions)
- [x] F1: N panel = 6.741 (3.001 adultos K6 ambos años) documentado · `dictionary.yml` verificado · tests esquema/rango · perfilado en `artifacts/`
- [x] F2: `make models && make audit` reproducible · informe HTML con las 7 piezas · todo ponderado · severo solo descriptivo (captura K6 spend 15% vs K6 29%; lift +0.77, IC excluye 0)
- [x] F3: **`audit/` implementado** (7 funciones, cobertura 99%) · demo auto-contenido ✅ · ejemplo de API en README ✅
- [x] F4: README bilingüe · CHANGELOG · `CITATION.cff` · tag `v0.1.0` · Zenodo DOI 10.5281/zenodo.21461268 · (backlog→issues opcional, pendiente)
- [x] Transversal: métrica `incremental_lift` (contribución propia, `methods.md` §2) ✅ · **bootstrap de diseño VARSTR/VARPSU** ✅ (`SurveyDesign`). **(v0.1 completada y publicada.)**

---

# v0.2 — Equidad + validación (plan vivo)

> `v0.1.2` publicado. Este es el plan ejecutable de v0.2. Spec vinculante en `PROTOCOL.md §9`; detalle conceptual en `docs/roadmap-v2.md`. Misma disciplina: fase por fase, DoD objetivo, lista cerrada.

## v0.2 · Fase 0 — Pulcritud (bookkeeping) · antes que nada

Cerrar la deuda de consistencia detectada en la revisión. Barato y desbloquea lo demás.

- [ ] **Versión de fuente única.** Versión dinámica de hatchling (`[tool.hatch.version] path = "src/riskaudit/__init__.py"`, `dynamic = ["version"]`), para que pyproject / `__init__` / test / CITATION no vuelvan a desfasarse. **DoD:** `riskaudit.__version__` == la versión del build; el test lo verifica.
- [ ] **`CITATION.cff` al día** (hoy dice `0.1.0`; el paquete es 0.1.2). **DoD:** versión de CITATION == versión del paquete.
- [ ] **`py.typed`** en `src/riskaudit/`. **DoD:** el marcador se empaqueta en el wheel.
- [ ] **Cerrar hueco de cobertura:** test que renderiza un `RobustnessResult` vía `audit_report`. **DoD:** cobertura de `riskaudit.audit` vuelve a ~99%.
- [ ] **Docs consistentes:** marcar `label_robustness` como entregado en `docs/roadmap-v2.md`; confirmar que ningún doc lo lista como pendiente. **DoD:** grep limpio.
- [ ] **Checklist de release** en uso (ver `PROTOCOL.md §9`): `ruff check . && ruff format --check . && pytest --cov=riskaudit.audit --cov-fail-under=90` antes de cada tag. **DoD:** se corre antes de taggear.

## v0.2 · Fase A — Validación canónica (Obermeyer 2019) · el ancla

Reproducir las métricas de auditoría del caso canónico sobre su sintético público (`gitlab.com/labsysmed/dissecting-bias`), usando **solo el API**. Convierte "confía en el autor" en "verificable". Detalle en `roadmap-v2.md §A`.

- [ ] `validation/obermeyer_2019/download.py` (checksum SHA-256, git-ignored) + `COVERAGE.md` (resultado por resultado: reproducible / parcial / no).
- [ ] `obermeyer_2019.ipynb`: solo API público; tabla paper vs. reproducido vs. delta; 2 figuras con `label_choice_curve` / `reclassification`.
- [ ] Test protegido (`make validate-obermeyer`, activable con `RISKAUDIT_RUN_VALIDATION=1`).
- [ ] Sección "Validation" bilingüe en README (≤10 líneas por idioma).
- **AC:** un tercero corre un comando y ve la tabla de reproducción en <15 min, sin credenciales.
- **Regla dura:** si un resultado no reproduce dentro de tolerancia, se documenta la discrepancia con hipótesis de causa — **no** se ajusta la tolerancia.

## v0.2 · Fase B — Expansión del API (equidad + decisión)

Una función por sesión: investigar → firma + AC → implementar contra el API → tests ~99% → fila en la tabla del README (EN/ES) → integrar en `audit_report`. Toda función reporta IC (filas y diseño) o declara en el docstring por qué no aplica.

- [ ] **`group_capture(scores, need, k, weights, groups)`** — captura por subgrupo con IC de diseño: el eje de equidad ("¿de *quién* es la necesidad omitida?"). **DoD:** test con dominio de subgrupo conocido.
- [ ] **`label_blend_frontier(scores_by_label, need, k, weights, alphas)`** — barre etiquetas compuestas α·A+(1−α)·B; la frontera de trade-off completa. La más citable. **DoD:** test con α=0 y α=1 recuperando los extremos.
- [ ] (backlog v0.2+) `worst_off_capture`, `capture_sweep`, `cost_of_blindness`, `topk_stability`, `need_weighted_nri`, `audit_manifest`.
- *(Ya hechas: `label_robustness` en 0.1.2; `oracle_capture` vive como `baseline`/`oracle` en `CaptureResult`.)*

## v0.2 · Release v0.2.0

- [ ] Bump versión (fuente única) → `0.2.0`; `CHANGELOG.md`; tabla de funciones del README al día.
- [ ] `git tag v0.2.0` → `publish.yml` publica solo.
- **DoD:** `pip install --upgrade riskaudit` == 0.2.0; PyPI muestra el README al día; CI verde.

## Checklist maestro v0.2 (una vista)

- [ ] Fase 0: versión única · `CITATION` al día · `py.typed` · cobertura ~99% · docs consistentes · checklist de release
- [ ] Fase A: validación Obermeyer reproducible en <15 min
- [ ] Fase B: `group_capture` · `label_blend_frontier`
- [ ] Release v0.2.0 publicado · CI verde

---

*Fin del plan (v0.1 completada + v0.2 vivo). Cambios se registran también en `docs/decisions.md`.*
