-- Permisos del rol de solo lectura agent_ro (el rol lo crea scripts/setup_db.py con su clave).
-- Principio I de la constitucion: el agente nunca escribe. Esta es la capa de la base de datos.

revoke all on all tables in schema public from agent_ro;
grant usage on schema public to agent_ro;

-- Tablas de negocio: las puede consultar el SQL generado por el modelo.
grant select on areas, tecnicos, equipos, sensores, lecturas, alarmas, ordenes_mantenimiento to agent_ro;

-- Fragmentos de documentos: solo los lee el modulo de recuperacion.
grant select on doc_chunks to agent_ro;

-- Que el rol vea los operadores de pgvector tambien en Supabase (donde las extensiones viven en "extensions").
alter role agent_ro set search_path = public, extensions;
