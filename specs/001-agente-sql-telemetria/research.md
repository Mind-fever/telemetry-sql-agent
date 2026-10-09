# Research: Agente SQL de Telemetría y Mantenimiento Industrial

**Fecha**: 2026-10-09 | **Spec**: [spec.md](spec.md)

Cada decisión indica su estado de verificación. "Verificado" significa que se confirmó en la
página oficial el 2026-10-09. "No verificado" significa que no se pudo confirmar y queda como
punto a comprobar durante la implementación, con la acción que lo resuelve.

## D1. Modelo de lenguaje: Gemini en capa gratuita

- **Decisión**: usar un modelo Flash de Gemini, configurable por variable de entorno
  (`GEMINI_MODEL`), con `gemini-3.5-flash` como valor por defecto.
- **Evidencia (verificado)**: la página de precios oficial lista como gratuitos en la capa
  gratuita, entre otros, `gemini-3.5-flash`, `gemini-3.5-flash-lite` y `gemini-3.1-flash-lite`.
  Los modelos Pro aparecen como no disponibles en la capa gratuita.
- **No verificado**: los límites exactos por modelo (solicitudes por minuto y por día). La
  documentación oficial remite a Google AI Studio, que requiere iniciar sesión. Los blogs de
  terceros que aparecen en las búsquedas no se usan como evidencia.
- **Consecuencia de diseño**: el agente hace como máximo 3 o 4 llamadas al modelo por pregunta,
  reintenta con espera creciente ante errores de cuota, y el modelo se cambia sin tocar código.
- **Acción**: al tener la API key, mirar los límites reales en AI Studio y anotarlos en el informe.
- **Alternativa descartada**: modelos Pro, por no estar en la capa gratuita.
- **Fuente**: https://ai.google.dev/gemini-api/docs/pricing y
  https://ai.google.dev/gemini-api/docs/rate-limits

## D2. Embeddings para el RAG

- **Decisión**: `gemini-embedding-2` con 768 dimensiones de salida, llamado con el SDK oficial
  `google-genai`.
- **Evidencia (verificado)**: la documentación indica que `gemini-embedding-2` es el modelo
  estable recomendado, que su salida por defecto es de 3072 dimensiones y que se admite un rango
  de 128 a 3072, con 768, 1536 y 3072 como valores recomendados. No usa el parámetro
  `task_type`: la tarea se indica con un prefijo en el texto (`task: search result | query: ...`
  para consultas y `title: ... | text: ...` para documentos). Admite hasta 8192 tokens de entrada,
  y lo que excede se trunca sin aviso.
- **Por qué 768**: reduce el espacio ocupado en la base (el plan gratuito de Supabase tiene
  500 MB) y alcanza para unas pocas decenas de fragmentos.
- **No verificado**: si los embeddings tienen capa gratuita. La sección de embeddings de la
  página de precios quedó fuera del texto que se pudo leer.
- **Acción**: la primera ingesta lo confirma. Si hubiera costo o un límite que bloquee, la
  clase de embeddings es intercambiable y se documenta la alternativa en el informe.
- **Fuente**: https://ai.google.dev/gemini-api/docs/embeddings

## D3. Base de datos y almacén vectorial: PostgreSQL con pgvector

- **Decisión**: una sola base PostgreSQL con la extensión pgvector para las tablas de negocio y
  para los fragmentos de documentos. Se usa Supabase como servicio en la nube. La conexión es por
  `DATABASE_URL`, así que sirve cualquier Postgres con pgvector (por ejemplo uno local).
- **Evidencia (verificado)**: el plan gratuito de Supabase incluye 500 MB de base por proyecto,
  2 proyectos activos y 5 GB de salida de datos. Los proyectos gratuitos se pausan tras 1 semana
  de inactividad. La guía de pgvector de Supabase indica habilitar la extensión desde el panel y
  usar columnas de tipo `vector(n)` con el operador `<->` para ordenar por distancia.
- **No verificado**: que pgvector esté habilitable en el plan gratuito (las páginas leídas no lo
  afirman ni lo niegan) y la sintaxis exacta de los índices HNSW de esa guía.
