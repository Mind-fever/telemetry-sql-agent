# Contrato: respuesta del agente

Lo comparten la interfaz Streamlit, la terminal y el evaluador. Cualquier cambio acá se refleja
en los tres.

## Entrada

| Campo | Tipo | Descripción |
|---|---|---|
| question | texto | pregunta del usuario, en castellano o inglés |
| thread_id | texto | identifica la conversación, para el contexto de seguimiento |

## Salida (`AgentResponse`)

| Campo | Tipo | Descripción |
|---|---|---|
| answer | texto | respuesta final, en el idioma de la pregunta |
| route | `sql`, `docs`, `both`, `none` o `refuse` | fuente que decidió usar el router; `refuse` es un pedido rechazado |
| route_reason | texto | justificación corta del router |
| sql | texto o nulo | consulta ejecutada, si se usó la base |
| rows | lista de filas o nulo | filas devueltas, ya acotadas |
| rows_truncated | booleano | verdadero si se aplicó el tope de filas |
| sources | lista de fuentes | fragmentos usados: `archivo`, `pagina`, `texto` |
| refused | booleano | verdadero si el pedido se rechazó por la regla de solo lectura |
| grounded | booleano | falso si el agente declaró no tener la información |
| error | texto o nulo | mensaje claro si no se pudo responder por un problema técnico |

## Reglas

- Si `route` es `sql` o `both`, `sql` está presente, salvo que la consulta haya sido rechazada.
- Si `route` es `docs` o `both` y `grounded` es verdadero, `sources` tiene al menos un elemento
  con `archivo` y `pagina` (SC-003).
- Si `refused` es verdadero, no se ejecutó ninguna sentencia contra la base (SC-002).
- Si `grounded` es falso, `answer` dice que no se encontró la información (SC-004).
