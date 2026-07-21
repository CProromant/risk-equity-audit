# Roadmap v2 — de librería publicada a implementación de referencia

Estado base (2026-07): `riskaudit` v0.1.1 en PyPI, archivado en Zenodo (DOI
10.5281/zenodo.21461268), CI verde, ~99% cobertura. Ejemplos MEPS y demo sintético
completos. El **producto es la librería**; los ejemplos solo demuestran que corre.

**Principio ordenador.** Cada función nueva debe responder: *¿cuánta necesidad quedó
fuera, de quién, comparado con qué, y con qué certeza?* Lo que no responda eso, no entra.
El riesgo dominante es la dispersión de un autor solo → lista cerrada, fases publicables
por sí solas, ninguna función sin al menos un usuario externo que la pida.

## Fase A — Validación canónica (Obermeyer et al. 2019) · iniciar ya

Reproducir las métricas de auditoría del caso más citado de label-choice bias sobre su
dataset sintético público (`gitlab.com/labsysmed/dissecting-bias`), usando **solo el API
público**. Alcance conocido: el sintético no trae covariables para reentrenar el modelo →
se reproducen las métricas, no el algoritmo (documentado en `COVERAGE.md`).

Entregables: `validation/obermeyer_2019/{download.py, COVERAGE.md, obermeyer_2019.ipynb}`,
test protegido (`make validate-obermeyer`, `RISKAUDIT_RUN_VALIDATION=1`), sección
"Validation" bilingüe en README. **Regla dura:** si un resultado no reproduce dentro de
tolerancia, se documenta la discrepancia con hipótesis de causa — no se ajusta la tolerancia.

Independiente del resto. Es el ancla de confianza: cualquiera verifica que las métricas
miden lo que dicen.

## Fase B — Expansión del API

Tres capacidades nuevas: **normalizar** (¿malo comparado con qué?), **desagregar** (¿de
quién es la necesidad omitida?), **decidir** (¿qué etiqueta elegir antes de desplegar?), más
funciones que blindan el resultado contra la crítica metodológica. Todas heredan la
infraestructura: pesos, bootstrap de filas/diseño (VARSTR/VARPSU), validación de entradas.

> Nota: `oracle_capture` del plan original **ya está** — `top_k_capture` reporta `baseline`
> (=k) y `oracle`. No se rehace; a lo sumo se expone un helper suelto si algún ejemplo lo pide.

### Tanda 1 (barata, sobre maquinaria existente; se demuestra sobre Obermeyer/MEPS)

| Función | Qué responde |
|---|---|
| `group_capture(scores, need, k, weights, groups)` | Captura desagregada por subgrupo con IC de diseño — la pregunta de equidad directa. Wrapper del bootstrap ya construido. |
| `label_blend_frontier(scores_by_label, need, k, weights, alphas)` | Barre etiquetas compuestas α·A+(1−α)·B y muestra, por α, captura y composición del top-k: la frontera de trade-off completa. Es el remedio de Obermeyer (reetiquetar), ejecutable. La más citable. |
| **`label_robustness(scores, need, weights, noise_grid)`** *(idea Fable)* | ¿Cuánto error en la **propia `need`** tumbaría la conclusión? Inyecta ruido/sesgo acotado en `need` y reporta la perturbación mínima que da vuelta la brecha de captura — un bound estilo Rosenbaum, no un IC de muestreo. Ataca el punto donde un revisor pega de verdad ("¿cómo sabes que tu etiqueta de necesidad es correcta?"). Nadie lo empaqueta; nuestra propia experiencia MEPS (K6 es un proxy, el efecto se cae en utilización no-psiquiátrica) lo justifica. **Prioridad de la tanda.** |

### Tanda 2 (v0.2+; algunas se benefician del panel MEPS modelado)

| Función | Qué responde |
|---|---|
| **`worst_off_capture(scores, need, weights, covariates, k)`** *(idea Fable)* | *Descubre* la rebanada peor-servida en vez de exigir nombrar el eje — que es justo el punto ciego que hizo posible Obermeyer (nadie preguntó por raza hasta mirar). Búsqueda greedy de la mayor brecha de captura + corrección por multiplicidad (permutaciones) para un IC honesto. Extiende `group_capture`; más ambiciosa → vigilar scope. Verificable: plantar una rebanada conocida y confirmar que la recupera. |
| `capture_sweep(scores, need, weights)` | Captura como curva de k (captura marginal por decil): la pregunta presupuestaria ("¿del 5% al 10%, cuánta necesidad nueva gano?"). |
| `cost_of_blindness(y_t1, y_pred, need, scores, k, weights)` | La matemática de `incremental_lift` traducida a plata: gasto futuro no capturado por cada 1.000 cupos. Los directores de presupuesto no leen lifts. |
| `topk_stability(scores, need, k, weights, n_boot)` | Fracción de la lista estable entre réplicas bootstrap vs. la que entra/sale por azar cerca del umbral. Ningún paquete de fairness lo reporta. |
| `need_weighted_nri(scores_a, scores_b, need, k, weights)` | NRI ponderado por necesidad y con varianza de diseño: ¿el modelo B mueve *necesidad* al top-k, no solo gente? |
| `audit_manifest(inputs, params)` | Hash SHA-256 de insumos/versiones/semilla incrustado en `audit_report`. No es estadística: es verificabilidad — prerequisito de la Fase C. |

**Qué NO entra:** métricas de fairness genéricas (fairlearn), calibración por grupos
(sklearn/pycalib), cualquier cosa que entrene o mitigue. El paquete es fuerte porque hace
una cosa: medir necesidad dejada atrás.

**Estándar por función:** implementación + tests a ~99% + fila en la tabla del README
(EN/ES) + integración en `audit_report`. Toda función reporta IC (filas y diseño) o declara
en el docstring por qué no aplica (`audit_manifest`).

## Fase C — Un modelo real (paralelo, no en ruta crítica)

Auditar un algoritmo desplegado que asigne recursos reales (servicio de salud con listas de
espera, isapre con gestión de casos, programa ministerial). El diseño lo hace viable: solo
`scores` + medida de necesidad, sin acceso al modelo ni PHI, ejecutable en los servidores de
la institución con `audit_manifest` garantizando integridad del informe.

Entregables: `docs/audit-protocol-external.md`, one-pager (ES) para instituciones candidatas,
caso piloto (un nulo bien medido también valida). Horizonte 6–18 meses, prob. ~30–50% → **no
bloquea nada**; el proyecto es completo y citable sin C. Gestión de contactos en paralelo
desde ya; ejecución tras A.

## Secuencia

```
A (Obermeyer) ─────────────┐   [iniciar ya: independiente]
                           ├─> B tanda 1 (group_capture · label_blend_frontier · label_robustness)
cerrar modelado MEPS ──────┤
                           └─> B tanda 2 (worst_off_capture · capture_sweep · cost_of_blindness · …)
C: contactos desde ya; ejecución tras A ─> piloto (si hay puerta)
```
