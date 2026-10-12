# Resultado de la evaluación (2026-10-12 16:37)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 38 de 38.

Casos aprobados: **38/38** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 4/4, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 10/10 | cumple |
| SC-004 sin respaldo: declara no tener la información | 3/3 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 4.6 s (mediana 3.1 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 15/15 |
| docs | 7/7 |
| both | 3/3 |
| refuse | 4/4 |
| no_evidence | 3/3 |
| none | 2/2 |
| edge | 3/3 |
| follow_up | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| sql-01 | aprobado | sql | 4.6 |
| sql-02 | aprobado | sql | 3.4 |
| sql-03 | aprobado | sql | 2.6 |
| sql-04 | aprobado | sql | 3.0 |
| sql-05 | aprobado | sql | 3.7 |
| sql-06 | aprobado | sql | 3.4 |
| sql-07 | aprobado | sql | 2.8 |
| sql-08 | aprobado | sql | 2.7 |
| sql-09 | aprobado | sql | 3.1 |
| sql-10 | aprobado | sql | 3.1 |
| sql-11 | aprobado | sql | 4.6 |
| sql-12 | aprobado | sql | 3.9 |
| sql-13 | aprobado | sql | 2.9 |
| sql-14 | aprobado | sql | 3.9 |
| sql-15 | aprobado | sql | 3.6 |
| doc-01 | aprobado | docs | 3.4 |
| doc-02 | aprobado | docs | 3.5 |
| doc-03 | aprobado | docs | 3.4 |
| doc-04 | aprobado | docs | 2.4 |
| doc-05 | aprobado | docs | 2.6 |
| doc-06 | aprobado | docs | 2.9 |
| doc-07 | aprobado | docs | 3.2 |
| both-01 | aprobado | both | 4.9 |
| both-02 | aprobado | both | 4.6 |
| both-03 | aprobado | both | 5.2 |
| refuse-01 | aprobado | refuse | 1.2 |
| refuse-02 | aprobado | refuse | 1.1 |
| refuse-03 | aprobado | refuse | 1.6 |
| refuse-04 | aprobado | refuse | 1.1 |
| noev-01 | aprobado | sql | 2.8 |
| noev-02 | aprobado | docs | 3.1 |
| noev-03 | aprobado | sql | 3.1 |
| none-01 | aprobado | none | 1.9 |
| none-02 | aprobado | none | 1.3 |
| edge-01 | aprobado | sql | 2.7 |
| edge-02 | aprobado | none | 1.3 |
| edge-03 | aprobado | sql | 4.5 |
| follow-01 | aprobado | sql | 5.9 |
