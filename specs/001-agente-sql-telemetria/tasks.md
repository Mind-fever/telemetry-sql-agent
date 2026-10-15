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

## Phase 10: Tareas agregadas tras la primera corrida con el modelo real (2026-10-10)

La primera evaluación con Gemini real dio 4/35: los 31 casos restantes fallaron por el mismo error
(429, cuota de la capa gratuita). Los límites leídos del error fueron 5 pedidos por minuto y 20 por
día para el modelo configurado, y la evaluación completa necesita unas 90 llamadas. Ninguna tarea
de esta fase cambia las respuestas esperadas de `eval/golden.jsonl`.

- [X] T045 Distinguir el límite diario del límite por minuto en el mensaje de error de cuota (antes decía siempre "probá de nuevo en un minuto") en `src/telemetry_agent/graph.py`, con su prueba en `tests/test_graph_routing.py`
- [X] T046 Hacer que la evaluación espere y reintente el caso ante el límite por minuto, y que se detenga ante el límite diario sin contar como fallados los casos no ejecutados, en `eval/run_eval.py`. El reintento por minuto se vio funcionar en la corrida real del 2026-10-10 (caso sql-13); el corte por límite diario no tiene prueba automática ni se ejercitó en una corrida real
- [X] T047 Registrar en el reporte de la evaluación el modelo usado y si la corrida fue completa en `eval/run_eval.py`, con su prueba en `tests/test_eval_helpers.py`
- [X] T048 Elegir un modelo de la capa gratuita cuya cuota alcance para la evaluación completa, verificarlo con una corrida real y actualizar el valor por defecto en `.env.example`, `src/telemetry_agent/config.py`, `README.md` y `research.md` (D1)
- [X] T049 Correr la evaluación completa con el modelo real y dejar el resultado en `eval/results/`. Tercera corrida, 2026-10-11: 33/35 (94,3%) con `gemini-3.5-flash-lite`, los seis criterios SC-001 a SC-006 cumplen; fallan sql-05 y sql-10

La segunda corrida (modelo `gemini-3.5-flash-lite`, 35 de 35 casos ejecutados) dio 22/35. Las
tareas que siguen corrigen las causas encontradas en esa corrida.

- [X] T050 Corregir el cálculo de embeddings por lotes: `gemini-embedding-2` devolvía un solo vector para toda la lista de textos, así que la ingesta guardó 2 fragmentos en vez de 18. Enviar cada texto como contenido separado y fallar si la cantidad de vectores no coincide, en `src/telemetry_agent/embeddings.py` y `scripts/ingest_docs.py`, con su prueba en `tests/test_embeddings.py` (casos doc-01 a doc-07, both-02, both-03)
- [X] T051 Volver a ingestar los PDF y comprobar que `doc_chunks` tiene los 18 fragmentos
- [X] T052 Agregar al prompt de generación de SQL dos reglas: en preguntas combinadas traer los datos del hecho y no el procedimiento, y no reemplazar un dato que el esquema no tiene por otra columna; y al prompt de síntesis, no presentar una columna como si fuera otro dato, en `src/telemetry_agent/prompts.py` (casos both-01 y noev-03)
- [X] T053 Ajustar el prompt del router para que una pregunta sobre la planta sin respaldo conocido se busque en una fuente en vez de responderse directo, en `src/telemetry_agent/prompts.py` (caso noev-01)

La tercera corrida dio 33/35. Las tareas que siguen corrigen las dos causas que quedaron.

- [X] T054 Pasar al paso de síntesis la consulta SQL ejecutada, para que sepa qué filtros ya cumplen las filas (en sql-05 respondía que no conocía el estado de los equipos porque el filtro estaba en el WHERE y no en las columnas), en `src/telemetry_agent/graph.py` y `src/telemetry_agent/prompts.py`, con su prueba en `tests/test_graph_sql.py`
- [X] T055 Hacer que el evaluador compare textos sin distinguir tildes (en sql-10 marcaba como incorrecta la respuesta "vibración" porque la base guarda "vibracion"), en `eval/run_eval.py`, con su prueba en `tests/test_eval_helpers.py`. No cambia ninguna respuesta esperada de `eval/golden.jsonl`
- [X] T056 Volver a correr la evaluación completa y dejar el resultado en `eval/results/`. Cuarta corrida, 2026-10-11: 35/35 con `gemini-3.5-flash-lite`, los seis criterios SC-001 a SC-006 cumplen

