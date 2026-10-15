# Contrato: configuración de cada entorno

**Plan**: [plan.md](../plan.md)

La interfaz que expone esta funcionalidad no es una API: es la configuración que lee el agente. El agente
lee todo con `os.getenv` (`src/telemetry_agent/config.py`). Este contrato fija qué variable va en cada
entorno y con qué valor.

## Entornos

| Entorno | Dónde vive la configuración | Para qué |
|---|---|---|
| **Local** | `.env` | Desarrollo, pruebas y evaluación con Docker. No cambia. |
| **Carga** | `.env` más variables definidas solo para un proceso | Crear el esquema y el rol y cargar los datos en Neon. Se usa desde la máquina del autor. |
| **Prueba contra Neon** | `.env` más variables definidas solo para un proceso | Correr el agente local y los 8 casos contra Neon |
| **Nube** | Panel de Secrets de Streamlit, con claves de primer nivel y sin secciones | La app pública |

## Variables

`—` significa que la variable no se define en ese entorno.

| Variable | Local (`.env`) | Carga | Prueba contra Neon | Nube (Secrets) |
|---|---|---|---|---|
| `DATABASE_URL` | Docker, con escritura (sin cambios) | Neon **directa**, `neondb_owner` | Neon **directa**, `neondb_owner`. El agente no la usa, pero `run_eval.py` sí: consultas de referencia y conteo de filas (R9) | **— nunca** |
| `DATABASE_URL_RO` | Docker, `agent_ro` (sin cambios) | `NUBE_DATABASE_URL_RO` (define la clave del rol) | `NUBE_DATABASE_URL_RO` | Valor de `NUBE_DATABASE_URL_RO` |
| `NUBE_DATABASE_URL` | Neon pooled, `neondb_owner` (ya está) | de acá sale la directa, sacando `-pooler` del host | — | **— nunca** |
| `NUBE_DATABASE_URL_RO` | Neon pooled, `agent_ro` (nueva, R3) | — | — | — (se copia su valor a `DATABASE_URL_RO`) |
| `GEMINI_API_KEY` | clave local | — | clave local | **clave aparte para la nube** (FR-011) |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | — | igual que local | `gemini-3.5-flash-lite` |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | — | igual que local | `gemini-embedding-2` |
| `EMBEDDING_DIMENSIONS` | `768` | — | igual que local | `768` |
| `LANGSMITH_TRACING` | `true` | — | `true` | `true` |
| `LANGSMITH_API_KEY` | clave de LangSmith | — | igual que local | clave de LangSmith |
| `LANGSMITH_PROJECT` | `agente-sql-telemetria` | — | `agente-sql-telemetria-nube` | `agente-sql-telemetria-nube` |
| `SQL_MAX_ROWS` | `50` | — | igual que local | `50` |
| `SQL_TIMEOUT_MS` | `8000` | — | igual que local | `8000` |
| `SQL_MAX_RETRIES` | `2` | — | igual que local | `2` |
| `RETRIEVAL_TOP_K` | `4` | — | igual que local | `4` |

## Garantías

- **G1 (solo lectura)**: en la nube, la única cadena de conexión es la de `agent_ro`. Ni `DATABASE_URL` ni
  `NUBE_DATABASE_URL` se cargan en Streamlit.
- **G2 (local intacto)**: `DATABASE_URL` y `DATABASE_URL_RO` de `.env` conservan sus valores de Docker.
  Los entornos de carga y de prueba los reemplazan solo dentro del proceso: `load_dotenv` no pisa una
  variable que ya está definida.
- **G3 (sin secretos en el repo)**: los valores solo existen en `.env`, que está en `.gitignore`, y en el
  panel de Streamlit. `.env.example` lista `NUBE_DATABASE_URL` y `NUBE_DATABASE_URL_RO` sin valores.
- **G4 (mismo comportamiento)**: los valores no secretos de la nube son los mismos que los locales.
- **G5 (claves de primer nivel)**: en Secrets, cada variable va como `NOMBRE = "valor"` en el primer nivel.
  Lo que va dentro de una sección `[...]` no llega como variable de entorno (R5).

## Formato del panel de Secrets

Los nombres son los de arriba. Los valores los carga el autor y no se escriben en ningún archivo del
repositorio:

```toml
DATABASE_URL_RO = "<valor de NUBE_DATABASE_URL_RO>"
GEMINI_API_KEY = "<clave aparte para la nube>"
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = "768"
LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "<clave de LangSmith>"
LANGSMITH_PROJECT = "agente-sql-telemetria-nube"
SQL_MAX_ROWS = "50"
SQL_TIMEOUT_MS = "8000"
SQL_MAX_RETRIES = "2"
RETRIEVAL_TOP_K = "4"
```

Los números van entre comillas para que lleguen como texto, igual que desde `.env`.
