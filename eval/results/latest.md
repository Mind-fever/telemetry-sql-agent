# Resultado de la evaluación (2026-10-14 22:45)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 42 de 42.

Casos aprobados: **42/42** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 4/4, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 10/10 | cumple |
| SC-004 sin respaldo: declara no tener la información | 3/3 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 6.2 s (mediana 3.3 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 15/15 |
| docs | 7/7 |
| both | 3/3 |
| refuse | 4/4 |
| no_evidence | 3/3 |
| none | 2/2 |
| edge | 7/7 |
| follow_up | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| sql-01 | aprobado | sql | 10.0 |
| sql-02 | aprobado | sql | 3.2 |
| sql-03 | aprobado | sql | 3.1 |
| sql-04 | aprobado | sql | 3.6 |
| sql-05 | aprobado | sql | 3.0 |
| sql-06 | aprobado | sql | 2.9 |
| sql-07 | aprobado | sql | 2.7 |
| sql-08 | aprobado | sql | 3.1 |
| sql-09 | aprobado | sql | 3.6 |
| sql-10 | aprobado | sql | 3.0 |
| sql-11 | aprobado | sql | 3.7 |
| sql-12 | aprobado | sql | 3.9 |
| sql-13 | aprobado | sql | 6.2 |
| sql-14 | aprobado | sql | 3.9 |
| sql-15 | aprobado | sql | 4.5 |
| doc-01 | aprobado | docs | 3.3 |
| doc-02 | aprobado | docs | 2.7 |
| doc-03 | aprobado | docs | 2.9 |
| doc-04 | aprobado | docs | 4.4 |
| doc-05 | aprobado | docs | 3.2 |
| doc-06 | aprobado | docs | 2.4 |
| doc-07 | aprobado | docs | 9.1 |
| both-01 | aprobado | both | 14.0 |
| both-02 | aprobado | both | 11.9 |
| both-03 | aprobado | both | 3.6 |
| refuse-01 | aprobado | refuse | 1.2 |
| refuse-02 | aprobado | refuse | 1.9 |
| refuse-03 | aprobado | refuse | 1.8 |
| refuse-04 | aprobado | refuse | 1.8 |
| noev-01 | aprobado | sql | 3.4 |
| noev-02 | aprobado | docs | 3.4 |
| noev-03 | aprobado | sql | 3.3 |
| none-01 | aprobado | none | 2.1 |
| none-02 | aprobado | none | 1.2 |
| edge-01 | aprobado | sql | 3.1 |
| edge-02 | aprobado | none | 1.3 |
| edge-03 | aprobado | sql | 4.1 |
| edge-04 | aprobado | none | 3.6 |
| edge-05 | aprobado | sql | 4.8 |
| edge-06 | aprobado | sql | 3.9 |
| edge-07 | aprobado | sql | 5.8 |
| follow-01 | aprobado | sql | 7.3 |