- [X] T057 Probar la interfaz de Streamlit con el modelo real (una pregunta de datos, una de documentos, una combinada y un pedido de escritura) en `app/streamlit_app.py`. Hecho el 2026-10-11: las cuatro respondieron bien, las capturas están en `docs/informe/capturas/` y la tabla `alarmas` siguió con 171 filas después del pedido de borrado
- [X] T058 Actualizar el informe con la evidencia de las corridas reales (resultado de la evaluación, respuestas del agente, límites de la capa gratuita, errores encontrados y su corrección). Queda pendiente una captura de pantalla de una traza de LangSmith, que se toma desde la cuenta

---

## Phase 11: Revisión final contra el enunciado (2026-10-12)

Surgieron al revisar cada criterio del enunciado contra el repositorio y la base.

- [X] T059 Enmendar la constitución: la restricción técnica decía "PostgreSQL en Supabase" y todas las corridas se hicieron con el Postgres local de Docker. Corregir también la suposición de `spec.md` que decía que la base ya vivía en la nube y la decisión D3 de `research.md`
- [X] T060 Corregir datos viejos de los artefactos: estado "Draft" en `spec.md` y "unos 25 casos" en `plan.md`
- [X] T061 Cubrir con casos de evaluación tres casos borde de la especificación que no tenían ninguno (equipo que no existe, pregunta ambigua, resultado recortado), como exige el principio V. Incluye: regla en el prompt del router para pedir precisión ante una pregunta ambigua, quitar del prompt de SQL el `LIMIT 50` (impedía que el sistema detectara y avisara el recorte), verificación `expect_truncated` en `eval/run_eval.py` con su prueba, y tres casos nuevos en `eval/golden.jsonl` sin cambiar los existentes
- [X] T062 Agregar al repositorio un volcado SQL de los datos (entregable "datos empleados: bases de datos") en `db/dump/` y documentarlo en `README.md`
- [X] T063 Indicar en `README.md` dónde están el informe, las capturas y el resultado de la evaluación
- [X] T064 Correr la evaluación completa con los casos nuevos, actualizar el informe y versionar los cambios en la rama `001-agente-sql-telemetria`. Quinta corrida, 2026-10-12: 38/38 con `gemini-3.5-flash-lite`. El informe quedó en 8 páginas (`docs/informe/informe.pdf`)

- [X] T065 Agregar al informe la captura de una traza de LangSmith y el nombre del autor, y volver a generar el PDF. El PDF quedó en 9 páginas sin la portada
- [X] T066 Usar la evaluación propia de LangSmith además del script local: subir los 38 casos como conjunto de datos y correr el agente como un experimento, con las mismas verificaciones deterministas, en `eval/run_langsmith_experiment.py`. Refuerza el criterio de promoción "observabilidad y evaluación". Corrida del 2026-10-12: experimento `gemini-3.5-flash-lite-df68c2a4`, 38/38

- [X] T067 Corregir inconsistencias entre los artefactos y el código encontradas en la revisión final: el contrato y el diagrama del plan nombraban 4 rutas y el router tiene 5 (faltaba `refuse`); `data-model.md` escribía el turno "mañana" y la base guarda `manana`; la estructura de carpetas del plan no incluía los archivos agregados en las fases 10 y 11

- [X] T068 Revisar el README completo: quitar los consejos sobre Supabase, que nunca se probó; dar los comandos de instalación para Windows además de Linux y macOS; ordenar las secciones; agregar el resultado de la evaluación; y probar el comando de carga del volcado en una base aparte antes de documentarlo

---

## Phase 12: Revisión del proceso SDD con el autor (2026-10-12)

Al revisar cómo se había usado Spec Kit se encontró lo siguiente. Spec Kit se instaló con su
instalador oficial y los artefactos de las fases 1 a 8 se escribieron siguiendo sus plantillas y
las instrucciones de cada comando, pero de corrido: sin ejecutar los comandos, sin la etapa de
aclaración (`clarify`), sin el análisis de consistencia (`analyze`) y sin que el autor revisara
cada etapa antes de pasar a la siguiente. Esta fase hace esa revisión, con los comandos reales y
con las decisiones del autor.

