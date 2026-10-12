# Agente SQL de telemetría y mantenimiento industrial

Trabajo Práctico Integrador de AI Engineering (Ingeniería en Informática, 5to año).

Un agente de IA que responde preguntas en castellano o inglés sobre una planta industrial ficticia.
Consulta una base de datos relacional con SQL que genera el modelo y busca en manuales en PDF con RAG.
En cada pregunta decide por sí mismo qué fuente usar: la base, los documentos, ambas o ninguna.
Solo lee: nunca modifica la base.

## Qué incluye

| Pieza | Dónde |
|---|---|
| Base relacional con 7 tablas y más de 15 registros en cada una | `db/schema.sql`, `scripts/seed.py` |
| 3 PDF ficticios para el RAG | `data/docs/` (se regeneran con `scripts/build_pdfs.py`) |
| Agente con LangGraph (decide la fuente, genera y valida SQL, recupera fragmentos) | `src/telemetry_agent/graph.py` |
| Interfaz de chat con Streamlit | `app/streamlit_app.py` |
| Trazas y evaluación con LangSmith | `eval/run_eval.py`, variables `LANGSMITH_*` |
| Spec Driven Development con GitHub Spec Kit | `.specify/` y `specs/001-agente-sql-telemetria/` |
| Pruebas automáticas | `tests/` |

Criterios de promoción que cubre: SDD, framework agéntico (LangGraph), interfaz gráfica (Streamlit) y
observabilidad y evaluación (LangSmith). La base de datos puede alojarse en la nube (Supabase) o correr local
con Docker. Todo lo que muestra el informe se probó con la base local; la opción de Supabase está prevista en el
código pero no se probó. El despliegue del agente en la nube no está incluido: se ejecuta en la computadora de
quien lo usa.

## Requisitos

- Python 3.11 o superior.
- Una base PostgreSQL con la extensión pgvector: un proyecto de Supabase, o Docker para una base local.
- Una API key de Gemini (Google AI Studio). Se usa la capa gratuita.
- Una API key de LangSmith para las trazas (opcional, pero necesaria para el criterio de observabilidad).

## Instalación y ejecución

```bash
# 1. Entorno e instalación
python -m venv .venv
source .venv/bin/activate            # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# 2. Variables de entorno
cp .env.example .env                 # completar DATABASE_URL, DATABASE_URL_RO, GEMINI_API_KEY, LANGSMITH_API_KEY

# 3. Base de datos (elegir una)
docker compose up -d db              # opción local; o usar un proyecto de Supabase y su cadena de conexión
python scripts/setup_db.py           # crea tablas y el rol agent_ro de solo lectura
python scripts/seed.py               # carga los datos sintéticos (semilla fija, siempre los mismos)

# 4. Documentos para el RAG
python scripts/ingest_docs.py        # fragmenta los PDF, calcula embeddings y los guarda

# 5. Probar
python -m pytest                     # pruebas automáticas, no gastan cuota del modelo
streamlit run app/streamlit_app.py   # interfaz de chat
python -m telemetry_agent.cli "¿Cuántas alarmas críticas hubo en septiembre?"   # desde la terminal

# 6. Evaluar
python eval/run_eval.py --check-refs # valores de referencia, sin modelo
python eval/run_eval.py              # corre los 38 casos; el resultado queda en eval/results/
```

### Cargar los datos desde el volcado (alternativa al paso de seed e ingesta)

`db/dump/telemetria_datos.sql` tiene los datos de las 7 tablas y los fragmentos de los PDF con sus embeddings,
tal como quedaron en la evaluación. Sirve para ver los datos sin ejecutar nada y para cargar la base sin API key:

```bash
python scripts/setup_db.py           # crea las tablas vacías y el rol
docker compose exec -T db psql -U postgres -d telemetria < db/dump/telemetria_datos.sql
```

## Informe y evidencias

| Qué | Dónde |
|---|---|
| Informe técnico | `docs/informe/` |
| Capturas de la interfaz con el modelo real | `docs/informe/capturas/` |
| Resultado de la última evaluación | `eval/results/latest.md` (el detalle por caso está en el `.json` de la misma carpeta) |
| Casos de evaluación y respuestas esperadas | `eval/golden.jsonl` |

