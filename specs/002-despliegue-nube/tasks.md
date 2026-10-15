---

description: "Lista de tareas del despliegue del agente en la nube"
---

# Tasks: Despliegue del agente en la nube

**Input**: Design documents from `/specs/002-despliegue-nube/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/configuracion-nube.md](contracts/configuracion-nube.md),
[quickstart.md](quickstart.md)

**Tests**: no se agregan pruebas automáticas nuevas, porque la funcionalidad no cambia código. La
verificación sale de los escenarios de [quickstart.md](quickstart.md), de los 8 casos de evaluación contra
Neon y de las 104 pruebas existentes. Hay dos excepciones:
- T020 agrega una prueba del mensaje que aparece cuando falta una clave.
- T013, si hace falta el plan B, lleva su propia prueba.

**Organization**: las tareas van por historia de usuario. La base remota (fase 2) bloquea a todas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de una tarea pendiente)
- **[Story]**: historia de la especificación (US1, US2, US3)
- **(autor)**: la tarea se hace en un panel web con la cuenta del autor. El asistente no crea cuentas ni
  carga claves.

## Reglas para todas las tareas

- **Ningún comando muestra una clave ni una cadena de conexión.** Los valores se leen de `.env` dentro del
  proceso, con `dotenv_values`, y se pasan como variables de entorno, nunca como argumentos.
- **`DATABASE_URL` y `DATABASE_URL_RO` de `.env` no se modifican** (G2 del contrato). Para apuntar a Neon,
  se definen solo para un proceso: `load_dotenv` no pisa una variable que ya está en el entorno.
- **Conexión directa de Neon**: es `NUBE_DATABASE_URL` sin el sufijo `-pooler` en el host (R2). Se arma
  dentro del proceso; no se guarda.
- Comandos para Git Bash, desde la raíz del repo, con `.venv/Scripts/python.exe`.
- **Plazo**: T014 es el punto de corte de las 20:00 del jueves 15 de octubre de 2026.

---

## Phase 1: Setup

**Purpose**: dejar el repositorio y `.env` listos para trabajar contra Neon.

- [X] T001 Hacer un commit en la rama `002-despliegue-nube` con los artefactos de Spec Kit:
  `specs/002-despliegue-nube/`, que son `spec.md`, `plan.md`, `research.md`, `data-model.md`,
  `quickstart.md`, `contracts/`, `checklists/` y este `tasks.md`. Mensaje en castellano.
  - No incluir los cambios de permisos de `.specify/scripts/bash/*.sh` ni `docs/plan-despliegue-nube.md`,
    que no es parte de la entrega.
- [X] T002 [P] En `.env.example`, agregar al final un bloque comentado "Despliegue en la nube (opcional,
  ver README)" con `NUBE_DATABASE_URL=` y `NUBE_DATABASE_URL_RO=`, sin valores. Dos comentarios de una
  línea:
  - La primera es la cadena pooled de Neon del dueño del proyecto y se usa solo para cargar la base desde
    la máquina del autor.
  - La segunda es la de `agent_ro` y es la única que se carga en Streamlit.
- [X] T003 Generar la clave de `agent_ro` en Neon y agregar `NUBE_DATABASE_URL_RO` al final de `.env`
  (R3). Hacerlo con un script de Python que corre en el momento y no queda en el repo:
  1. Leer `NUBE_DATABASE_URL` con `dotenv_values`.
  2. Generar la clave con `secrets.token_urlsafe(24)`.
  3. Armar la cadena con el mismo host pooled, la misma base y `sslmode=require`, con usuario `agent_ro` y
     la clave nueva. Usar `psycopg.conninfo.make_conninfo` o codificar la URL.
  4. Agregar la línea a `.env`.
  5. Imprimir solo "NUBE_DATABASE_URL_RO agregada".

  Antes y después, comparar un hash de las líneas `DATABASE_URL=` y `DATABASE_URL_RO=` de `.env` para
  comprobar que no cambiaron. Si `NUBE_DATABASE_URL_RO` ya existe, no hacer nada.

---

## Phase 2: Foundational (base remota)

**Purpose**: dejar en Neon una copia exacta de la base local. Bloquea a las tres historias.

- [X] T004 Crear el esquema, la extensión `vector` y el rol `agent_ro` en Neon. Correr
  `scripts/setup_db.py` con `DATABASE_URL` = conexión directa de Neon y `DATABASE_URL_RO` =
  `NUBE_DATABASE_URL_RO`, definidas solo para ese proceso. Para no mostrar los valores, usar un script de
  Python que corre en el momento: arma el entorno y llama a `setup_db.py` con `subprocess`.
  - Se espera "Esquema creado." y "Rol agent_ro listo con permisos de solo lectura."
  - Si Neon rechaza la clave por entropía, volver a T003 con `token_urlsafe(32)`.
- [X] T005 Cargar `db/dump/telemetria_datos.sql` en Neon con el `psql` 16.15 del contenedor de Docker (R4).
  1. Comprobar que el contenedor esté levantado (`docker compose up -d db`).
  2. Copiar el volcado con `docker compose cp db/dump/telemetria_datos.sql db:/tmp/telemetria_datos.sql`.
  3. Correr `docker compose exec -T -e PGURL db sh -c 'psql "$PGURL" -v ON_ERROR_STOP=1 -f /tmp/telemetria_datos.sql'`,
     con `PGURL` = conexión directa de Neon, definida en el entorno del proceso que lanza `docker`.

  Se espera un `COPY n` por tabla y ningún error.

  **Antes de cargar (hallazgo B1 del análisis)**: comprobar que la variable llega al contenedor. Correr
  `docker compose exec -T -e PGURL db sh -c 'test -n "$PGURL" && echo PGURL ok || echo PGURL vacia'`
  con `PGURL` definida en el entorno del proceso. Si dice "vacía", lanzar `docker` desde un script de
  Python con `subprocess`, pasando `-e PGURL=<valor>` en la lista de argumentos. El valor no se imprime y
  la lista de argumentos tampoco.
- [X] T006 Contar las filas de las 8 tablas en Neon (conexión directa) y en Docker (`DATABASE_URL`), y
  comparar (SC-002). Se espera, en las dos bases: areas 18, tecnicos 20, equipos 40, sensores 108,
  lecturas 38.880, alarmas 171, ordenes_mantenimiento 153 y doc_chunks 18. Anotar el resultado en la
  sección "Notas de ejecución" de este archivo.
- [X] T007 Comprobar en Neon que `agent_ro` no puede escribir: con `NUBE_DATABASE_URL_RO`, intentar
  `delete from alarmas` y esperar un error de permisos. Después, con la conexión directa, confirmar que
  siguen 171 alarmas. Anotarlo en "Notas de ejecución".

**Checkpoint**: SC-002 cumplido. La base remota está lista para el agente.

---

## Phase 3: User Story 1 - El jurado usa el agente desde un enlace (Priority: P1) 🎯 MVP

**Goal**: la app responde desde una dirección pública, con la base de Neon y solo con `agent_ro`.

**Independent Test**: desde otra computadora o desde el celular, abrir el enlace y hacer las 5 preguntas del
escenario 3 de [quickstart.md](quickstart.md).

- [X] T008 [US1] Prueba de humo antes de publicar: correr
  `python -m telemetry_agent.cli "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?"` con
  `DATABASE_URL_RO` = `NUBE_DATABASE_URL_RO`, solo para ese proceso. Se espera la misma respuesta que con
  la base local, con fuente "base de datos". Si falla, el problema está en la base o en la conexión, no en
  Streamlit.
- [X] T009 [US1] (autor) Preparar el texto del panel de Secrets en un archivo temporal fuera del repo, con
  el formato de [contracts/configuracion-nube.md](contracts/configuracion-nube.md):
  - Claves de primer nivel, sin secciones.
  - `DATABASE_URL_RO` con el valor de `NUBE_DATABASE_URL_RO`.
  - `GEMINI_API_KEY` con la clave aparte para la nube.
  - `LANGSMITH_PROJECT = "agente-sql-telemetria-nube"`.
  - Los valores no secretos, iguales a los de `.env`.
  - **Sin `DATABASE_URL` ni `NUBE_DATABASE_URL`.**

  El asistente puede escribir la plantilla con los valores no secretos; las claves las completa el autor.
- [X] T010 [US1] (autor) En share.streamlit.io, crear la app:
  - Repositorio `Mind-fever/telemetry-sql-agent`, rama `master`, archivo `app/streamlit_app.py`.
  - Un subdominio propio en `streamlit.app`.
  - En Advanced settings: Python 3.13 y pegar los Secrets de T009.

  Anotar la dirección pública en "Notas de ejecución".
- [X] T011 [US1] Revisar el registro de construcción de la app (R6):
  - Debe decir Python 3.13 y que se instaló `requirements.txt` sin errores.
  - Si usó otra versión y falla una dependencia, borrar la app y volver a crearla.
  - Si sigue fallando, ajustar `requirements.txt` en la rama 002. En ese caso, desplegar desde
    `002-despliegue-nube` hasta la fusión (R7).
- [X] T012 [US1] Abrir la dirección pública sin sesión iniciada, desde otro dispositivo distinto de la
  computadora del autor (otra computadora o un celular, SC-001). Hacer las 5 preguntas del escenario 3 de [quickstart.md](quickstart.md): datos, documentos,
  combinada, sin respaldo y pedido de borrar alarmas.
  - Para cada una, anotar en "Notas de ejecución" la fuente indicada y el tiempo de respuesta.
  - La primera debe tardar menos de 60 s y las demás menos de 20 s (SC-005).
  - Después del pedido de borrar, confirmar en Neon que siguen 171 alarmas (SC-004).
  - En la barra lateral debe decir "Trazas en LangSmith: activadas".
- [X] T013 [US1] **Solo si en T012 la app dice que falta una variable** (por ejemplo "Falta DATABASE_URL_RO"),
  aplicar el plan B de R5:
  - En `app/streamlit_app.py`, antes de importar `telemetry_agent`, copiar a `os.environ` cada clave de
    primer nivel de `st.secrets` que todavía no esté en el entorno. Si no hay archivo de secretos, no
    hacer nada: localmente no existe, y el acceso tira `FileNotFoundError` o `StreamlitSecretNotFoundError`.
  - Agregar en `tests/test_streamlit_app.py` una prueba de que sin secretos la app sigue arrancando.
  - Commit en la rama 002, borrar la app y crearla de nuevo desde `002-despliegue-nube` (R7).
  - Si no hace falta, marcarla como no aplicada en "Notas de ejecución".
- [X] T014 [US1] **Punto de corte, jueves 15 de octubre de 2026 a las 20:00.** Anotar en "Notas de
  ejecución" si se cumplen SC-001 (T012) y SC-002 (T006).
  - Si se cumplen, seguir con las fases 4 a 6.
  - Si no, hacer T026 y no hacer nada más de esta lista.

**Checkpoint**: la app pública responde. Es el MVP del criterio de promoción.

---

## Phase 4: User Story 2 - El autor comprueba que la versión en la nube es equivalente (Priority: P2)

**Goal**: evidencia de que la versión en la nube es la misma que se evaluó.

**Independent Test**: los 8 casos contra Neon dan lo mismo, caso por caso, que en
`eval/results/20261015-001031.json`, y hay trazas en `agente-sql-telemetria-nube`.

- [X] T015 [P] [US2] Crear `eval/nube.jsonl` con 8 líneas copiadas tal cual de `eval/golden.jsonl`: los casos
  `sql-01`, `doc-01`, `both-01`, `refuse-01`, `noev-02`, `none-01`, `edge-03` y `follow-01`, en ese orden.
  Agregar a cada línea el campo
  `"origen": "Copia de eval/golden.jsonl del 2026-10-15: 8 de sus 43 casos, uno por categoría, para SC-003 de la funcionalidad 002. Fuera de este campo, el caso es idéntico al original."`.
  Agregar solo a `noev-02` el campo
  `"nota": "Se usa en lugar de noev-01 porque noev-01 tiene una variación conocida con el modelo real (medición del 2026-10-15 en specs/001-agente-sql-telemetria/tasks.md). Si fallara contra Neon, no diría nada sobre la nube."`.
  - Para comprobar la copia, quitar `origen` y `nota` de cada línea y compararla con su original en
    `golden.jsonl`: tienen que ser iguales. Se puede hacer con un script de Python que corre en el momento.
  - Correr `python eval/run_eval.py --cases eval/nube.jsonl --check-refs` con la configuración local para
    ver que el archivo se lee.
- [X] T016 [US2] Correr `python eval/run_eval.py --cases eval/nube.jsonl --delay 5` con tres variables
  definidas solo para ese proceso (R9):
  - `DATABASE_URL_RO` = `NUBE_DATABASE_URL_RO`.
  - `DATABASE_URL` = conexión directa de Neon. `run_eval.py` la usa para las consultas de referencia y para
    el conteo de "datos intactos".
  - `LANGSMITH_PROJECT=agente-sql-telemetria-nube`.

  Se espera:
  - 8 de 8 y datos intactos.
  - Se generan `eval/results/latest-nube.md` y `eval/results/<fecha>-nube.json`.
  - `eval/results/latest.md` no cambia.

  Unos 20 pedidos de la cuota local.
- [X] T017 [US2] Comparar caso por caso `eval/results/<fecha>-nube.json` con los mismos 8 ids de
  `eval/results/20261015-001031.json`: `passed` y ruta. Anotar la tabla en "Notas de ejecución" (SC-003).
  Si un caso difiere, volver a correr solo ese caso una vez y anotar los dos resultados. No ajustar
  prompts: esta funcionalidad no cambia el agente (FR-004). **Si después de repetirlo sigue difiriendo**,
  escribir en "Notas de ejecución", antes de T025, la justificación que pide el principio V de la
  constitución: qué difiere, si la causa es la nube o la variación del modelo, y por qué igual se fusiona.
  Sin esa justificación, no se fusiona.
- [X] T018 [US2] (autor) En LangSmith, abrir el proyecto `agente-sql-telemetria-nube` y comprobar que estén
  las ejecuciones de T012 (5) y T016 (8). Guardar una captura de la traza de la pregunta combinada de T012
  en `docs/informe/capturas/07-traza-nube.png`.
- [X] T019 [P] [US2] (autor) Guardar una captura de la app pública respondiendo la pregunta combinada de
  T012, con la dirección visible, en `docs/informe/capturas/06-app-nube.png`.

**Checkpoint**: la evidencia del criterio de despliegue está completa.

---

## Phase 5: User Story 3 - La versión local sigue igual (Priority: P3)

**Goal**: confirmar que la 002 no rompió la versión local.

**Independent Test**: con `.env` tal cual, sin variables extra, pasan las 104 pruebas y el agente responde
con la base de Docker.

- [X] T020 [P] [US3] Agregar en `tests/test_streamlit_app.py` una prueba del caso borde "falta una clave"
  (hallazgo C4 del análisis). Hoy no hay ninguna.
  - Simular que `load_agent()` lanza `RuntimeError("Falta DATABASE_URL_RO en el entorno (ver .env.example).")`.
  - Comprobar que la app muestra un `st.error` que nombra `DATABASE_URL_RO`.
  - Comprobar que no muestra ningún valor de conexión: el texto de error no contiene `postgresql://`.

  Después, correr `.venv/Scripts/python.exe -m pytest` sin variables extra en el entorno. Se esperan 105
  pruebas aprobadas: las 104 de antes de la 002 más esta, o 106 si se aplicó T013. Anotar el resultado
  en "Notas de ejecución" (SC-006).
- [X] T021 [US3] Con la configuración local, correr el CLI con una pregunta de datos y comprobar que
  responde con la base de Docker. Confirmar con el hash de T003 que `DATABASE_URL` y `DATABASE_URL_RO`
  de `.env` no cambiaron (FR-010).

**Checkpoint**: la versión local sigue como estaba.

---

## Phase 6: Polish & documentación

**Purpose**: documentar y entregar (FR-012, FR-013, SC-007). Hay tiempo hasta el viernes 16 a las 23:59.

- [X] T022 [P] Actualizar `README.md`:
  1. En "Qué incluye", agregar la fila "Despliegue en la nube (Neon y Streamlit Community Cloud)" con la
     dirección pública y `specs/002-despliegue-nube/`. Cambiar el párrafo de criterios de promoción para
     que incluya el despliegue.
  2. Reemplazar la sección "Base de datos en la nube" por "Despliegue en la nube". Debe explicar:
     - Cómo crear el proyecto de Neon y las dos variables `NUBE_*`.
     - Cómo cargar la base (T003 a T006, sin valores).
     - Cómo crear la app en Streamlit, con la lista de nombres de Secrets y la advertencia de no cargar
       `DATABASE_URL`.
     - Cómo correr los 8 casos contra Neon.
     - Cómo reactivar la app dormida, en menos de 10 minutos (SC-007), y abrirla unos minutos antes del
       coloquio.
     - Que después del 30 de octubre de 2026 hay que borrarla o hacerla privada, y regenerar o borrar la
       clave de Gemini de la nube (FR-006, R11).
  3. En "Resultado de la evaluación", agregar una línea con el resultado de `eval/results/latest-nube.md`.
  4. En "Informe y evidencias", agregar las capturas 06 y 07 y `eval/results/latest-nube.md`.
- [X] T023 [P] Actualizar `docs/informe/README.md` con las dos capturas nuevas y su fecha.
- [X] T024 Actualizar el informe `docs/informe/informe.docx`:
  - Agregar la fila del criterio de despliegue con su evidencia: dirección, capturas 06 y 07, resultado
    de los 8 casos y conteo de filas.
  - Para no pasar de 10 páginas, reducir la tabla de corridas de evaluación de 13 filas a las 4 o 5 que
    cuentan la historia. Proponerle al autor cuáles quedan antes de borrar.
  - Exportar `docs/informe/informe.pdf`, con LibreOffice si está instalado; si no, lo hace el autor desde
    Word. Comprobar que el PDF tiene 10 páginas o menos.
- [ ] T025 Cerrar la funcionalidad:
  - Cambiar el Status de `specs/002-despliegue-nube/spec.md` a "Implementada" con la fecha.
  - Marcar estas tareas y completar "Notas de ejecución".
  - **Antes del commit final, comprobar que no hay secretos en la rama** (FR-009, principio IV, hallazgo C1
    del análisis):
    - `git grep -n -I -E "neon\.tech|npg_|AIza|lsv2_|agent_ro:[^@]*@" -- . ':!.env.example'` sobre lo
      versionado y lo que está en el área de preparación no tiene que devolver nada. Hay que revisar a mano
      los ejemplos con `cambiar_esta_clave`.
    - `git ls-files .streamlit/secrets.toml .env` no tiene que devolver nada.
    - El archivo temporal de Secrets de T009 tiene que estar fuera del repo o borrado.
  - Hacer commit y, con el OK del autor, fusionar `002-despliegue-nube` en `master` y subirlo.
  - Si la app se desplegó desde la rama 002 (T013), borrarla y crearla de nuevo desde `master` con el
    mismo subdominio.

---

## Phase 7: Después de la entrega

**Purpose**: los criterios que solo se pueden comprobar con el paso del tiempo (SC-007 y FR-006).

- [ ] T027 (autor) **Viernes 16 de octubre de 2026, a la mañana** (hallazgo C2 del análisis). Abrir la
  dirección pública después de la noche sin visitas.
  - Si aparece el aviso de app dormida, pulsar el botón para despertarla y medir cuánto tarda hasta
    que se puede hacer una pregunta. Hacer una pregunta de datos.
  - Anotar en "Notas de ejecución" si estaba dormida, cuánto tardó en despertar (SC-007 pide menos de
    10 minutos) y cuánto tardó la primera respuesta.
  - Si se hace antes de la entrega, agregar el dato al README y al informe (T022, T024).
- [ ] T028 (autor) **Sábado 31 de octubre de 2026**, después del último coloquio (hallazgo C3 del análisis,
  FR-006):
  - Borrar la app en el panel de Streamlit, o cambiarla a privada con acceso solo para correos invitados.
  - Regenerar o borrar en Google AI Studio la clave de Gemini de la nube.
  - Opcional: borrar el proyecto de Neon.
  - El asistente puede dejar programado un recordatorio para esa fecha si el autor lo pide.

---

## Abandono (solo si T014 no se cumple)

- [ ] T026 Si a las 20:00 del jueves 15 no se cumplen SC-001 y SC-002:
  - Anotar en "Notas de ejecución" qué se intentó, en qué tarea falló y por qué se descartó.
  - Hacer commit de este archivo en la rama `002-despliegue-nube` y **no fusionarla**.
  - Opcional, el autor: borrar la app de Streamlit y el proyecto de Neon desde sus paneles.
  - Se entrega `master` como está.

---

## Dependencies & Execution Order

```text
T001 ─┐
T002 ─┤ (en paralelo)
T003 ─┴─► T004 ─► T005 ─► T006 ─► T007            (fase 2: bloquea todo)
                                    │
                                    ├─► T008 ─► T009 ─► T010 ─► T011 ─► T012 ─► (T013) ─► T014   US1
                                    │
                                    ├─► T015 ─► T016 ─► T017 ;  T018, T019 después de T012/T016   US2
                                    │
                                    └─► T020, T021                                                   US3
T014 ✔ ─► T022, T023 (en paralelo) ─► T024 ─► T025 ─► T027 (mañana del 16) ─► T028 (31/10)
T014 ✘ ─► T026
```

- **US1** depende solo de la fase 2. Es la que define el punto de corte.
- **US2** depende de la fase 2. T015 se puede preparar en cualquier momento; T018 y T019 necesitan T012.
- **US3** no depende de las otras. Se puede correr al final o mientras se espera la construcción de T010.

## Parallel Opportunities

- T002 junto con T003, porque son archivos distintos.
- Mientras Streamlit construye la app (T010 y T011): T015 (crear `eval/nube.jsonl`) y T020 (pytest local).
- T022 y T023, porque son archivos distintos.

## Implementation Strategy

1. **MVP = fases 1, 2 y 3**: base remota verificada y app pública que responde. Es lo que tiene que estar
   antes de las 20:00 (T014).
2. Después, US2: la evidencia de equivalencia, con unos 20 pedidos de cuota.
3. Después, US3: confirmar que la versión local no cambió.
4. Por último, la documentación y la fusión, hasta el viernes 16 a las 23:59.

## Notas de ejecución

(Se completa durante la implementación: conteos de T006 y T007, dirección de T010, tabla de T012, si se
aplicó T013, decisión de T014, comparación de T017 y resultado de T020.)

### 2026-10-15

- **T003**: `NUBE_DATABASE_URL_RO` agregada a `.env`. El hash de las líneas `DATABASE_URL=` y
  `DATABASE_URL_RO=` es el mismo antes y después (`09c01829dfd0`).
- **T004**: `setup_db.py` contra Neon (conexión directa) terminó con "Esquema creado." y "Rol agent_ro
  listo con permisos de solo lectura.". Neon aceptó la clave de `token_urlsafe(24)`.
- **T005**: antes de cargar se comprobó que `PGURL` llega al contenedor (hallazgo B1): `docker compose
  exec -e PGURL` toma el valor del entorno. El volcado se cargó con el `psql` del contenedor, sin errores,
  y los 8 `setval` quedaron en el último id de cada tabla.
- **T006 (SC-002 cumplido)**: Docker y Neon dan las mismas filas, tabla por tabla.

  | Tabla | Docker | Neon |
  |---|---|---|
  | areas | 18 | 18 |
  | tecnicos | 20 | 20 |
  | equipos | 40 | 40 |
  | sensores | 108 | 108 |
  | lecturas | 38.880 | 38.880 |
  | alarmas | 171 | 171 |
  | ordenes_mantenimiento | 153 | 153 |
  | doc_chunks | 18 | 18 |

- **T007**: con `agent_ro`, `delete from alarmas` falló con `InsufficientPrivilege` ("permission denied
  for table alarmas"). Después siguen 171 alarmas. `agent_ro` lee por el pooler (40 equipos), y pgvector
  0.8.6 está instalado.
- **T008**: la pregunta "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?" con el CLI contra
  Neon respondió 1 alarma, igual que la consulta de referencia de `sql-01` en Docker.
- **T015**: se creó `eval/nube.jsonl` con 8 casos, uno por categoría. Sin los campos `origen` y `nota`,
  cada caso es idéntico a su original de `golden.jsonl`. `--check-refs` lee los 8 casos y no reporta
  problemas en las referencias.
- **T016**: los 8 casos contra Neon dieron 8 de 8 a las 16:16, con datos intactos (`DATABASE_URL` en Neon
  solo para ese proceso). El resultado está en `eval/results/latest-nube.md` y
  `eval/results/20261015-161644-nube.json`. `eval/results/latest.md` no cambió (mismo md5). Tiempos: la
  mediana fue 6,2 s y el p90 10,0 s.
- **T017 (SC-003 cumplido)**: los 8 casos coinciden con la corrida local `20261015-001031.json`.

  | Caso | Local | Neon |
  |---|---|---|
  | sql-01 | aprobado, sql | aprobado, sql |
  | doc-01 | aprobado, docs | aprobado, docs |
  | both-01 | aprobado, both | aprobado, both |
  | refuse-01 | aprobado, refuse | aprobado, refuse |
  | noev-02 | aprobado, docs | aprobado, docs |
  | none-01 | aprobado, none | aprobado, none |
  | edge-03 | aprobado, sql | aprobado, sql |
  | follow-01 | aprobado, sql | aprobado, sql |

  No hubo diferencias, así que no hace falta la justificación del principio V.
- **T020 (SC-006)**: se agregó a `tests/test_streamlit_app.py` la prueba
  `test_missing_setting_names_the_variable_without_showing_values`. Con la configuración local pasan 105
  pruebas: las 104 de antes más esta.
- **T021**: el CLI con la configuración local respondió "¿Cuántas alarmas siguen abiertas?" con 3, desde
  Docker. El hash de `DATABASE_URL` y `DATABASE_URL_RO` sigue siendo `09c01829dfd0` y las dos apuntan a
  `localhost`.
- **T009 y T010**: el autor creó la app en `https://telemetry-sql-agent.streamlit.app/` desde `master`,
  con los Secrets de T009. La plantilla de Secrets quedó en un archivo temporal fuera del repo y no
  incluye `DATABASE_URL` ni `NUBE_DATABASE_URL`.
- **T011**: el registro de construcción dice "Using Python 3.13.16" (lo confirmó el autor). La app
  construyó y corre sin errores.
- **T012 (16:37 a 16:40)**: las 5 preguntas se hicieron desde la dirección pública, en el navegador
  integrado de Claude, que corre en la computadora del autor y no tenía sesión de Streamlit. Los tiempos son
  aproximados: se tomaron por capturas de pantalla.

  | Pregunta | Fuente | Resultado | Tiempo |
  |---|---|---|---|
  | Alarmas críticas de P-101 en septiembre (datos) | Base de datos | 1 alarma, igual que la referencia | 9 a 20 s, la primera |
  | Lubricación de rodamientos (documentos) | Documentos | 2.500 h o 4 meses, `manual_mantenimiento_preventivo.pdf` p. 4 | menos de 10 s |
  | Procedimiento para la última alarma de vibración del C-201 (combinada) | Base de datos y documentos | alarma crítica, procedimiento de `procedimiento_respuesta_alarmas.pdf` p. 3 | 10 a 18 s |
  | Borrar todas las alarmas (modificación) | Pedido rechazado (solo lectura) | rechazado; en Neon siguen 171 alarmas | menos de 8 s |
  | Costo de un rodamiento (sin respaldo) | Base de datos | dice que no hay información de costos y no inventa | 10 a 18 s |

  La barra lateral dice "Trazas en LangSmith: activadas". El autor repitió la pregunta de la bomba P-101
  desde su celular y obtuvo la misma respuesta: 1 alarma crítica en septiembre. SC-001 se cumple desde
  otro dispositivo.
- **T013**: no se aplicó. La app lee los Secrets como variables de entorno sin cambios de código: lo
  muestran la conexión a Neon y las trazas activadas.
- **T014 (punto de corte)**: a las 16:45 del jueves 15 se cumplen SC-001 (T012) y SC-002 (T006). No se
  abandona: se sigue con las fases 4 a 6. T026 no se aplica.
- **T024 (Word)**: cambios en `docs/informe/informe.docx`, validado con el validador de la herramienta de
  Word (párrafos: 331 → 310).
  - Fila nueva "Despliegue en la nube" en criterios de promoción, que ahora dice "se eligieron cinco".
  - El párrafo que decía que el despliegue no se había elegido ahora explica cómo se hizo.
  - La limitación "Supabase sin probar" pasó a ser "Servicios gratuitos en la nube".
  - Pruebas automáticas: 105, de las cuales 5 son de la interfaz.
  - Tabla de corridas: quedan la 1, la 2, la 3, la 9 a 11 y la 13, elegidas por el autor. El texto aclara
    que las 13 están en `eval/results/`.

  Falta que el autor exporte el PDF desde Word y compruebe que tiene 10 páginas o menos: en esta máquina
  no hay LibreOffice.
- **T018 y T019**: el autor guardó `docs/informe/capturas/06-app-nube.png` (16:57) y
  `docs/informe/capturas/07-traza-nube.png` (17:02), las dos en PNG, y se actualizaron las referencias.
  - La 06 muestra la dirección pública, la pregunta combinada del C-201, la respuesta con cita a
    `procedimiento_respuesta_alarmas.pdf` p. 3, la fuente "Base de datos y documentos" y "Trazas en
    LangSmith: activadas".
  - La 07 muestra la traza de las 4:57 PM: ruta `both`, 9,71 s en total, con router, SQL, recuperación y
    síntesis.
  - Ninguna de las dos muestra claves.
- **T024 (PDF)**: `docs/informe/informe.pdf` se exportó con Word (automatización COM, el documento se abrió
  en modo de solo lectura). Word cuenta 10 páginas y pypdf también. El PDF incluye la fila del criterio de
  despliegue, "se eligieron cinco", las 105 pruebas y la limitación nueva.
- **T025**: se borró el archivo temporal de Secrets de T009. Se buscaron secretos en lo versionado y en lo
  preparado para commit, con el resultado de abajo. El estado de `spec.md` pasó a "Implementada y
  desplegada".
  - Búsqueda de claves (`npg_`, `AIza`, `lsv2_`, `agent_ro:…@` y `neondb_owner:`) en lo preparado y en
    toda la historia de la rama (`git log master..HEAD -p`): la única coincidencia es el propio patrón
    escrito en esta lista.
  - No hay hosts de Neon (`ep-….neon.tech`) en el repo.
  - `git ls-files .env .streamlit/secrets.toml` no devuelve nada.
  - Pendiente: fusionar en `master` y subir, con el OK del autor.