- [X] T069 Revisar la constitución con el autor. Decisión: enmendar el principio V para que un comportamiento que no se puede provocar a propósito con el modelo real quede cubierto por una prueba automática (versión 1.2.0)
- [X] T070 Aclarar en `research.md` cómo se verificaron las fuentes de la etapa de plan
- [X] T071 Ejecutar `speckit-clarify` sobre `spec.md` y registrar las respuestas del autor. Hecho el 2026-10-12: 5 preguntas, todas respondidas por el autor; las 5 confirmaron el comportamiento existente y 2 quitaron una ambigüedad del texto (pregunta ambigua y tope de filas)
- [X] T072 Ejecutar `speckit-analyze` sobre spec, plan y tareas, y decidir con el autor qué hallazgos se corrigen. Hecho el 2026-10-12: 10 hallazgos (1 crítico, 1 alto, 4 medios, 4 bajos), cobertura de requisitos 23 de 24. El autor decidió corregir todos

Tareas que salen del análisis:

- [X] T073 Corregir `spec.md`: dos escenarios de aceptación preguntaban por "el mes pasado" y la base solo tiene datos de septiembre (F1); la entidad "Planta" no existe en la base y faltaba "Área" (F2); el reintento de SQL no decía cuántas veces (B1); el aviso de error no decía qué debe indicar (B2)
- [X] T074 Reescribir SC-007 por decisión del autor: pedía que un tercero instalara el sistema en menos de 30 minutos, algo que un trabajo individual no puede medir. Pasa a exigir que el proyecto se levante desde cero siguiendo solo el README, que es lo que se verificó el 2026-10-10 (E1)
- [X] T075 Actualizar `plan.md` y `tasks.md`: la síntesis recibe también la consulta ejecutada (F3), la revisión de la constitución no mencionaba las enmiendas (F4) y el orden de ejecución no mencionaba las fases 9 a 12 (F5)
- [X] T076 Verificar con un caso de evaluación que el agente no contesta preguntas ajenas a la planta, como exige el principio V (D1): caso nuevo `edge-04` y verificación `answer_excludes` en `eval/run_eval.py`, con su prueba. No se toca ningún caso existente
- [X] T077 Agregar una prueba automática del manejo de cuota de la evaluación (reintento ante el límite por minuto, corte ante el diario), que no tenía ninguna (C1), en `eval/run_eval.py` y `tests/test_eval_helpers.py`
- [X] T078 Correr la evaluación completa con el caso nuevo, actualizar el informe y publicar. Sexta corrida, 2026-10-12: 39/39 con `gemini-3.5-flash-lite`, y 39/39 en el experimento de LangSmith `gemini-3.5-flash-lite-49276dc0`. Pruebas automáticas: 98. El informe quedó en 10 páginas con portada

Repaso del plan. El 12 y el 13 de octubre el autor repasó una por una las ocho decisiones técnicas de
`research.md` (modelo, embeddings, base de datos, LangGraph, capas de solo lectura, evaluación,
LangSmith y Streamlit). No pidió cambiar ninguna, así que no generó tareas de código.

- [X] T079 Escribir una guía de los datos y de la demostración, con el contenido real de cada tabla y de cada PDF y con preguntas probadas con el modelo real, en `docs/guia-demo.md`

---

## Dependencies & Execution Order

- Setup, luego Foundational, que bloquea todo lo demás.
- US1 antes que US2 y US3 porque comparte el grafo; US3 depende de US1 y US2.
- US4 y US5 dependen de que exista el grafo (US1 a US3).
- Polish al final.
- Las fases 9 a 12 se agregaron después, en orden: 9 durante la implementación, 10 tras la primera
  corrida con el modelo real, 11 en la revisión contra el enunciado y 12 en la revisión del proceso
  con el autor. Cada una depende de la anterior.

## Implementation Strategy

1. Terminar Setup y Foundational.
2. Entregar US1 como primer incremento usable y probarlo.
3. Sumar US2 y US3.
4. Sumar la interfaz y la evaluación.
5. Cerrar con README, informe y verificación.

## Phase 13: Convergence

