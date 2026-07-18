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