- **Acción**: `create extension vector` se prueba al crear el proyecto. HNSW e IVFFlat son
  índices estándar de pgvector, así que se toma la sintaxis de su documentación original al
  implementar. Con la cantidad de fragmentos prevista (menos de 200) un índice ni siquiera es
  necesario, y se decide en la implementación.
- **Riesgo a gestionar**: la pausa por inactividad. Si el proyecto está pausado el día del
  coloquio, hay que reactivarlo antes. Mitigación: usarlo durante la semana previa y tener un
  Postgres local (docker compose) como respaldo.
- **Alternativas descartadas**: SQLite más una base vectorial aparte (dos tecnologías sin
  necesidad); Neon u otro Postgres (sin ventaja que justifique cambiar).
- **Fuente**: https://supabase.com/pricing y
  https://supabase.com/docs/guides/database/extensions/pgvector

## D4. Framework agéntico: LangGraph

- **Decisión**: LangGraph para orquestar el agente como un grafo de estados con pasos explícitos.
- **Por qué**: permite que la decisión de fuente sea un nodo propio (principio III), que los
  reintentos de SQL sean un ciclo con tope, y que cada paso aparezca como un tramo separado en
  la traza de LangSmith. Está nombrado en el enunciado como ejemplo de framework agéntico.
- **Versión disponible (verificado en PyPI)**: langgraph 1.2.14, langchain-google-genai 4.4.0,
  langsmith 0.14.5, google-genai 2.29.0.
- **Alternativa descartada**: Smolagents. Un agente que escribe código para resolver la consulta
  dificulta garantizar la regla de solo lectura.

## D5. Seguridad de las consultas SQL

- **Decisión**: defensa en capas. (1) Validador que parsea la consulta con `sqlglot` en dialecto
  PostgreSQL y exige una única sentencia SELECT, sobre tablas permitidas, sin funciones
  peligrosas. (2) Rol de base de datos con solo permiso SELECT sobre las tablas permitidas.
  (3) Transacción de solo lectura con `statement_timeout`. (4) Tope de filas aplicado por el
  sistema, no por el modelo.
- **Por qué en capas**: cada capa cubre el fallo de la otra. Si el validador tuviera un hueco, el
  rol y la transacción de solo lectura siguen impidiendo escribir.
- **Versión disponible (verificado en PyPI)**: sqlglot 30.21.0.

## D6. Observabilidad y evaluación

- **Decisión**: LangSmith para trazas y para ejecutar la evaluación; un conjunto de evaluación
  propio en un archivo `jsonl` con verificaciones deterministas (sin un modelo que haga de juez).
- **Evidencia (verificado)**: el plan Developer de LangSmith es gratuito, con 1 puesto y 5 mil
  trazas base por mes. La página menciona 14 días de retención para trazas base, pero no
  confirma que eso aplique al plan Developer.
- **Consecuencia**: una corrida completa de evaluación consume pocas trazas, pero las capturas
  para el informe se toman en el momento y no se confía en verlas semanas después.
- **Por qué verificaciones deterministas**: comparar el resultado de la consulta generada con el de
  una consulta de referencia, y comprobar el archivo y la página citados, es reproducible y se
  puede explicar en el coloquio. Un juez basado en modelo agrega variabilidad y consumo de cuota.
- **Fuente**: https://www.langchain.com/pricing

## D7. Interfaz: Streamlit

- **Decisión**: Streamlit con los componentes de chat y paneles desplegables para la fuente.
- **Por qué**: nombrado en el enunciado, es Python puro y no requiere un frontend aparte.
- **Despliegue en la nube del agente**: fuera de alcance por ahora (ver la sección Assumptions
  de la especificación). Si sobra tiempo, la opción a evaluar es Streamlit Community Cloud
  conectado al repositorio de GitHub. No se afirma nada sobre sus condiciones hasta verificarlas.

## D8. Qué se puede comprobar sin la API key

El esquema, el seed, el validador de SQL, el ingestado de PDF, el recorte en fragmentos y la
lógica del grafo se prueban con pruebas automáticas usando un modelo y un generador de
embeddings falsos y deterministas. Lo que requiere la API key (calidad real de las respuestas,
puntaje de la evaluación, trazas en LangSmith) lo ejecuta el usuario con su propia clave, y esos
resultados son la evidencia del informe.
