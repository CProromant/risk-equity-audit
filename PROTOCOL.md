# PROTOCOLO DE EJECUCIÓN — `risk-equity-audit`

**Documento de instrucciones para Claude Code.** Leer completo antes de escribir cualquier línea de código. Contiene: contexto, decisiones ya tomadas (no re-discutir), arquitectura, fuentes de datos verificadas, especificación de módulos, fases con criterios de aceptación y guardrails.

- Fuentes verificadas el: **17-jul-2026**
- Autor del proyecto: Conrado — MD (PUC), MSc(c) Data Science (PUC)
- Cómo usar este documento: guardarlo como `PROTOCOL.md` en la raíz de una carpeta vacía, crear un `CLAUDE.md` mínimo que diga "Lee y sigue PROTOCOL.md; ejecuta por fases; no avances de fase sin cumplir los criterios de aceptación", y arrancar Claude Code ahí con el prompt de la sección 8. Docs oficiales de Claude Code: https://docs.claude.com/en/docs/claude-code/overview

---

## 0. Qué es esto y por qué existe

**Tesis en una frase:** los modelos de estratificación de riesgo entrenados con gasto sanitario son ciegos *por construcción* a las personas con distrés psíquico que no consultan (gasto observado = 0), aunque esa población genera gasto médico no psiquiátrico al año siguiente. Este proyecto lo mide con MEPS y empaqueta la auditoría como herramienta reutilizable.

**Producto final (release v0.1.0):**
1. Paquete Python instalable **`riskaudit`**: auditoría de sesgo por elección de etiqueta (label-choice bias, estilo Obermeyer et al. 2019) aplicable a cualquier modelo de estratificación de riesgo.
2. Pipeline reproducible **MEPS 2021–2023** que implementa la tesis: tres targets, modelos idénticos, auditoría completa.
3. **Módulo Chile**: triangulación descriptiva de la brecha (síntomas medidos vs tratamiento vs listas de espera vs licencias médicas).
4. **Demo end-to-end** sobre datos sintéticos (Synthea), ejecutable en <10 minutos, sin credenciales ni PHI.
5. Repo público con CI verde, README bilingüe (EN primero, ES después), DOI de Zenodo en el release.

**Usos del repo (contexto para resolver trade-offs):** tesis de magíster reproducible; portafolio para cargos de gestión poblacional / RWE; trabajo público para afiliación ML Collective; base del preprint. Prioridad ante cualquier conflicto: **correcto > reproducible > usable por terceros > bonito**.

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
| Diseño muestral | pesos SIEMPRE en resultados finales (`LONGWT`, `LSAQWT`, `PERWT*`, `SAQWT*`); varianza con VARSTR/VARPSU (linearización de Taylor vía `samplics` o `statsmodels`; documentar el método en `docs/methods.md`) |
| Tests | pytest; cobertura mínima de `riskaudit.audit`: 90% |
| Calidad | ruff (lint + format) + pre-commit |
| CI | GitHub Actions: lint + tests en Python 3.11 y 3.12 |
| Licencia | MIT |
| Idiomas | código, docstrings, commits: inglés. README bilingüe. Informes del módulo Chile: español |
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
├── Makefile                   # download / etl / models / audit / chile / demo / all / test
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
│   ├── audit/                 # ← EL PAQUETE PÚBLICO
│   │   ├── capture.py
│   │   ├── reclassification.py
│   │   ├── ablation.py
│   │   ├── curves.py          # label_choice_curve estilo Obermeyer
│   │   ├── rtm.py             # regresión a la media
│   │   └── report.py          # informe HTML autocontenido
│   └── chile/
│       ├── parsers.py         # Glosa 06, DEIS, SUSESO, ENS, Termómetro
│       └── figures.py
├── scripts/                   # entrypoints finos que llaman al paquete
├── demo/
│   ├── run_demo.py            # Synthea → modelo de costo → auditoría → HTML
│   └── README.md
├── tests/
├── docs/
│   ├── methods.md             # definiciones matemáticas y decisiones estadísticas
│   └── decisions.md           # registro de desviaciones respecto a este protocolo
├── data/                      # NO versionado
│   ├── raw/ processed/ chile/ synthetic/
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
| **HC-244** | **Panel 26 Longitudinal 2021–2022** (2.737 variables; el archivo central de la tesis; incluye `LONGWT` y el peso longitudinal del SAQ `LSAQWT`) | https://www.meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h244/h244doc.pdf |