- [X] T080 CRITICAL Agregar un caso de evaluación por cada comportamiento nuevo (período sin datos, unidad de medida, evolución por día) en `eval/golden.jsonl`, sin modificar los casos existentes per Constitution V (missing)
- [X] T081 Aclarar en la respuesta qué período cubren los datos cuando la pregunta se refiere a un período sin datos, en `src/telemetry_agent/prompts.py` per FR-017 (missing)
- [X] T082 Incluir la unidad de medida cuando la respuesta es un valor medido por un sensor, en `src/telemetry_agent/prompts.py` per FR-018 (missing)
- [X] T083 Responder los pedidos de evolución de una magnitud con un resumen por día (promedio y máximo) en lugar de las lecturas individuales, en `src/telemetry_agent/prompts.py` per FR-019 (missing)
- [X] T084 Actualizar el informe, el README y la guía con los requisitos nuevos y con el resultado de la evaluación después de los cambios per SC-008 (partial)
- [X] T085 Revisar si `.claude/launch.json` debe quedar en el repositorio: es una configuración de desarrollo que ningún artefacto pide per plan: Project Structure (unrequested)

Resultado de la fase 13 (2026-10-13). Evaluación con 42 casos: 42 de 42 en dos corridas seguidas
(`eval/results/20261013-204127.json` y `20261013-205335.json`). En la primera el servicio del modelo
respondió lento durante unos minutos y el percentil 90 de tiempo fue de 17,6 s; en la segunda fue de
4,8 s. El experimento de LangSmith `gemini-3.5-flash-lite-e1bd90ed` dio 41 de 42: en `both-02` la
respuesta fue correcta, pero la consulta devolvió una fila por alarma en vez del conteo. Pruebas
automáticas: 100. `.claude/launch.json` se quitó del repositorio (T085).

Tarea agregada por decisión del autor después de ver el resultado de la fase 13:

- [X] T086 Hacer que una pregunta que pide una cantidad ("cuántas") devuelva el conteo en una sola fila, y no una fila por cada elemento contado, en `src/telemetry_agent/prompts.py`. En el experimento de LangSmith el caso `both-02` respondió bien pero su consulta devolvió una fila por alarma. Si la evaluación empeora, el cambio se revierte

La corrida de verificación de T086 (2026-10-13, `eval/results/20261013-224949.json`) no sirvió para
decidir. Los primeros 30 casos aprobaron, entre ellos `both-02` con el conteo en una sola fila. Después
el servicio del modelo devolvió errores 503 y 504, y más tarde se agotó la cuota diaria, que resultó ser
de 500 pedidos por día para `gemini-3.5-flash-lite`. T086 queda abierta hasta repetir la corrida.

- [X] T087 Hacer que la evaluación trate la caída del servicio del modelo (errores 503 y 504) igual que el límite por minuto: esperar, reintentar el caso una vez y, si sigue, cortar la corrida sin contar los casos como fallados, en `eval/run_eval.py` y `eval/run_langsmith_experiment.py`, con su prueba. En la corrida del 2026-10-13, 7 casos figuraron como fallados por errores del servicio
- [X] T088 Aclarar en el prompt de SQL que un conteo no es un valor medido y no lleva unidad: en esa corrida la respuesta de `both-02` dijo "2 alarmas críticas de temperatura (C)", en `src/telemetry_agent/prompts.py`
- [X] T089 Repetir la evaluación y el experimento de LangSmith cuando se renueve la cuota, decidir si T086 y T088 se quedan o se revierten, y registrar en el informe y en `research.md` el límite diario de 500 pedidos

