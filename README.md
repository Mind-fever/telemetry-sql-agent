# Agente SQL de telemetría y mantenimiento industrial

Trabajo Práctico Integrador de AI Engineering. Ingeniería en Informática, 5to año, UCSE Sede Rafaela.
Autor: Santiago Nicolas Martinez (trabajo individual).

Un agente de IA que responde preguntas en castellano o inglés sobre una planta industrial ficticia.
Consulta una base de datos relacional con SQL que genera el modelo y busca en manuales en PDF con RAG.
En cada pregunta decide por sí mismo qué fuente usar: la base, los documentos, ambas o ninguna.
Solo lee: nunca modifica la base.

## Qué incluye

| Pieza | Dónde |
|---|---|
| Base relacional con 7 tablas y más de 15 registros en cada una | `db/schema.sql`, `scripts/seed.py`, `db/dump/` |
| 3 PDF ficticios para el RAG | `data/docs/` (se regeneran con `scripts/build_pdfs.py`) |
| Agente con LangGraph (decide la fuente, genera y valida SQL, recupera fragmentos) | `src/telemetry_agent/graph.py` |
| Interfaz de chat con Streamlit | `app/streamlit_app.py` |
| Trazas y evaluación con LangSmith | `eval/run_eval.py`, `eval/run_langsmith_experiment.py` |
| Spec Driven Development con GitHub Spec Kit | `.specify/` y `specs/001-agente-sql-telemetria/` |
| Pruebas automáticas | `tests/` |
| Informe técnico y capturas | `docs/informe/` |

Criterios de promoción que cubre: SDD, framework agéntico (LangGraph), interfaz gráfica (Streamlit) y
observabilidad y evaluación (LangSmith). El despliegue en la nube no está incluido: el agente y la base corren
en la computadora de quien lo usa.

## Resultado de la evaluación

Última corrida, 12 de octubre de 2026, con `gemini-3.5-flash-lite`: 39 de 39 casos aprobados, tanto con
`eval/run_eval.py` como en el experimento de LangSmith. El detalle está en `eval/results/latest.md`.
Las pruebas automáticas son 98 y pasan todas.

El modelo no responde siempre igual, así que el resultado puede variar entre corridas. El historial de las
corridas anteriores, con los errores que se encontraron y corrigieron, está en `eval/results/` y en el informe.

## Requisitos

- Python 3.11 o superior (se desarrolló y probó con 3.13).
- Docker, para levantar la base PostgreSQL con la extensión pgvector.
- Una API key de Gemini (Google AI Studio). Alcanza con la capa gratuita.
- Una API key de LangSmith para las trazas y el experimento. Sin ella el agente funciona igual, pero no deja trazas.

## Instalación y ejecución

Los comandos son los mismos en Windows, Linux y macOS, salvo la activación del entorno.

```bash
# 1. Entorno e instalación
python -m venv .venv
.venv\Scripts\activate               # Windows. En Linux y macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. Variables de entorno
cp .env.example .env                 # completar GEMINI_API_KEY y LANGSMITH_API_KEY (en cmd de Windows: copy)

# 3. Base de datos
docker compose up -d db              # PostgreSQL 16 con pgvector, en el puerto 5432
python scripts/setup_db.py           # crea las tablas y el rol agent_ro de solo lectura
python scripts/seed.py               # carga los datos sintéticos (semilla fija, siempre los mismos)

# 4. Documentos para el RAG
python scripts/ingest_docs.py        # fragmenta los PDF, calcula los embeddings y los guarda

# 5. Probar
python -m pytest                     # pruebas automáticas, no gastan cuota del modelo
streamlit run app/streamlit_app.py   # interfaz de chat
python -m telemetry_agent.cli "¿Cuántas alarmas críticas hubo en septiembre?"   # desde la terminal

# 6. Evaluar
python eval/run_eval.py --check-refs        # valores de referencia, sin modelo
python eval/run_eval.py                     # corre los 39 casos; el resultado queda en eval/results/
python eval/run_langsmith_experiment.py     # los mismos casos como experimento de LangSmith
```

Los valores de `DATABASE_URL` y `DATABASE_URL_RO` que trae `.env.example` ya sirven para la base de Docker.

### Cargar los datos desde el volcado

`db/dump/telemetria_datos.sql` tiene los datos de las 7 tablas y los 18 fragmentos de los PDF con sus embeddings,
tal como quedaron en la evaluación. Sirve para revisar los datos sin ejecutar nada y para cargar la base sin
API key. Reemplaza a los pasos de `seed.py` e `ingest_docs.py`:

```bash
python scripts/setup_db.py           # crea las tablas vacías y el rol
docker compose cp db/dump/telemetria_datos.sql db:/tmp/telemetria_datos.sql
docker compose exec -T db psql -U postgres -d telemetria -f /tmp/telemetria_datos.sql
```

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

El archivo `.env` no se sube al repositorio.

## Cómo funciona

