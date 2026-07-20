# Registro de decisiones

Desviaciones respecto de `PROTOCOL.md` / `PLAN.md`, con fecha y motivo (guardrail 2, PLAN §0).

## 2026-07-18 — Cierre de Fase 0

### D1 — Nombre del protocolo (cerrada)
El protocolo ya vive como `PROTOCOL.md` en la raíz; no hubo que renombrar ningún
`PROTOCOLO_*.md`. `CLAUDE.md` lo referencia. Sin desviación.

## 2026-07-18 — Decisiones D2–D5 (resueltas; detalle matemático en `docs/methods.md`)

### D2 — Vara de necesidad: EQUIDAD como argumento central
El claim principal es normativo-equitativo: el distrés medido (K6) es necesidad
legítima aunque aún no haya generado gasto. Riesgo conocido: objeción de
circularidad. Se contesta empíricamente con la métrica-contribución (abajo), no
con retórica. Ver `methods.md` §1–§2.

### Métrica-contribución — Lift de necesidad incremental en la cola baja
Contribución original de `riskaudit` (no-Obermeyer): entre los deprioritizados por
el modelo de gasto, diferencia ponderada del residual del desenlace futuro entre
personas con y sin distrés. Es la columna empírica que sostiene D2 y neutraliza la
circularidad — el desenlace es gasto/utilización futura, no K6. `methods.md` §2.

### D3 — Hiperparámetros: TUNING LIGERO POR TARGET
Misma clase de modelo y mismas features (comparabilidad); HP por target con la
misma rutina CV 5-fold, luego congelados. No idénticos. `methods.md` §4.

### D4 — Estimación de DOMINIO (decidida por correctitud)
Subpoblaciones vía indicador 0/1 sobre el marco muestral completo; nunca
filtrar-y-repesar. Varianza por linearización de Taylor sobre `VARSTR`/`VARPSU`.
`methods.md` §3.

### D5 — Necesidad: CONTINUO principal + umbral K6≥13 como robustez
`methods.md` §1.

### D6 — Alcance: sin cambios; se revisa solo si el tiempo aprieta.

### Contrato provisional de artefactos (a confirmar en Fase 2)
`scripts/run_audit.py` asume `artifacts/predictions.parquet` con una columna de
score por target (`spend`, `k6`, …) y `FeatureMatrix.targets` indexado por nombre
de target (`k6_t1`, …). El esquema definitivo lo fija la Fase 2 (tareas 2.2/2.4);
si cambia, se actualiza el script y esta entrada.

## 2026-07-18 — Fase 1 (ETL MEPS)

### Verificación de variables (guardrail 1)
Los nombres crudos se leyeron de las **etiquetas embebidas de los `.dta`** (metadata
pyreadstat), no se adivinaron. Todos en `dictionary.yml`. Hallazgos que corrigen el
plan: diabetes es `DIABDX_M18` (no `DIABDX`); cáncer es `CANCERY1/Y2` en el panel y
`CANCERDX` en FYC; K6 del panel es `K6SUM2` (2021, R2) y `K6SUM4` (2022, R4). Mapeo
del Panel 26 confirmado por etiquetas: `Y1`=2021, `Y2`=2022.

### Códigos faltantes de MEPS
MEPS usa negativos reservados `{-1,-7,-8,-9,-15}` como faltantes. `meps.py` los
convierte a NaN salvo en ids, pesos, estrato y PSU. K6 válido = `[0,24]`.

### N real vs esperado (guardrail 2)
Panel 26 = **6.741** personas (los ~5.700 del plan son los *completers* con `LONGWT`).
Adultos con K6 válido en ambos años = **3.001** (esperado ~2.900, ✓). Distrés severo
`K6_t≥13` con K6 en ambos años = **135**; el subgrupo *sin tratamiento* será menor y se
fija al operacionalizar el tratamiento (abajo). `fyc_pooled` = 69.686 filas (28.336 +
22.431 + 18.919 para 2021/22/23). Perfilado en `artifacts/meps_profile.txt`.

### Tratamiento de salud mental (deferido)
El flag "distrés no tratado" necesita un proxy de tratamiento (visitas/gasto en salud
mental), que vive en los archivos de eventos/condiciones, no en el FYC/longitudinal. Se
operacionaliza en `methods.md` antes de que la Fase 2 lo use. No se usó ningún nombre
sin verificar.

