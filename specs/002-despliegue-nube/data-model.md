# Modelo de datos: Despliegue del agente en la nube

**Plan**: [plan.md](plan.md)

Esta funcionalidad no agrega tablas ni columnas. El esquema es `db/schema.sql`, definido en
[la 001](../001-agente-sql-telemetria/data-model.md). Lo que se describe acá son las tres piezas de la
especificación y las reglas que las validan.

## Base remota

Copia de la base local en Neon (`neondb`, esquema `public`).

| Tabla | Filas esperadas | Fuente |
|---|---|---|
| areas | 18 | volcado |
| tecnicos | 20 | volcado |
| equipos | 40 | volcado |
| sensores | 108 | volcado |
| lecturas | 38.880 | volcado |
| alarmas | 171 | volcado |
| ordenes_mantenimiento | 153 | volcado |
| doc_chunks | 18 | volcado (con los embeddings de 768 dimensiones ya calculados) |

**Reglas**:

- Cada tabla tiene exactamente la cantidad de filas de la tabla de arriba, que es la misma de la base local
  (SC-002).
- Las secuencias quedan en el último id de cada tabla. Las ajustan los `setval` del volcado.
- La extensión `vector` queda instalada en `public`.
- Existe el rol `agent_ro` con login y con los permisos de `db/roles.sql`: SELECT sobre las 8 tablas, sin
  escritura y sin DDL.
- Una sentencia de escritura con `agent_ro` falla con un error de permisos (FR-005, caso borde de la
  especificación).

**Ciclo de vida**:

```text
vacía → esquema y rol creados (setup_db.py) → datos cargados (volcado) → verificada (conteo)
                                                                          ↓
                                                         suspendida ⇄ activa (Neon, sola)
                                                                          ↓
                                    después del 30/10: se conserva o se borra (decisión del autor)
```

`setup_db.py` recrea todo desde cero, así que el paso se puede repetir si una carga sale mal.

## Aplicación desplegada

La app de `app/streamlit_app.py`, publicada en Streamlit Community Cloud.

| Atributo | Valor |
|---|---|
| Repositorio y rama | `Mind-fever/telemetry-sql-agent`, `master` (R7) |
| Archivo principal | `app/streamlit_app.py` |
| Python | 3.13 (R6) |
| Dirección | subdominio fijo en `streamlit.app`, elegido al crear la app |
| Acceso | público hasta el 30 de octubre de 2026 inclusive |
| Configuración | Secrets, según [contracts/configuracion-nube.md](contracts/configuracion-nube.md) |

**Ciclo de vida**:

```text
creada → construyendo → activa ⇄ dormida (12 h sin visitas; se despierta con un botón)
                          ↓
            después del 30/10: borrada o privada
```

**Reglas**:

- Cada visitante tiene su propia conversación (`thread_id` por sesión, ya implementado).
- Si falta una variable, la app muestra qué variable falta y no muestra su valor.

## Configuración de la nube

Claves y valores que la app necesita. Viven en el panel de Secrets de Streamlit y, para los pasos que se
corren desde la máquina del autor, en `.env`. El detalle de cada variable está en
[contracts/configuracion-nube.md](contracts/configuracion-nube.md).

**Reglas**:

- Ningún valor secreto se sube al repositorio. `.env` y `.streamlit/secrets.toml` ya están en `.gitignore`.
- `DATABASE_URL` no está en los Secrets de Streamlit.
- `GEMINI_API_KEY` de la nube es distinta de la de `.env`.

## Evidencia

Lo que el informe necesita para el criterio de despliegue (FR-013):

| Evidencia | Dónde queda |
|---|---|
| Dirección pública | README e informe |
| Captura de la app respondiendo | `docs/` (imagen que referencia el informe) |
| Traza de esa ejecución | proyecto `agente-sql-telemetria-nube` en LangSmith (enlace o captura) |
| Resultado de los 8 casos contra Neon | `eval/results/latest-nube.md` y `<fecha>-nube.json` |
| Conteo de filas de la base remota | `tasks.md` de la 002 y el informe |