- Patrón de descarga de datos (formato Stata): `https://meps.ahrq.gov/mepsweb/data_files/pufs/{id}/{id}dta.zip` con `{id}` ∈ {h233, h243, h244, h251}. **Si un URL da 404, obtener el enlace desde la página de detalle del PUF; no adivinar.**
- Código de ejemplo oficial (R/SAS/Stata, incluye cómo cargar cada archivo): https://github.com/HHS-AHRQ/MEPS — usarlo como referencia de lectura y de nombres de variables.
- Explorador de variables: https://datatools.ahrq.gov/meps-hc#varExp
- Contexto de tamaño muestral (ya calculado en la fase de diseño): completan las 5 rondas del panel ≈ 5.700 personas; adultos con K6 en ambos años ≈ 2.900; K6 ≥ 13 ≈ 95; K6 ≥ 13 sin tratamiento ≈ 45. **Consecuencia de diseño (fija): el subgrupo severo se analiza descriptivamente, no se modela.** El target de salud mental es K6 continuo.

### 3.2 Módulo Chile

| Fuente | Contenido | Acceso |
|---|---|---|
| **ENS 2016-17** (MINSAL) | Prevalencias nacionales (síntomas depresivos 15,8%), módulo CIDI, base de medicamentos | Bases F1-F2 y F4 + documentación, descarga libre: http://epi.minsal.cl/bases-de-datos/ |
| **Termómetro de Salud Mental ACHS-UC** | Panel longitudinal 2020→2025 (11 rondas), PHQ-9, GAD-7, GHQ-12, AUDIT-C; ronda 11: 69,7% de quienes tuvieron problemas de salud mental no buscó o no pudo acceder a ayuda (~1,3 M personas) | Informes: https://www.achs.cl/termometro-salud-mental · Microdatos depositados en el repositorio de Datos de Investigación UC (buscar "Termómetro de la Salud Mental", PI David Bravo): https://datosinvestigacion.repositorio.uc.cl — **el acceso al microdato puede requerir solicitud; eso lo gestiona el humano, no Claude Code. Para v0.1 basta con los agregados de los informes.** |
| **Listas de espera GES/no-GES (Glosa 06)** | Informes trimestrales, incluido 1er trimestre 2026 | https://www.minsal.cl/eje-tiempos-de-espera/ |
| **DEIS MINSAL** | Microdatos anonimizados de egresos hospitalarios 2001–2023 (CIE-10 → filtrar F00–F99), atenciones de urgencia, REM, defunciones | Sección datos abiertos: https://deis.minsal.cl |
| **SUSESO** | Licencias médicas Fonasa + Isapre; trastornos mentales = 33,1% de las emitidas en 2024, primera causa | Estadísticas interactivas y informes anuales: https://www.suseso.cl (agregados descargables; no hay microdato individual) |
| **CASEN 2022** (y serie hasta 2024) | Microdatos libres; módulo salud (atención y tratamiento) + ingresos, para el gradiente socioeconómico | https://observatorio.ministeriodesarrollosocial.gob.cl/encuesta-casen |

### 3.3 Sintéticos (para el demo)

| Fuente | Uso | Acceso |
|---|---|---|
| **Synthea** (MITRE) | Cohorte sintética CSV para el demo (muestra de 1.000 pacientes basta) | Descargas: https://synthea.mitre.org/downloads · Generador: https://github.com/synthetichealth/synthea |
| **CMS Synthetic Medicare** (opcional, backlog) | Claims sintéticos formato RIF | https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event |

### 3.4 Lo que NO existe (y define el diseño)

No hay microdato chileno que vincule síntomas medidos con gasto individual (no existe un "MEPS chileno"). Por eso el módulo Chile es **triangulación descriptiva por diseño**. No intentar entrenar modelos con datos chilenos; documentar esta limitación en el README como parte del argumento.

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

- Mismo estimador (LGBMRegressor / LGBMClassifier) e **hiperparámetros idénticos** para los tres targets; tuning ligero con CV 5-fold en train, congelar y aplicar igual a todos.
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

