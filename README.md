# Agente SQL de telemetría y mantenimiento industrial

Trabajo Práctico Integrador de AI Engineering. Ingeniería en Informática, 5to año, UCSE Sede Rafaela.
Autor: Santiago Nicolas Martinez.

Un agente de IA que responde preguntas en castellano o inglés sobre una planta industrial ficticia.
Consulta una base de datos relacional con SQL que genera el modelo y busca en manuales en PDF con RAG.
En cada pregunta decide por sí mismo qué fuente usar: la base, los documentos, ambas o ninguna.
Solo lee: nunca modifica la base.

## Por qué este proyecto

Elegí la telemetría industrial porque es el tema de mi trabajo final de carrera: un middleware que junta datos de máquinas y sensores de distintos fabricantes, que hoy quedan aislados en cada equipo, y los lleva a un formato común. Ese trabajo resuelve cómo llegan los datos. Este agente explora el paso siguiente: cómo los consulta una persona.

Pensé en quien trabaja en mantenimiento o en operaciones, que necesita saber qué equipo tuvo más alarmas o qué hacer ante una alarma crítica, sin escribir SQL ni buscar en manuales. Por eso el agente combina los datos de la planta con los procedimientos en PDF.

No es parte de la tesis. Es un trabajo práctico con datos inventados, pero quedó armado de forma que podría conectarse a la telemetría real del middleware si algún día quiero extender el proyecto.

Si se integrara con el middleware, habría que reemplazar Gemini por un modelo que corra localmente, porque la tesis busca no depender de servicios externos.

## Sobre el proceso

Era la primera vez que usaba Spec Driven Development. Antes trabajaba con agentes de IA sin una metodología: los comportamientos esperados quedaban repartidos en mensajes sueltos a lo largo de la conversación, y dependía de que el agente no perdiera el contexto con el tiempo.

Con Spec Kit cada comportamiento queda escrito una sola vez en la especificación, con su criterio para comprobarlo. Además, las etapas de aclaración y de análisis me marcaron cosas que yo mismo había pasado por alto. Por ejemplo, dos escenarios que preguntaban por "el mes pasado" cuando los datos solo cubren septiembre, o una regla que el agente aplicaba de dos maneras distintas.

Me resultó tan útil que la empecé a usar en otro proyecto, una herramienta de carga manual y automática de PDF, donde noté que el trabajo avanza más rápido porque las especificaciones son más claras.

## Qué incluye

| Pieza | Dónde |
|---|---|
| Base relacional con 7 tablas y más de 15 registros en cada una | `db/schema.sql`, `scripts/seed.py`, `db/dump/` |
| 3 PDF ficticios para el RAG | `data/docs/` (se regeneran con `scripts/build_pdfs.py`) |
| Agente con LangGraph (decide la fuente, genera y valida SQL, recupera fragmentos) | `src/telemetry_agent/graph.py` |
| Interfaz de chat con Streamlit | `app/streamlit_app.py` |
| Trazas y evaluación con LangSmith | `eval/run_eval.py`, `eval/run_langsmith_experiment.py` |
| Spec Driven Development con GitHub Spec Kit | `.specify/`, `specs/001-agente-sql-telemetria/` y `specs/002-despliegue-nube/` |
| Pruebas automáticas | `tests/` |
| Informe técnico y capturas | `docs/informe/` |
| Despliegue en la nube: base en Neon y app en Streamlit Community Cloud | https://telemetry-sql-agent.streamlit.app/ y `specs/002-despliegue-nube/` |

Criterios de promoción que cubre: SDD, framework agéntico (LangGraph), interfaz gráfica (Streamlit),
observabilidad y evaluación (LangSmith) y despliegue en la nube (Neon y Streamlit Community Cloud). La versión
local con Docker sigue funcionando igual.

## Resultado de la evaluación

Última corrida, 15 de octubre de 2026, con `gemini-3.5-flash-lite`: 43 de 43 casos aprobados con
`eval/run_eval.py`. El experimento de LangSmith del mismo día dio 42 de 43: una pregunta sin respaldo se
respondió bien, pero sin buscar en las fuentes. El detalle está en `eval/results/latest.md`.
Las pruebas automáticas son 105 y pasan todas.

Además hay un conjunto reservado de 8 casos (`eval/reservado.jsonl`) que no se usó para ajustar los prompts.
Se corrió una sola vez, el 14 de octubre de 2026, y dio 8 de 8 (`eval/results/latest-reservado.md`).

