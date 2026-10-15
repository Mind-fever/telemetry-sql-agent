# Investigación: Despliegue del agente en la nube

**Fecha**: 2026-10-15 | **Plan**: [plan.md](plan.md)

Cada decisión dice qué se eligió, por qué y qué otras opciones se consideraron. Lo que dice "comprobado" se
verificó hoy contra el servicio real o contra el código del repositorio. Lo que dice "según la
documentación" o "según el foro" no se verificó todavía.

## R1. La base de Neon

- **Decisión**: usar el proyecto de Neon que ya creó el autor, en la base `neondb`, sin cambiar el esquema.
- **Comprobado** (consulta de solo metadatos, sin mostrar la cadena de conexión):
  - PostgreSQL 18.6. La base local es 16.15.
  - pgvector 0.8.6 disponible, todavía sin instalar. `db/schema.sql` ya hace `create extension if not exists vector`.
  - Esquema `public` vacío (0 tablas).
  - El usuario de la cadena (`neondb_owner`) puede crear roles.
  - Todavía no existe un rol `agent_ro`.
  - La cadena de `NUBE_DATABASE_URL` apunta al host *pooled* (con `-pooler`) y usa `sslmode=require`.
- **Por qué**: en Neon la extensión queda en `public`, así que no hace falta el ajuste
  `extensions.vector(768)` que el README prevé para Supabase. `db/roles.sql` ya agrega `extensions` al
  `search_path` de `agent_ro`. PostgreSQL acepta que ese esquema no exista, así que no molesta.
- **Diferencia de versión**: el volcado tiene solo datos (`COPY`) y los `setval` de las secuencias. Cargar
  en PostgreSQL 18 datos volcados desde PostgreSQL 16 es compatible.
- **Alternativas**: Supabase. Se descartó porque el proyecto gratuito se pausa tras una semana sin uso y
  hay que reactivarlo a mano, con riesgo para el coloquio.

## R2. Qué conexión usa cada cosa

- **Decisión**:
  - Carga (esquema, rol y datos): conexión **directa** de `neondb_owner`, que es el mismo host sin `-pooler`.
  - Agente (en la nube y en las pruebas locales contra Neon): conexión **pooled** de `agent_ro`.
- **Por qué**:
  - El volcado y `setup_db.py` usan ajustes de sesión (`SET`, `set_config`). Con el pooler en modo
    transacción, cada sentencia puede caer en otra conexión del servidor, y esos ajustes no se mantienen
    entre sentencias.
  - El agente abre una conexión por consulta y solo usa `set local` dentro de la transacción
    (`src/telemetry_agent/db.py`). Eso funciona igual con el pooler.
  - El `search_path` de `agent_ro` se guarda en el servidor con `alter role`, así que el pooler no lo afecta.
- **Alternativas**: usar la conexión directa también para el agente. Funciona, pero cada visita a la app
  abriría una conexión real al servidor. El pooler es lo que recomienda Neon para aplicaciones.

## R3. La clave del rol `agent_ro` en Neon

- **Decisión**: se genera una clave nueva en la máquina del autor, con el módulo `secrets` de Python, de
  al menos 24 bytes al azar. Con ella se arma `NUBE_DATABASE_URL_RO`: la misma cadena pooled, con usuario
  `agent_ro` y esa clave. Se agrega al final de `.env` sin mostrarla en pantalla. El autor la copia
  después al panel de Streamlit.
- **Por qué**:
  - Neon exige claves de al menos 60 bits de entropía para los roles creados por SQL, según la
    documentación de roles de Neon. 24 bytes al azar son 192 bits.
  - No conviene reutilizar la clave local de Docker: es conocida, porque está en `.env.example`.
- **Restricción del autor**: `DATABASE_URL` y `DATABASE_URL_RO` de `.env` no se tocan.
  `NUBE_DATABASE_URL_RO` es una variable nueva.

## R4. Cómo se cargan los datos sin tocar `.env`

- **Decisión**: se corre `scripts/setup_db.py` con `DATABASE_URL` y `DATABASE_URL_RO` definidas solo para
  ese proceso: la conexión directa de Neon y `NUBE_DATABASE_URL_RO`.
- **Por qué funciona**: `load_dotenv` (`src/telemetry_agent/config.py`) no pisa variables que ya están en
  el entorno. Así el script usa la base de Neon y el `.env` sigue apuntando a Docker.
- **Carga del volcado**: no hay `psql` instalado en la máquina del autor (comprobado). Se usa el `psql`
  16.15 del contenedor de Docker, que sale a internet. Es la misma versión que generó el volcado y entiende
  el comando `\restrict` que trae el archivo. La cadena se le pasa como variable de entorno, no como
  argumento.