```text
pregunta
   |
[router]  decide: sql | docs | both | none | refuse
   |        (none y refuse responden directo, sin consultar ninguna fuente)
   |
[sql_generate] -> [sql_validate] -> [sql_execute]    (si falla, reintenta con el motivo, máximo 2 veces)
   |
[retrieve]  fragmentos de los PDF más cercanos (pgvector, distancia coseno)
   |
[synthesize]  respuesta en el idioma de la pregunta, solo con la evidencia, citando archivo y página
```

La ruta `sql` usa los pasos de SQL y la síntesis. La ruta `docs` usa la recuperación y la síntesis. La ruta
`both` usa todos.

El agente es de solo lectura por cuatro capas independientes: el validador de SQL (`sql_guard.py`) solo acepta
un SELECT sobre las tablas permitidas, el rol `agent_ro` solo tiene permiso de lectura, la transacción se abre en
modo solo lectura y cada consulta tiene un timeout y un tope de filas.

La respuesta del agente tiene siempre la misma forma (`specs/001-agente-sql-telemetria/contracts/agent-response.md`):
respuesta, fuente elegida, consulta SQL, filas, fragmentos citados y si el pedido fue rechazado.

## Evaluación

`eval/golden.jsonl` tiene 39 casos: preguntas de datos, de documentos, combinadas, pedidos de escritura que deben
rechazarse, preguntas sin respaldo, preguntas que no necesitan fuente, casos borde y una de seguimiento.

Las verificaciones son deterministas, sin un modelo que haga de juez. Para las preguntas de datos, el evaluador
ejecuta una consulta de referencia y compara su resultado con el del agente. Para las de documentos, comprueba
el archivo y la página citados.

- `eval/run_eval.py` corre los casos y deja el resultado en `eval/results/`. Si LangSmith está configurado,
  cada ejecución queda trazada con su resultado.
- `eval/run_langsmith_experiment.py` sube los casos a LangSmith como conjunto de datos y corre el agente como
  un experimento, con las mismas verificaciones. El resultado se ve en "Datasets & Experiments".

## Metodología (SDD)

Se usó GitHub Spec Kit. Los artefactos, en el orden en que se generaron:

1. `.specify/memory/constitution.md`: principios del proyecto.
2. `specs/001-agente-sql-telemetria/spec.md`: especificación, con su checklist en `checklists/requirements.md`.
3. `specs/001-agente-sql-telemetria/plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
4. `specs/001-agente-sql-telemetria/tasks.md`: tareas, marcadas a medida que se implementaron. Las fases 9 a 11
   son tareas que surgieron durante la implementación y las corridas reales, cada una con su motivo.

## Informe y evidencias

| Qué | Dónde |
|---|---|
| Informe técnico (PDF y Word) | `docs/informe/` |
| Capturas de la interfaz y de una traza de LangSmith | `docs/informe/capturas/` |
| Resultado de la última evaluación | `eval/results/latest.md` (el detalle por caso está en el `.json` de la misma carpeta) |
| Casos de evaluación y respuestas esperadas | `eval/golden.jsonl` |
| Guía de los datos y de la demostración | `docs/guia-demo.md` |
| Enunciado del trabajo | `docs/Enunciado.pdf` |

## Datos y documentos

Los datos y los PDF son ficticios y están hechos para este trabajo. Los PDF no deben usarse como guía en una
instalación real. Las fechas de los datos van del 2026-09-01 al 2026-09-30; el agente toma el 30 de septiembre
como "hoy".

## Base de datos en la nube

El agente se conecta por `DATABASE_URL`, así que en principio sirve cualquier PostgreSQL con pgvector, por ejemplo
un proyecto de Supabase. Esa opción no se probó: todo el desarrollo, las pruebas y la evaluación se hicieron con
la base local de Docker.

## Problemas frecuentes

- **`docker compose up` falla con un error de conexión al motor de Docker.** Docker Desktop está cerrado. Abrirlo,
  esperar a que termine de iniciar y volver a correr el comando.
- **Errores 429 o `RESOURCE_EXHAUSTED`.** Se alcanzó el límite de la capa gratuita de Gemini. El mensaje del agente
  indica si es el límite por minuto o el diario. La evaluación espera y reintenta sola ante el límite por minuto, y
  se detiene ante el diario. Límites observados el 2026-10-10: `gemini-3.5-flash` 5 pedidos por minuto y 20 por día;
  `gemini-3.5-flash-lite` 15 por minuto. Los límites vigentes se ven en https://ai.dev/rate-limit.
- **Las preguntas sobre documentos responden "no tengo esa información".** Revisar que `ingest_docs.py` haya
  informado 18 fragmentos cargados. Si usó `--fake`, los embeddings son falsos y hay que volver a correrlo sin esa
  opción.
- **El nombre del modelo no existe.** Los nombres de los modelos cambian. Ver la lista vigente en la documentación
  de Gemini y ajustar `GEMINI_MODEL`.