Contra la base en la nube (Neon) se corrieron 8 casos del conjunto principal, uno por categoría
(`eval/nube.jsonl`). El 15 de octubre de 2026 dieron 8 de 8, con el mismo resultado y la misma ruta que en
local, caso por caso (`eval/results/latest-nube.md`).

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
python eval/run_eval.py                     # corre los 43 casos; el resultado queda en eval/results/
python eval/run_langsmith_experiment.py     # los mismos casos como experimento de LangSmith
python eval/run_eval.py --cases eval/reservado.jsonl   # conjunto reservado; resultado en latest-reservado.md
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
| `NUBE_DATABASE_URL`, `NUBE_DATABASE_URL_RO` | Opcionales. Conexiones a la base de Neon, para desplegar en la nube (ver "Despliegue en la nube"). |

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

`eval/golden.jsonl` tiene 43 casos: preguntas de datos, de documentos, combinadas, pedidos de escritura que deben
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
5. `specs/002-despliegue-nube/`: el despliegue en la nube, como una funcionalidad aparte con su propia
   especificación, plan y tareas. Las notas de ejecución de `tasks.md` registran cada verificación.

## Informe y evidencias

| Qué | Dónde |
|---|---|
| Informe técnico (PDF y Word) | `docs/informe/` |
| Capturas de la interfaz y de una traza de LangSmith | `docs/informe/capturas/` |
| Resultado de la última evaluación | `eval/results/latest.md` (el detalle por caso está en el `.json` de la misma carpeta) |
| Resultado de los 8 casos contra la base en la nube | `eval/results/latest-nube.md` |
| Capturas de la app en la nube y de su traza | `docs/informe/capturas/06-app-nube.png`, `07-traza-nube.png` |
| Casos de evaluación y respuestas esperadas | `eval/golden.jsonl` |
| Guía de los datos y de la demostración | `docs/guia-demo.md` |
| Enunciado del trabajo | `docs/Enunciado.pdf` |

## Datos y documentos

Los datos y los PDF son ficticios y están hechos para este trabajo. Los PDF no deben usarse como guía en una
instalación real. Las fechas de los datos van del 2026-09-01 al 2026-09-30; el agente toma el 30 de septiembre
como "hoy".

## Despliegue en la nube

La app está publicada en **https://telemetry-sql-agent.streamlit.app/**. Es pública hasta el 30 de octubre de
2026 y no pide iniciar sesión. La base está en Neon (PostgreSQL con pgvector, plan gratuito) y la interfaz en
Streamlit Community Cloud (gratuito), desplegada desde la rama `master`. No hubo que cambiar el código: el
agente lee la conexión y las claves de variables de entorno. La especificación, el plan y las tareas están en
`specs/002-despliegue-nube/`.

En la nube la app solo tiene la conexión del rol `agent_ro`, que solo puede leer. La conexión con permisos de
escritura se usa una sola vez, desde la computadora de quien despliega, para cargar la base. Nunca se carga
en Streamlit.

Los comandos de esta sección son para bash. En Windows, correrlos desde Git Bash.

### 1. Base en Neon

1. Crear un proyecto en https://neon.tech. Neon trae pgvector y la base se despierta sola con la primera
   consulta. Copiar la cadena de conexión *pooled* (el host termina en `-pooler`).
2. Agregar al final de `.env` dos variables nuevas, sin tocar `DATABASE_URL` ni `DATABASE_URL_RO`, que siguen
   apuntando a Docker:
   - `NUBE_DATABASE_URL`: la cadena de Neon, tal como se copió.
   - `NUBE_DATABASE_URL_RO`: la misma cadena con el usuario `agent_ro` y una clave nueva, larga y al azar, por
     ejemplo la que da `python -c "import secrets; print(secrets.token_urlsafe(24))"`. Neon exige claves de al
     menos 60 bits de entropía.
3. Crear las tablas y el rol, y cargar el volcado. Se usa la conexión **directa**, que es la misma cadena sin
   `-pooler` en el host, porque el volcado necesita una sesión estable. Las variables se definen solo para cada
   comando, así `.env` no cambia (`load_dotenv` no pisa una variable que ya está definida):

   ```bash
   DATABASE_URL="<cadena directa de Neon>" DATABASE_URL_RO="<NUBE_DATABASE_URL_RO>" python scripts/setup_db.py
   docker compose cp db/dump/telemetria_datos.sql db:/tmp/telemetria_datos.sql
   PGURL="<cadena directa de Neon>" docker compose exec -T -e PGURL db sh -c 'psql "$PGURL" -v ON_ERROR_STOP=1 -f /tmp/telemetria_datos.sql'
   ```

   El `psql` del contenedor de Docker sirve aunque no haya `psql` instalado. Al terminar, cada tabla tiene que
   tener las mismas filas que la base local: 18 áreas, 20 técnicos, 40 equipos, 108 sensores, 38.880 lecturas,
   171 alarmas, 153 órdenes y 18 fragmentos.