- **Verificación**: contar las filas de las 8 tablas en Neon y compararlas con la base local: 18 áreas,
  20 técnicos, 40 equipos, 108 sensores, 38.880 lecturas, 171 alarmas, 153 órdenes y 18 fragmentos (SC-002).
- **Alternativas**:
  - Correr `seed.py` e `ingest_docs.py` contra Neon. Se descartó porque gasta cuota de embeddings de Gemini
    y puede dar vectores distintos a los evaluados.
  - Instalar `psql` en Windows. Lleva más tiempo y no aporta nada.

## R5. Cómo llegan las claves a la aplicación en Streamlit Cloud

- **Decisión**: cargar en el panel de Secrets todas las variables como claves de primer nivel, sin
  secciones, con los mismos nombres que en `.env`. No hace falta cambiar código.
- **Por qué**: según la documentación de Streamlit, las claves de primer nivel de los secretos también
  quedan como variables de entorno, y las que están dentro de una sección `[...]` no. El agente lee todo
  con `os.getenv` en `get_settings()` cada vez que se llama, así que las ve. LangSmith también lee sus
  variables del entorno.
- **Riesgo y plan B**: si en el primer despliegue la app dice que falta `DATABASE_URL_RO` o
  `GEMINI_API_KEY`, se agrega al principio de `app/streamlit_app.py` una copia de `st.secrets` a
  `os.environ`. Es el único cambio de código previsto, y solo si hace falta.
- **Mensaje si falta algo**: la app ya muestra "No se pudo iniciar el agente…" con el detalle, por ejemplo
  "Falta DATABASE_URL_RO en el entorno". El detalle nombra la variable y no muestra su valor (comprobado en
  `db.py` y `streamlit_app.py`).

## R6. Versión de Python y dependencias en Streamlit Cloud

- **Decisión**: elegir Python 3.13 en Advanced settings, la misma versión con que se desarrolló y evaluó.
  Instalar con el `requirements.txt` actual, sin cambios.
- **Según la documentación**:
  - La versión se elige solo en Advanced settings; no se lee de `runtime.txt`.
  - Para cambiarla hay que borrar la app y desplegarla de nuevo.
  - La versión por omisión es 3.12.
- **Según el foro**: en 2026 hubo despliegues que usaron Python 3.14 aunque se eligiera otra versión.
- **Cómo se controla**: mirar en el registro de construcción qué versión se usó. Si no es 3.13 y alguna
  dependencia falla, borrar y volver a desplegar. Si el problema sigue, ajustar `requirements.txt` en la
  rama 002.
- **Por qué no se recorta `requirements.txt`**: trae `pytest` y `reportlab`, que la app no necesita, pero
  no molestan. Recortarlo es un cambio que no resuelve ningún requisito (principio VI).

## R7. Desde qué rama se despliega

- **Decisión**: desplegar la app desde `master`, archivo `app/streamlit_app.py`.
- **Por qué**:
  - La 002 no cambia código, solo documentación. El código de `master` es el que se va a desplegar.
  - Si después se fusiona la 002, la app no hay que tocarla.
  - Si se abandona, se borra la app y `master` queda igual. El criterio de abandono no cambia.
- **Excepción**: si hace falta el plan B de R5, ese cambio vive en la rama 002, y la app se despliega
  desde `002-despliegue-nube` hasta la fusión. Después de fusionar, se borra y se vuelve a desplegar
  desde `master` con el mismo subdominio.
- **Dirección fija (FR-001)**: elegir un subdominio propio en `streamlit.app` al crear la app, por
  ejemplo `telemetria-agente.streamlit.app`.

## R8. Trazas y clave del modelo en la nube

