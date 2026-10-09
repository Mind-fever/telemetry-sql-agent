# Quickstart: validar el agente de punta a punta

Guía de validación de la Fase 1. Los comandos exactos se confirman en el README cuando termina
la implementación.

## Requisitos previos

- Python 3.11 o superior.
- Una base PostgreSQL con pgvector: un proyecto de Supabase o `docker compose up -d db`.
- Una API key de Gemini y, para las trazas, una API key de LangSmith.
- Un archivo `.env` copiado de `.env.example` con `DATABASE_URL`, `DATABASE_URL_RO`,
  `GEMINI_API_KEY`, `LANGSMITH_API_KEY` y `LANGSMITH_PROJECT`.

## Pasos

1. Instalar dependencias desde `requirements.txt`.
2. Crear el esquema y el rol de solo lectura (`db/schema.sql` y `db/roles.sql`).
3. Cargar los datos sintéticos con `scripts/seed.py`.
4. Generar los PDF con `scripts/build_pdfs.py` y cargarlos con `scripts/ingest_docs.py`.
5. Correr las pruebas automáticas.
6. Abrir la interfaz con Streamlit y hacer una pregunta de cada tipo.
7. Correr la evaluación.

## Resultados esperados

- Cada tabla de negocio tiene más de 15 filas (FR-001).
- Las pruebas automáticas pasan, incluidas las de rechazo de sentencias de escritura (FR-007).
- "¿Cuántas alarmas críticas hubo en el área de bombeo?" responde con la fuente `sql` y muestra
  la consulta (User Story 1).
- "¿Cada cuánto se lubrican los rodamientos de un motor?" responde con la fuente `docs`, con
  archivo y página (User Story 2).
- Una pregunta que necesita un dato y un procedimiento responde con la fuente `both` (User Story 3).
- "Borrá todas las alarmas" es rechazada y la base queda igual (SC-002).
- La evaluación termina con un resultado por caso y un porcentaje total, y cada ejecución aparece
  en LangSmith (User Story 5).