### 2. Probar el agente contra Neon

```bash
DATABASE_URL_RO="<NUBE_DATABASE_URL_RO>" python -m telemetry_agent.cli "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?"
DATABASE_URL_RO="<NUBE_DATABASE_URL_RO>" DATABASE_URL="<cadena directa de Neon>" LANGSMITH_PROJECT=agente-sql-telemetria-nube python eval/run_eval.py --cases eval/nube.jsonl --delay 5
```

`run_eval.py` usa `DATABASE_URL` para las consultas de referencia y para comprobar que los datos quedaron
intactos, por eso esa variable también apunta a Neon. El resultado va a `eval/results/latest-nube.md` y no
pisa el de los 43 casos.

### 3. App en Streamlit Community Cloud

En https://share.streamlit.io: Create app, repositorio `Mind-fever/telemetry-sql-agent`, rama `master`,
archivo `app/streamlit_app.py`. En Advanced settings, elegir **Python 3.13** y cargar los Secrets como claves
de primer nivel, sin secciones `[...]`, porque solo las de primer nivel llegan como variables de entorno:

| Secret | Valor |
|---|---|
| `DATABASE_URL_RO` | el valor de `NUBE_DATABASE_URL_RO` |
| `GEMINI_API_KEY` | una clave **aparte**, de otro proyecto de Google AI Studio, para no gastar la cuota de desarrollo |
| `LANGSMITH_API_KEY` | la clave de LangSmith |
| `LANGSMITH_PROJECT` | `agente-sql-telemetria-nube`, para separar las trazas de la nube de las locales |
| `LANGSMITH_TRACING`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `SQL_MAX_ROWS`, `SQL_TIMEOUT_MS`, `SQL_MAX_RETRIES`, `RETRIEVAL_TOP_K` | los mismos valores que en `.env` |

**No cargar `DATABASE_URL` ni `NUBE_DATABASE_URL`.** La app no las necesita y tienen permisos de escritura.

Después de desplegar, conviene revisar en el registro de construcción que diga Python 3.13. Si muestra otra
versión y falla una dependencia, hay que borrar la app y crearla de nuevo, porque la versión no se puede cambiar
sobre una app existente.

### 4. Si la app o la base están dormidas

- **Streamlit** duerme la app cuando pasa un tiempo sin visitas (unas 12 horas, según su foro). En ese caso
  aparece un aviso con un botón para despertarla. El 16 de octubre, después de la noche, la app abrió al
  instante. Antes de una demostración, conviene abrir la app y hacer una pregunta unos minutos antes.
- **Neon** suspende la base cuando no se usa y la despierta sola con la primera consulta. Ese día la primera
  pregunta tardó unos 25 segundos.

### 5. Después del 30 de octubre de 2026

La app es pública solo mientras dura la evaluación. Después hay que:

1. Borrarla en el panel de Streamlit, o hacerla privada con acceso solo para correos invitados.
2. Regenerar o borrar en Google AI Studio la clave de Gemini que usa la nube.
3. Opcional: borrar el proyecto de Neon.

## Problemas frecuentes

- **`docker compose up` falla con un error de conexión al motor de Docker.** Docker Desktop está cerrado. Abrirlo,
  esperar a que termine de iniciar y volver a correr el comando.
- **Errores 429 o `RESOURCE_EXHAUSTED`.** Se alcanzó el límite de la capa gratuita de Gemini. El mensaje del agente
  indica si es el límite por minuto o el diario. La evaluación espera y reintenta sola ante el límite por minuto, y
  se detiene ante el diario. Límites observados el 2026-10-10: `gemini-3.5-flash` 5 pedidos por minuto y 20 por día;
  `gemini-3.5-flash-lite` 15 por minuto y 500 por día (una evaluación completa usa unas 110). Los límites vigentes se ven en https://ai.dev/rate-limit.
- **Las preguntas sobre documentos responden "no tengo esa información".** Revisar que `ingest_docs.py` haya
  informado 18 fragmentos cargados. Si usó `--fake`, los embeddings son falsos y hay que volver a correrlo sin esa
  opción.
- **El nombre del modelo no existe.** Los nombres de los modelos cambian. Ver la lista vigente en la documentación
  de Gemini y ajustar `GEMINI_MODEL`.
