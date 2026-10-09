---

description: "Lista de tareas del Agente SQL de Telemetría y Mantenimiento Industrial"
---

# Tasks: Agente SQL de Telemetría y Mantenimiento Industrial

**Input**: documentos de diseño en `/specs/001-agente-sql-telemetria/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/agent-response.md

**Tests**: se incluyen porque la constitución (principio V) exige que todo comportamiento tenga un caso de prueba o de evaluación.

**Organization**: las tareas se agrupan por historia de usuario, así cada una se puede implementar y probar por separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencia pendiente)
- **[Story]**: historia de usuario a la que pertenece (US1 a US5)

## Phase 1: Setup

- [X] T001 Crear la estructura de carpetas del plan en la raíz del repositorio
- [X] T002 Crear `requirements.txt` con versiones fijas y `.env.example` con todas las variables en `.env.example`
- [X] T003 [P] Crear `.gitignore` (excluye `.env`, entornos virtuales y cachés) en `.gitignore`
- [X] T004 [P] Crear `docker-compose.yml` con Postgres y pgvector local en `docker-compose.yml`

---

## Phase 2: Foundational (bloquea todas las historias)

**Checkpoint**: base creada, poblada y documentos cargados; las historias pueden empezar.

- [X] T005 Escribir el esquema con claves foráneas y `COMMENT ON` en castellano, y la tabla `doc_chunks` en `db/schema.sql`
- [X] T006 Crear el rol `agent_ro` con solo SELECT sobre las tablas permitidas en `db/roles.sql`
- [X] T007 Implementar la lectura de variables de entorno en `src/telemetry_agent/config.py`
- [X] T008 Implementar conexiones y ejecución de solo lectura con timeout y tope de filas en `src/telemetry_agent/db.py`
- [X] T009 Implementar el generador de datos sintéticos con semilla fija en `scripts/seed.py`
- [X] T010 [P] Escribir pruebas de integridad del seed (conteos, claves foráneas, umbrales, coherencia de alarmas) en `tests/test_seed_integrity.py`
- [X] T011 [P] Generar los 3 PDF ficticios coherentes con los códigos de equipo en `scripts/build_pdfs.py` y `data/docs/`
- [X] T012 Implementar la interfaz de embeddings y su versión falsa en `src/telemetry_agent/embeddings.py`
- [X] T013 Implementar la interfaz del modelo de lenguaje y su versión falsa en `src/telemetry_agent/llm.py`
- [X] T014 [P] Implementar el validador de SQL en `src/telemetry_agent/sql_guard.py`
- [X] T015 [P] Escribir pruebas del validador (UPDATE, DELETE, DROP, múltiples sentencias, tablas no permitidas, SELECT válido) en `tests/test_sql_guard.py`
- [X] T016 Implementar la ingesta de PDF (extraer por página, fragmentar, embeber, guardar) en `scripts/ingest_docs.py`
- [X] T017 [P] Escribir pruebas de fragmentación que conserven archivo y página en `tests/test_chunking.py`

---

## Phase 3: User Story 1 - Consultar datos de operación y mantenimiento (P1)

**Goal**: responder preguntas sobre datos con SQL generado por el modelo.

**Independent Test**: preguntas con respuesta conocida contra la base poblada.

- [X] T018 [US1] Implementar la descripción del esquema para el modelo a partir de los comentarios en `src/telemetry_agent/schema_context.py`
- [X] T019 [US1] Escribir los prompts de generación de SQL y de síntesis en `src/telemetry_agent/prompts.py`
- [X] T020 [US1] Implementar los nodos `sql_generate`, `sql_validate`, `sql_execute` con reintentos acotados y el nodo `synthesize` en `src/telemetry_agent/graph.py`
- [X] T021 [US1] Implementar la consulta desde terminal en `src/telemetry_agent/cli.py`
- [X] T022 [US1] Escribir pruebas del camino SQL con modelo falso, incluido el rechazo de pedidos de escritura, en `tests/test_graph_sql.py`

---

## Phase 4: User Story 2 - Consultar manuales y procedimientos (P2)

**Goal**: responder con contenido de los PDF citando archivo y página.

**Independent Test**: preguntas con respuesta en un pasaje conocido.

- [X] T023 [US2] Implementar la búsqueda de fragmentos por distancia coseno en `src/telemetry_agent/retriever.py`
- [X] T024 [US2] Agregar el nodo `retrieve` y la regla de "no tengo la información" al grafo en `src/telemetry_agent/graph.py`
- [X] T025 [US2] Escribir pruebas del camino de documentos con embeddings falsos y de la respuesta sin evidencia en `tests/test_graph_docs.py`

---

## Phase 5: User Story 3 - Preguntas combinadas (P3)

**Goal**: el agente decide la fuente y combina ambas cuando hace falta.

**Independent Test**: una pregunta que depende de un dato y un procedimiento.

- [X] T026 [US3] Implementar el nodo `router` con salida estructurada y registro de la decisión en `src/telemetry_agent/graph.py`
- [X] T027 [US3] Conectar las rutas `sql`, `docs`, `both` y `none` y el contexto de conversación por hilo en `src/telemetry_agent/graph.py`
- [X] T028 [US3] Escribir pruebas de enrutamiento para las cuatro rutas en `tests/test_graph_routing.py`

---

## Phase 6: User Story 4 - Interfaz de chat (P4)

**Goal**: usar el agente desde una interfaz web.

**Independent Test**: abrir la interfaz y preguntar una cosa de cada tipo.

- [X] T029 [US4] Implementar el chat con paneles desplegables de fuente, consulta y fragmentos en `app/streamlit_app.py`
- [X] T030 [US4] Manejar errores del servicio del modelo y de la base mostrando un mensaje claro en `app/streamlit_app.py`

---

## Phase 7: User Story 5 - Seguimiento y evaluación (P5)

**Goal**: ver el recorrido de cada pregunta y medir el resultado.

**Independent Test**: correr la evaluación y revisar las trazas.

- [X] T031 [US5] Activar el trazado con LangSmith mediante variables de entorno y documentarlo en `src/telemetry_agent/config.py`
- [X] T032 [US5] Escribir los casos de evaluación (datos, documentos, combinadas, rechazo, sin respaldo, inglés, seguimiento) en `eval/golden.jsonl`
- [X] T033 [US5] Implementar el evaluador con verificaciones deterministas y reporte por caso y total en `eval/run_eval.py`

---

## Phase 8: Polish y entrega

- [X] T034 Escribir el README con instalación, ejecución y variables en `README.md`
- [X] T035 Redactar el informe técnico (máx. 10 páginas) como documento en línea; la evidencia de la corrida real con Gemini y LangSmith queda marcada como pendiente en el informe
- [X] T036 Verificar cada criterio contra lo que se pudo probar sin API key y marcar en el informe lo que falta (evaluación con modelo real, capturas, trazas)
- [X] T037 Revisar que el repositorio no contenga secretos y que los artefactos SDD estén completos en `.specify/` y `specs/`

---

---

## Phase 9: Tareas agregadas durante la implementación

Surgieron al implementar y se registraron acá antes de hacerlas, como pide la constitución.

- [X] T038 Crear el esquema y el rol de solo lectura con un solo comando en `scripts/setup_db.py`
- [X] T039 [P] Hacer instalable el paquete y configurar pytest en `pyproject.toml`
- [X] T040 [P] Probar que el rol agent_ro no puede escribir aunque falle el validador, y que el timeout y el tope de filas funcionan, en `tests/test_readonly_db.py`
- [X] T041 [P] Probar la interfaz con un agente de mentira en `tests/test_streamlit_app.py`
- [X] T042 [P] Probar las verificaciones del evaluador en `tests/test_eval_helpers.py`
- [X] T043 Definir la zona horaria de la planta y aplicarla en cada consulta (se detectó que la fecha de referencia salía un día corrida) en `src/telemetry_agent/config.py` y `src/telemetry_agent/db.py`
- [X] T044 Definir los tipos compartidos y el contrato de respuesta en `src/telemetry_agent/models.py`

---

## Dependencies & Execution Order

- Setup, luego Foundational, que bloquea todo lo demás.
- US1 antes que US2 y US3 porque comparte el grafo; US3 depende de US1 y US2.
- US4 y US5 dependen de que exista el grafo (US1 a US3).
- Polish al final.

## Implementation Strategy

1. Terminar Setup y Foundational.
2. Entregar US1 como primer incremento usable y probarlo.
3. Sumar US2 y US3.
4. Sumar la interfaz y la evaluación.
5. Cerrar con README, informe y verificación.
