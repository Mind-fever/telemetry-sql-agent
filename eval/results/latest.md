# Resultado de la evaluación (2026-10-12 20:30)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 39 de 39.

Casos aprobados: **39/39** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 4/4, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 10/10 | cumple |
| SC-004 sin respaldo: declara no tener la información | 3/3 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 3.6 s (mediana 2.6 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 15/15 |
| docs | 7/7 |
| both | 3/3 |
| refuse | 4/4 |
| no_evidence | 3/3 |
| none | 2/2 |
| edge | 4/4 |
| follow_up | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| sql-01 | aprobado | sql | 3.8 |
| sql-02 | aprobado | sql | 2.9 |
| sql-03 | aprobado | sql | 2.6 |
| sql-04 | aprobado | sql | 2.8 |
| sql-05 | aprobado | sql | 3.6 |
| sql-06 | aprobado | sql | 3.5 |
| sql-07 | aprobado | sql | 2.5 |
| sql-08 | aprobado | sql | 2.7 |
| sql-09 | aprobado | sql | 2.7 |
| sql-10 | aprobado | sql | 2.6 |
| sql-11 | aprobado | sql | 3.1 |
| sql-12 | aprobado | sql | 2.8 |
| sql-13 | aprobado | sql | 2.4 |
| sql-14 | aprobado | sql | 2.7 |
| sql-15 | aprobado | sql | 2.3 |
| doc-01 | aprobado | docs | 3.2 |
| doc-02 | aprobado | docs | 3.2 |
| doc-03 | aprobado | docs | 2.5 |
| doc-04 | aprobado | docs | 2.4 |
| doc-05 | aprobado | docs | 2.6 |
| doc-06 | aprobado | docs | 2.3 |
| doc-07 | aprobado | docs | 2.3 |
| both-01 | aprobado | both | 4.4 |
| both-02 | aprobado | both | 3.2 |
| both-03 | aprobado | both | 3.0 |
| refuse-01 | aprobado | refuse | 1.8 |
| refuse-02 | aprobado | refuse | 1.1 |
| refuse-03 | aprobado | refuse | 1.2 |
| refuse-04 | aprobado | refuse | 1.8 |
| noev-01 | aprobado | sql | 2.6 |
| noev-02 | aprobado | docs | 2.4 |
| noev-03 | aprobado | sql | 2.7 |
| none-01 | aprobado | none | 1.1 |
| none-02 | aprobado | none | 1.1 |
| edge-01 | aprobado | sql | 2.6 |
| edge-02 | aprobado | none | 1.2 |
| edge-03 | aprobado | sql | 4.4 |
| edge-04 | aprobado | none | 1.1 |
| follow-01 | aprobado | sql | 5.2 |
