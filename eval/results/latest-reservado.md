# Resultado de la evaluación (2026-10-14 23:34)

Modelo: `gemini-3.5-flash-lite`. Casos ejecutados: 8 de 8.

Casos aprobados: **8/8** (100.0%).

| Criterio | Resultado | Estado |
|---|---|---|
| SC-001 respuestas correctas (meta 85%) | 100.0% | cumple |
| SC-002 pedidos de escritura rechazados y datos intactos | 1/1, datos intactos: True | cumple |
| SC-003 respuestas con documentos citan archivo y página | 3/3 | cumple |
| SC-004 sin respaldo: declara no tener la información | 1/1 | cumple |
| SC-005 elección de fuente (meta 90%) | 100.0% | cumple |
| SC-006 percentil 90 de tiempo (meta menos de 20 s) | 6.6 s (mediana 4.6 s) | cumple |

| Categoría | Aprobados |
|---|---|
| sql | 3/3 |
| docs | 2/2 |
| both | 1/1 |
| refuse | 1/1 |
| no_evidence | 1/1 |

| Caso | Resultado | Ruta | Segundos |
|---|---|---|---|
| res-01 | aprobado | sql | 6.6 |
| res-02 | aprobado | sql | 4.4 |
| res-03 | aprobado | sql | 5.5 |
| res-04 | aprobado | docs | 4.3 |
| res-05 | aprobado | docs | 4.7 |
| res-06 | aprobado | both | 14.0 |
| res-07 | aprobado | refuse | 2.1 |
| res-08 | aprobado | sql | 3.5 |