- **Decisión**: en Secrets van:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_API_KEY`
  - `LANGSMITH_PROJECT=agente-sql-telemetria-nube`
  - `GEMINI_API_KEY`, la clave aparte que creó el autor, distinta de la local (FR-011)
  - Los mismos valores no secretos que el `.env` local: modelo, modelo de embeddings, dimensiones y límites
- **Por qué**: el agente toma el nombre del proyecto de LangSmith de `LANGSMITH_PROJECT`, así que no hace
  falta código. Con los mismos valores no secretos, el comportamiento es el mismo que el evaluado (FR-004).
- **Qué no va nunca a Secrets**: `DATABASE_URL`. La app no la usa (`db.py` usa solo `DATABASE_URL_RO` en el
  agente) y es la conexión con permiso de escritura (FR-005).

## R9. Los 8 casos que se corren contra Neon (SC-003)

- **Decisión**: copiar esos 8 casos, sin cambios salvo los campos `origen` y `nota` descritos abajo, de `eval/golden.jsonl` a un archivo nuevo,
  `eval/nube.jsonl`. Correrlos desde la máquina del autor con `eval/run_eval.py --cases eval/nube.jsonl`,
  con tres variables definidas solo para ese comando, sin modificar `.env`:
  - `DATABASE_URL_RO` = `NUBE_DATABASE_URL_RO`, para el agente.
  - `DATABASE_URL` = conexión directa de Neon, la misma de la carga (R2).
  - `LANGSMITH_PROJECT=agente-sql-telemetria-nube`.

  Los casos son `sql-01`, `doc-01`, `both-01`, `refuse-01`, `noev-02`, `none-01`, `edge-03` y
  `follow-01`.
- **Cómo el archivo dice de dónde sale**: en JSONL no hay comentarios, y `load_cases` toma como caso
  cada línea que no está vacía (comprobado en `eval/run_eval.py`). Una línea de encabezado se tomaría como
  un caso más. La explicación va entonces en campos extra que `run_eval.py` ignora, porque solo lee los
  campos que conoce:
  - En los 8 casos: `"origen": "Copia de eval/golden.jsonl del 2026-10-15: 8 de sus 43 casos, uno por categoría, para SC-003 de la funcionalidad 002. Fuera de este campo, el caso es idéntico al original."`
  - Solo en `noev-02`: `"nota": "Se usa en lugar de noev-01 porque noev-01 tiene una variación conocida con el modelo real (medición del 2026-10-15 en specs/001-agente-sql-telemetria/tasks.md). Si fallara contra Neon, no diría nada sobre la nube."`

  Con esto, el archivo se explica solo, sin depender de esta investigación.
- **Por qué un archivo aparte y no `--only`**: con el conjunto principal, `run_eval.py` escribe
  `eval/results/latest.md` y reemplazaría el resultado de los 43 casos por el de 8. Con otro archivo de
  casos, el script escribe `latest-nube.md` y `<fecha>-nube.json`, y no toca el resultado principal
  (comprobado en `eval/run_eval.py`). No hace falta cambiar código.
- **Por qué `DATABASE_URL` también apunta a Neon**: `run_eval.py` usa `connect_admin()`, que lee
  `DATABASE_URL`, para dos cosas (comprobado en `eval/run_eval.py`):
  - Correr las consultas de referencia de cada caso.
  - Contar las filas antes y después de la corrida, para comprobar que los datos quedaron intactos.

  Si `DATABASE_URL` siguiera en Docker, las respuestas del agente vendrían de Neon pero se compararían con
  valores de la base local. El control de "datos intactos" del caso `refuse-01` miraría además la base
  equivocada. Esa conexión se usa solo desde la máquina del autor y solo para leer. No va a la nube (G1 del
  contrato).
- **Base de comparación**: la corrida local `eval/results/20261015-001031.json`, donde los 8 pasaron.
- **Por qué estos casos**:
  - Uno por cada una de las 8 categorías.
  - `refuse-01` prueba el rechazo de una escritura.
  - `edge-03` ("Listá todas las alarmas registradas") prueba el recorte a 50 filas.
  - Se usa `noev-02` y no `noev-01`, porque `noev-01` tiene una variación conocida con el modelo real
    (tareas de la 001, medición del 2026-10-15). Una falla de ese caso no diría nada sobre la nube.
- **Costo**: unos 20 pedidos de la cuota local.

## R10. Bases y apps que se duermen

- **Neon**: la base se suspende tras unos minutos sin uso y se despierta con la primera conexión, en
  segundos. psycopg espera a que conecte, así que la primera pregunta tarda más pero no falla (FR-008,
  SC-005).
- **Streamlit Cloud** (según el foro): la app se duerme tras 12 horas sin visitas. Quien la abre ve un botón
  para despertarla, y tarda hasta unos 2 minutos. Eso entra en los 10 minutos de SC-007.
- **Para el coloquio**: el autor abre la app y hace una pregunta unos minutos antes. Queda en el README.
- **Alternativas**: un proceso que visite la app cada pocas horas. Se descartó: agrega una pieza que hay
  que mantener y no resuelve ningún requisito.

## R11. Qué se hace después del 30 de octubre

- **Decisión**: el autor elige una de dos opciones:
  - Borrar la app en el panel de Streamlit.
  - Cambiarla a privada, con acceso solo para correos invitados.
  
  En los dos casos regenera o borra la clave de Gemini de la nube. Opcional: borrar el proyecto de Neon.
- **Por qué**: lo pide FR-006 y está en los supuestos de la especificación. Queda como paso en el README.
