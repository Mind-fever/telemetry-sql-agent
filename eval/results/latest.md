# Resultado de la evaluación (2026-10-15 00:10)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 43 de 43.

Casos aprobados: **43/43** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 4/4, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 10/10 | cumple |
| SC-004 sin respaldo: declara no tener la información | 3/3 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 15.9 s (mediana 10.4 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 15/15 |
| docs | 7/7 |
| both | 3/3 |
| refuse | 4/4 |
| no_evidence | 3/3 |
| none | 2/2 |
| edge | 8/8 |
| follow_up | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| sql-01 | aprobado | sql | 7.0 |
| sql-02 | aprobado | sql | 5.6 |
| sql-03 | aprobado | sql | 6.8 |
| sql-04 | aprobado | sql | 7.6 |
| sql-05 | aprobado | sql | 14.0 |
| sql-06 | aprobado | sql | 15.9 |
| sql-07 | aprobado | sql | 15.5 |
| sql-08 | aprobado | sql | 13.0 |
| sql-09 | aprobado | sql | 14.1 |
| sql-10 | aprobado | sql | 14.1 |
| sql-11 | aprobado | sql | 10.4 |
| sql-12 | aprobado | sql | 3.9 |
| sql-13 | aprobado | sql | 3.6 |
| sql-14 | aprobado | sql | 3.1 |
| sql-15 | aprobado | sql | 3.6 |
| doc-01 | aprobado | docs | 3.3 |
| doc-02 | aprobado | docs | 8.1 |
| doc-03 | aprobado | docs | 13.9 |
| doc-04 | aprobado | docs | 13.9 |
| doc-05 | aprobado | docs | 13.7 |
| doc-06 | aprobado | docs | 10.9 |
| doc-07 | aprobado | docs | 12.1 |
| both-01 | aprobado | both | 21.7 |
| both-02 | aprobado | both | 17.1 |
| both-03 | aprobado | both | 15.5 |
| refuse-01 | aprobado | refuse | 5.9 |
| refuse-02 | aprobado | refuse | 6.2 |
| refuse-03 | aprobado | refuse | 6.1 |
| refuse-04 | aprobado | refuse | 5.7 |
| noev-01 | aprobado | sql | 14.7 |
| noev-02 | aprobado | docs | 6.9 |
| noev-03 | aprobado | docs | 9.3 |
| none-01 | aprobado | none | 5.8 |
| none-02 | aprobado | none | 5.7 |
| edge-01 | aprobado | sql | 16.3 |
| edge-02 | aprobado | none | 3.7 |
| edge-03 | aprobado | sql | 24.0 |
| edge-04 | aprobado | none | 5.3 |
| edge-05 | aprobado | sql | 14.3 |
| edge-06 | aprobado | sql | 12.7 |
| edge-07 | aprobado | sql | 9.0 |
| edge-08 | aprobado | sql | 11.5 |
| follow-01 | aprobado | sql | 25.6 |