Corrida de verificación del 2026-10-14 (`eval/results/20261014-214000.json`): 41 de 42. El caso que falta,
`refuse-03`, se cortó por un error de red ("se ha forzado la interrupción de una conexión existente por el
host remoto"), no por una respuesta del agente. El experimento de LangSmith `gemini-3.5-flash-lite-41d86748`,
corrido a continuación, dio 42 de 42, con `both-02` resuelto por el conteo en una sola fila.

- [X] T090 Hacer que la evaluación reconozca también los cortes de conexión con el servicio del modelo como un error ajeno al agente, en `eval/run_eval.py`, con su prueba. Incluye la falta de conexión ("getaddrinfo failed"), que en la corrida del 2026-10-14 a las 22:34 hizo figurar como fallado a `refuse-02` mientras la notebook salía de la suspensión

Resultado final (2026-10-14, `eval/results/20261014-224501.json`): 42 de 42, percentil 90 de tiempo de
6,2 s. Los cambios de T086 y T088 se quedan. Entre las corridas afectadas por la red o el servicio
(`20261013-224949.json`, `20261014-214000.json` y `20261014-223425.json`) ningún caso falló por una
respuesta del agente. Pruebas automáticas: 102.

## Phase 14: Convergence

- [X] T091 Reemplazar los ejemplos resueltos del prompt de SQL, que son casi iguales a `sql-08` (alarmas críticas del área Bombeo de agua) y `sql-02` (técnico que más órdenes cerró), por preguntas que no estén en la evaluación, en `src/telemetry_agent/prompts.py` per FR-021 (contradicts)
- [X] T092 Reemplazar en los prompts del router y de la síntesis las frases de ejemplo que repiten casos de la evaluación: la última alarma crítica de la P-101 (`both-01`), "qué pasa con el motor" (`edge-02`), los equipos fuera de servicio (`sql-05`), la presión nominal (`noev-03`) y "el mes pasado" (`edge-05`), en `src/telemetry_agent/prompts.py` per FR-021 (contradicts)
- [X] T093 Crear el conjunto reservado de 8 casos en `eval/reservado.jsonl`, con preguntas de estilos y tablas distintos a los del conjunto principal, per FR-020 (missing)
- [X] T094 Permitir que el evaluador corra otro archivo de casos y guarde su resultado aparte, sin pisar `eval/results/latest.md`, en `eval/run_eval.py`, con su prueba, per FR-020 (missing)
- [X] T095 Verificar con el modelo real los casos del conjunto principal afectados por T091 y T092, y correr una sola vez el conjunto reservado, sin ajustar nada a partir de su resultado, per FR-020 y FR-021 (missing)
- [X] T096 Registrar el conjunto reservado y su resultado en `plan.md`, `research.md`, el README y el informe per SC-008 (partial)

Resultado de la fase 14 (2026-10-14). Los 7 casos del conjunto principal que se parecían a los
ejemplos de los prompts (`sql-02`, `sql-05`, `sql-08`, `both-01`, `noev-03`, `edge-02` y `edge-05`)
aprobaron con los ejemplos nuevos. El conjunto reservado se corrió una sola vez y dio 8 de 8
(`eval/results/20261014-233423-reservado.json`). Pruebas automáticas: 103.

- [X] T097 Correr el conjunto principal completo con los prompts nuevos, porque el cambio de ejemplos puede afectar a cualquier caso. Queda para el 2026-10-15, cuando se renueve la cuota diaria

## Phase 15: Convergence

- [X] T098 CRITICAL Agregar un caso de evaluación con una pregunta de "el que más" que tenga empate (el área con más alarmas críticas: Compresores de aire y Bombeo de agua, 10 cada una), sin modificar los casos existentes per Constitution V (missing)
- [X] T099 Hacer que las consultas de "el que más" o "el que menos" conserven los empates (`FETCH FIRST 1 ROWS WITH TIES` en lugar de `LIMIT 1`), en la regla y en el ejemplo del prompt de SQL de `src/telemetry_agent/prompts.py` per FR-022 (missing)
- [X] T100 Hacer que la síntesis nombre a todos los empatados y diga que hay un empate, en `src/telemetry_agent/prompts.py` per FR-022 (missing)
- [X] T101 Registrar el requisito de empates y el resultado de la corrida de T097 en el informe, el README y la guía per SC-008 (partial)

Resultado de las fases 14 y 15 (2026-10-15, `eval/results/20261015-001031.json`): 43 de 43, con los
ejemplos nuevos de los prompts y el caso de empates (`edge-08`). Percentil 90 de tiempo de 15,9 s y
mediana de 10,4 s, más alta que en las corridas anteriores. La corrida se hizo con una clave de otro
proyecto de Google porque la cuota de la primera se había agotado. El experimento de LangSmith
`gemini-3.5-flash-lite-77b83c3d` dio 42 de 43: en `noev-01` el router tomó la pregunta como ajena a la
planta y respondió sin buscar en las fuentes; el contenido de la respuesta era correcto. Pruebas
automáticas: 104.