### Workaround de TLS (entorno)
La máquina intercepta el HTTPS de Python con una raíz que OpenSSL 3 rechaza (falla hasta
github.com). `download.py` verifica TLS por defecto pero acepta `RISKAUDIT_INSECURE_TLS=1`
(o `RISKAUDIT_CA_BUNDLE`); la integridad la garantizan los SHA-256 de `data/checksums.txt`.

## 2026-07-19 — Fase 2: proxy de tratamiento de salud mental

Operacionalización verificada contra los datos (guardrail 1). **Tratado_SM 2021** =
condición SM en HC-231 (ICD-10 `F*` o CCSR `MBD*`) **o** psicofármaco en HC-229A (clases
Multum {67,70,71,76,77,79,208,209,210,242,249,251,306,307,308,341,504,516}; se excluyen
los cajones CNS 57/80). Sanity: los fármacos más frecuentes son sertralina, trazodona,
escitalopram, duloxetina. **N:** 21.2% del panel tratado; distrés severo K6_t≥13 = 190, de
los cuales **63 sin tratamiento** (subgrupo pequeño → solo descriptivo, guardrail 4).
Robustez (backlog): definición estrecha (solo mood/ansiedad). Salida:
`data/processed/treatment.parquet` vía `build_treatment_proxy`.

### Predicciones: OOF 5-fold sobre todo el dominio (en vez de split 80/20)
El PROTOCOL §4.3 pedía split 80/20. Uso **5-fold cross-fitting sobre toda la muestra
analítica** (folds estratificados por decil de gasto_t): cada fila queda predicha por un
modelo que no la vio, así el audit corre sobre las 3.001 con predicciones honestas (más
filas que un test del 20%). Métricas OOF: spend R²≈0.48, avoidable AUC≈0.69, K6 R²≈0.41
(K6 dominado por K6_t — semi-tautológico, ya documentado). HP tuneados por target sobre
un grid chico y congelados (D3). Salidas en `artifacts/`: `predictions.parquet`,
`metrics.json` (con SHAP), `model_{target}.txt`.

### Demo: sintético auto-contenido, no Synthea
El PROTOCOL proponía Synthea. Uso un **generador sintético dentro de `demo/run_demo.py`**
(determinista, `seed=2026`): el auditor solo necesita scores+need+weights, así que un
dataset inventado en el script es más robusto y rápido que una descarga externa frágil, y
cumple el mismo propósito (ver la herramienta funcionar sin datos reales ni PHI).

## 2026-07-19 — Revisión de código (REVIEW.md) y su resolución

Una revisión externa encontró bugs que fabricaban o sobre-afirmaban hallazgos. Cerrados:

- **Ablación in-sample (A1):** ahora cross-fitted; Δglobal se mide, no se asume ≈0.
- **Ablación medía captura del target (A2):** parámetro `need`; audita captura de K6.
- **Lift con un modelo que veía K6 (A3):** se reporta con y sin las features de salud mental (ciego
  +1.05, con features +0.77 — ambos IC excluyen 0). El sesgo es de la **etiqueta**, no de falta de info.
- **Escala y circularidad (A4):** el lift se declara en log-dólares y se reporta también sobre
  utilización evitable (no-psiquiátrica), donde es **nulo** (≈+0.04, IC incluye 0). Conclusión honesta:
  **no se demuestra el mecanismo no-psiquiátrico**; un target de gasto no-psiquiátrico queda en backlog.
- **Captura sin piso/oráculo (B1):** `CaptureResult` reporta floor (=k) y oracle. Spend 15% vs floor 10%, oracle 41%.
- **RTM mal especificado (B2):** fórmula con pendiente de regresión; degradado a descriptivo.
- **Varianza:** el bootstrap opera sobre el dominio filtrado (A5); se avisa cuando un estrato colapsa a 1
  PSU (3 en el panel) (B3); se quitó la promesa muerta de linearización de Taylor (D3).
- **Determinismo (N2):** LightGBM `deterministic=True, force_row_wise=True`.
- **Validación (C3/N1):** las funciones públicas exigen finitos y misma longitud; `run_audit` re-indexa por etiqueta.
- **Docs (D1/D2):** estado único; n del subgrupo severo = 40 (analítico) / 63 (panel); borrado el "45" muerto.
