# Implementation Plan: Agente SQL de Telemetría y Mantenimiento Industrial

**Branch**: `001-agente-sql-telemetria` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-agente-sql-telemetria/spec.md`

## Summary

Un agente que responde preguntas en castellano o inglés sobre una planta industrial ficticia.
Lee una base PostgreSQL de telemetría y mantenimiento mediante SQL generado por el modelo, y
consulta PDF de manuales y procedimientos mediante búsqueda vectorial. Un paso de decisión
elige la fuente en cada pregunta. Se orquesta como un grafo con LangGraph, se usa desde una
interfaz de chat en Streamlit y cada ejecución se traza en LangSmith. Un conjunto de evaluación
con verificaciones deterministas mide el resultado. Las decisiones y su evidencia están en
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11 o superior (se desarrolla y prueba con 3.13)

**Primary Dependencies**: langgraph, langchain-google-genai, google-genai, langsmith, streamlit,
psycopg 3, sqlglot, pypdf, reportlab (para generar los PDF), pydantic

**Storage**: PostgreSQL con pgvector (Supabase en la nube, o un Postgres local con docker compose)

**Testing**: pytest, con un modelo y un generador de embeddings falsos para las pruebas
automáticas; la evaluación con el modelo real se ejecuta aparte

**Target Platform**: Linux, macOS o Windows con Python; la base en la nube o local

**Project Type**: aplicación de una sola unidad (paquete Python más interfaz Streamlit y scripts)

**Performance Goals**: 90% de las respuestas en menos de 20 segundos (SC-006)

**Constraints**: capa gratuita del modelo (pocas llamadas por pregunta, reintentos con espera);
solo lectura sobre la base; datos y documentos ficticios; sin secretos en el repositorio

**Scale/Scope**: 7 tablas de negocio (unas 39.400 filas en total, de las cuales 38.880 son lecturas), 3 PDF, unos 25 casos de
evaluación, un usuario por vez

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple en este plan | Estado |
|---|---|---|
| I. Solo lectura | Validador sqlglot, rol `agent_ro` con solo SELECT, transacción de solo lectura, timeout y tope de filas (research D5) | Cumple |
| II. Respuestas fundadas | La síntesis recibe solo filas y fragmentos recuperados; si no hay evidencia responde que no sabe; la respuesta incluye fuente, archivo y página (contrato) | Cumple |
| III. Decisión de fuente explícita | Nodo `router` propio en el grafo; su salida se guarda en el estado y en la traza | Cumple |
| IV. Reproducibilidad | `requirements.txt` con versiones fijas, `schema.sql` y seed con semilla, `.env.example`, README con quickstart | Cumple |
| V. Evaluación y observabilidad | `eval/golden.jsonl` cubre cada comportamiento; trazas con LangSmith; la evaluación se corre con un comando | Cumple |
| VI. Simplicidad defendible | Un solo motor de datos para SQL y vectores; verificaciones deterministas; sin capas extra | Cumple |

Después del diseño (Phase 1) se vuelve a revisar: sin cambios. Sin violaciones, así que no
hace falta la tabla de complejidad.

## Arquitectura del agente

```text
pregunta + historial
        |
     [router]  ->  decide: sql | docs | both | none
        |
   +----+-----------------+
   |                      |
[sql_generate]        [retrieve]
   |                      |
[sql_validate]  -- inválida o con error, reintenta (máx. 2) -->
   |
[sql_execute]
   |                      |
   +----------+-----------+
              |
        [synthesize]  -> respuesta + fuente + detalle
```

- **router**: una llamada al modelo con salida estructurada. Recibe la pregunta y el historial
  reciente, y devuelve la ruta y una justificación corta.
- **sql_generate**: recibe la descripción del esquema (armada desde `COMMENT ON`) y la pregunta.
  Devuelve una única consulta.
- **sql_validate**: el validador de la constitución (principio I). Si rechaza, el motivo vuelve a
  `sql_generate` como contexto para reintentar, con un máximo de 2 reintentos.
- **sql_execute**: ejecuta con el rol de solo lectura, con tope de filas y de tiempo.
- **retrieve**: embebe la pregunta y trae los 4 fragmentos más cercanos por distancia coseno.
- **synthesize**: redacta la respuesta en el idioma de la pregunta usando solo la evidencia. Si no
  hay filas ni fragmentos útiles, responde que no tiene la información.
- Llamadas al modelo por pregunta: router, generación de SQL (1 a 3) y síntesis, es decir 3 a 5
  en el peor caso. En la ruta `none` son 2.

El historial de la conversación se guarda por hilo en la memoria del grafo, que es lo que permite
las preguntas de seguimiento (FR-011).

## Project Structure

### Documentation (this feature)

```text
specs/001-agente-sql-telemetria/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── agent-response.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
.
├── README.md
├── .env.example
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml          # Postgres con pgvector local, opcional
├── db/
│   ├── schema.sql              # tablas, comentarios, doc_chunks
│   └── roles.sql               # rol agent_ro de solo lectura
├── scripts/
│   ├── setup_db.py             # crea esquema y rol de solo lectura
│   ├── seed.py                 # datos sintéticos con semilla fija
│   ├── build_pdfs.py           # genera los PDF ficticios
│   └── ingest_docs.py          # PDF -> fragmentos -> embeddings -> doc_chunks
├── data/
│   └── docs/                   # los PDF
├── src/telemetry_agent/
│   ├── config.py               # variables de entorno
│   ├── db.py                   # conexiones y ejecución de solo lectura
│   ├── sql_guard.py            # validador de SQL
│   ├── schema_context.py       # descripción del esquema para el modelo
│   ├── llm.py                  # modelo de lenguaje y su versión falsa para pruebas
│   ├── embeddings.py           # embeddings y su versión falsa para pruebas
│   ├── retriever.py            # búsqueda de fragmentos
│   ├── prompts.py
│   ├── models.py               # tipos y contrato de respuesta
│   ├── graph.py                # el grafo de LangGraph
│   └── cli.py                  # preguntar desde la terminal
├── app/
│   └── streamlit_app.py
├── eval/
│   ├── golden.jsonl
│   └── run_eval.py
├── tests/
│   ├── test_sql_guard.py
│   ├── test_seed_integrity.py
│   ├── test_chunking.py
│   ├── test_readonly_db.py
│   ├── test_graph_routing.py   # con modelo falso
│   ├── test_graph_sql.py
│   ├── test_graph_docs.py
│   ├── test_streamlit_app.py
│   └── test_eval_helpers.py
└── docs/
    └── informe/                # informe técnico (máx. 10 páginas)
```

**Structure Decision**: un solo paquete Python con una carpeta de interfaz y otra de
evaluación. No hay servidor aparte porque la interfaz Streamlit llama directamente al grafo.
Mantiene el sistema chico, que es lo que exige el principio VI.

## Complexity Tracking

Sin violaciones de la constitución. Se deja anotada una decisión que podría parecer extra:
`docker-compose.yml` con Postgres local. Se justifica por el principio IV: permite reproducir el
proyecto sin cuenta en la nube y sirve de respaldo si el proyecto gratuito de Supabase está
pausado el día del coloquio (research D3).