### Variables de entorno

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | Conexión con permisos de escritura. La usan solo `setup_db.py`, `seed.py` e `ingest_docs.py`. |
| `DATABASE_URL_RO` | Conexión del rol `agent_ro` (solo lectura). La usa el agente. Define la clave del rol. |
| `GEMINI_API_KEY` | Clave del modelo de lenguaje y de los embeddings. |
| `GEMINI_MODEL` | Modelo de chat. Por defecto `gemini-3.5-flash-lite`. |
| `GEMINI_EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS` | Embeddings. Por defecto `gemini-embedding-2` con 768 dimensiones. |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | Trazas en LangSmith. |
| `SQL_MAX_ROWS`, `SQL_TIMEOUT_MS`, `SQL_MAX_RETRIES`, `RETRIEVAL_TOP_K` | Límites del agente. |

## Cómo funciona

```text
pregunta
   |
[router]  decide: sql | docs | both | none | refuse
   |
[sql_generate] -> [sql_validate] -> [sql_execute]    (si falla, reintenta con el motivo, máximo 2 veces)
   |
[retrieve]  fragmentos de los PDF más cercanos (pgvector, distancia coseno)
   |
[synthesize]  respuesta en el idioma de la pregunta, solo con la evidencia, citando archivo y página
```

El agente es de solo lectura por cuatro capas independientes: el validador de SQL (`sql_guard.py`) solo acepta
un SELECT sobre las tablas permitidas, el rol `agent_ro` solo tiene permiso de lectura, la transacción se abre en
modo solo lectura y cada consulta tiene un timeout y un tope de filas.

La respuesta del agente tiene siempre la misma forma (`specs/001-agente-sql-telemetria/contracts/agent-response.md`):
respuesta, fuente elegida, consulta SQL, filas, fragmentos citados y si el pedido fue rechazado.

## Metodología (SDD)

Se usó GitHub Spec Kit. Los artefactos, en el orden en que se generaron:

1. `.specify/memory/constitution.md`: principios del proyecto.
2. `specs/001-agente-sql-telemetria/spec.md`: especificación, con su checklist en `checklists/requirements.md`.
3. `specs/001-agente-sql-telemetria/plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
4. `specs/001-agente-sql-telemetria/tasks.md`: tareas, marcadas a medida que se implementaron.

## Datos y documentos

Los datos y los PDF son ficticios y están hechos para este trabajo. Los PDF no deben usarse como guía en una
instalación real. Las fechas de los datos van del 2026-09-01 al 2026-09-30; el agente toma el 30 de septiembre
como "hoy".

## Problemas frecuentes

- **El proyecto de Supabase está pausado.** Los proyectos gratuitos se pausan tras una semana sin actividad.
  Reactivarlo desde el panel antes de usarlo, por ejemplo antes del coloquio.
- **`create extension vector` falla o no se encuentra el tipo `vector`.** Habilitar la extensión desde el panel de
  Supabase (Database, Extensions). Si quedó en el esquema `extensions`, escribir `extensions.vector(768)` en
  `db/schema.sql`.
- **No conecta a Supabase.** Probar con la cadena de conexión del pooler en lugar de la directa, o al revés.
- **Errores 429 o `RESOURCE_EXHAUSTED`.** Se alcanzó el límite de la capa gratuita de Gemini. El mensaje del agente
  indica si es el límite por minuto o el diario. La evaluación espera y reintenta sola ante el límite por minuto, y
  se detiene ante el diario. Límites observados el 2026-10-10: `gemini-3.5-flash` 5 pedidos por minuto y 20 por día;
  `gemini-3.5-flash-lite` 15 por minuto. Los límites vigentes se ven en https://ai.dev/rate-limit.
- **El nombre del modelo no existe.** Los nombres de los modelos cambian. Ver la lista vigente en la documentación
  de Gemini y ajustar `GEMINI_MODEL`.
- **`ingest_docs.py --fake`** usa embeddings falsos y solo sirve para probar el flujo sin API key. No usar para
  responder preguntas.