audit_report(results, out_html) -> Path
# Informe HTML autocontenido con todas las figuras y tablas.
```

Requisitos: docstring con definición matemática exacta de cada métrica; soporte de `weights` en todas; tests unitarios con datos sintéticos de resultado conocido a mano; IC por bootstrap ponderado donde aplique.

### 4.5 `riskaudit.chile`

Entregable: `scripts/build_chile.py` produce 4 figuras + 1 tabla país, cada una con la fuente citada en el pie:
1. Prevalencia de síntomas depresivos (ENS 15,8%; Termómetro serie 2020–2025) vs población en tratamiento.
2. Brecha de acceso: 69,7% sin ayuda ≈ 1,3 M personas (Termómetro R11), desagregado si el informe lo permite.
3. Licencias médicas por trastornos mentales como % del total (serie SUSESO; 33,1% en 2024).
4. Salud mental en listas de espera GES (Glosa 06, último trimestre disponible).
Parsers tolerantes: los archivos MINSAL/SUSESO son Excel/PDF heterogéneos; si un parser automático es frágil, aceptar un paso manual documentado ("descargar X, guardarlo en `data/chile/`") antes que scraping frágil.

### 4.6 `demo/`

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

**Fase 4 — Chile (3–4 días).**
AC: `make chile` produce las 4 figuras + tabla con fuentes en el pie; `docs/methods.md` explica por qué es triangulación y no modelo.

**Fase 5 — Release (1–2 días).**
AC: README bilingüe completo (qué es, instalación, quickstart, hallazgos con 2 figuras, datos, limitaciones, cita); CHANGELOG; tag `v0.1.0`; instrucciones de archivado en Zenodo escritas (la cuenta la conecta el humano); sección "How to cite".

---

## 6. Guardrails para Claude Code

1. **Nombres de variables MEPS: nunca inventar.** Flujo obligatorio: buscar la variable en la documentación descargada (h244doc, h251doc) o en el Variable Explorer → registrarla en `dictionary.yml` con su referencia → recién entonces usarla. Si una variable esperada no existe en el año, detenerse, anotar en `docs/decisions.md` y proponer alternativa.
2. **Si los datos contradicen el plan** (tamaños muestrales, distribuciones, missingness), no forzar: documentar en `docs/decisions.md`, proponer ajuste y seguir. La honestidad estadística es un feature del proyecto.
3. **Pesos y varianza siempre** en resultados finales. Está permitido explorar sin pesos, prohibido reportar sin pesos.
4. **No sobre-afirmar con n chico**: el grupo severo lleva IC anchos y lenguaje descriptivo.
5. **Nada de datos en git**: ni microdatos, ni parquets, ni zips. Revisar `.gitignore` antes de cada commit.
6. **Sitios chilenos**: descargas simples con `requests`; si un sitio bloquea o el formato es caótico, pedir descarga manual al humano en vez de scraping agresivo.
7. **Commits convencionales** en inglés (`feat:`, `fix:`, `docs:`, `test:`); commits pequeños por unidad lógica.
8. **Al cerrar cada fase**: resumen de lo hecho, AC cumplidos, pendientes y decisiones tomadas. No avanzar de fase con AC en rojo.
9. **Volumen**: los archivos MEPS son de decenas de MB; procesar en memoria con pandas está bien; no introducir Spark/Dask.

---

## 7. Backlog explícito (NO hacer en v0.1)

Pooling de paneles 24–27; two-part models / GLM gamma para gasto; integración con `fairlearn`; CLI (`riskaudit audit ...`); dashboard interactivo del módulo Chile; conversión del demo a CMS Synthetic RIF; sitio de docs (mkdocs); manuscrito/preprint en Quarto. Anotarlos como issues de GitHub al final de la Fase 5.

---

## 8. Prompt inicial sugerido para Claude Code

> Lee PROTOCOL.md completo. Es la especificación del proyecto y sus decisiones son vinculantes. Ejecuta la Fase 0 (andamiaje) exactamente como la define la sección 5, respetando la estructura de la sección 2 y las decisiones de la sección 1. Cuando los criterios de aceptación de la Fase 0 estén verdes, muéstrame el resumen de cierre de fase (guardrail 8) y detente para que revise antes de autorizar la Fase 1.

Después, autorizar fase por fase. Para la Fase 1, recordarle el guardrail 1 (verificación de variables contra codebook) en el prompt de arranque.
