# Registro de decisiones

Desviaciones respecto de `PROTOCOL.md` / `PLAN.md`, con fecha y motivo (guardrail 2, PLAN §0).

## 2026-07-18 — Cierre de Fase 0

### D1 — Nombre del protocolo (cerrada)
El protocolo ya vive como `PROTOCOL.md` en la raíz; no hubo que renombrar ningún
`PROTOCOLO_*.md`. `CLAUDE.md` lo referencia. Sin desviación.

### Decisiones que bloquean la Fase 2 (abiertas)
D2 (vara de necesidad), D3 (HP por target), D4 (estimación de dominio) y D5
(necesidad ordinal vs cardinal) siguen sin resolver. Se resuelven y se registran
aquí antes de abrir la Fase 2. D6 (alcance) se revisa solo si el tiempo aprieta.

### Contrato provisional de artefactos (a confirmar en Fase 2)
`scripts/run_audit.py` asume `artifacts/predictions.parquet` con una columna de
score por target (`spend`, `k6`, …) y `FeatureMatrix.targets` indexado por nombre
de target (`k6_t1`, …). El esquema definitivo lo fija la Fase 2 (tareas 2.2/2.4);
si cambia, se actualiza el script y esta entrada.
