# Resultado de la evaluación (2026-10-15 16:16)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 8 de 8.

Casos aprobados: **8/8** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 1/1, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 2/2 | cumple |
| SC-004 sin respaldo: declara no tener la información | 1/1 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 10.0 s (mediana 6.2 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 1/1 |
| docs | 1/1 |
| both | 1/1 |
| refuse | 1/1 |
| no_evidence | 1/1 |
| none | 1/1 |
| edge | 1/1 |
| follow_up | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| sql-01 | aprobado | sql | 10.0 |
| doc-01 | aprobado | docs | 5.4 |
| both-01 | aprobado | both | 8.0 |
| refuse-01 | aprobado | refuse | 3.3 |
| noev-02 | aprobado | docs | 5.3 |
| none-01 | aprobado | none | 3.8 |
| edge-03 | aprobado | sql | 6.9 |
| follow-01 | aprobado | sql | 17.5 |
