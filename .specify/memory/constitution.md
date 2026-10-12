<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Principios modificados: ninguno
- Secciones modificadas: Restricciones Técnicas (base de datos), Governance (lista de enmiendas)
- Secciones eliminadas: ninguna
- Artefactos actualizados: spec.md (Assumptions), research.md (D3), tasks.md (T059)
- TODOs diferidos: ninguno
- Historial: (plantilla sin ratificar) -> 1.0.0 el 2026-10-09, principios I a VI
-->
# Agente SQL de Telemetría y Mantenimiento Industrial Constitution

## Core Principles

### I. Acceso a datos de solo lectura (NON-NEGOTIABLE)
El agente MUST ejecutar únicamente sentencias SELECT. Toda consulta generada por el modelo
MUST validarse antes de ejecutarse (una sola sentencia, sin escritura, sin DDL) y MUST correr
con un rol de base de datos que solo tenga permiso de lectura. Debe haber un límite de filas y
un tiempo máximo por consulta.
Fundamento: el modelo de lenguaje produce SQL que nadie revisó. La defensa no puede depender de
que el modelo se porte bien, tiene que estar en la base y en el validador.

### II. Respuestas fundadas en fuentes
Toda respuesta MUST apoyarse en filas devueltas por la base o en fragmentos recuperados de los
PDF. Si ninguna fuente respalda la respuesta, el agente MUST decir que no tiene la información y
MUST NOT inventar valores. Cada respuesta MUST indicar de qué fuente proviene (SQL, documentos
o ambas) y, cuando use documentos, el archivo y la página.
Fundamento: en mantenimiento industrial un dato inventado es peor que no tener dato.

### III. Decisión de fuente explícita
El agente MUST decidir en cada pregunta si consulta la base, los documentos, ambos o ninguno, y
MUST registrar esa decisión. La decisión es un paso propio del grafo del agente, no una
consecuencia implícita de un prompt largo.
Fundamento: el enunciado exige que el agente decida cuándo obtener el contexto de cada fuente,
y un paso explícito se puede probar y mostrar en el coloquio.

### IV. Reproducibilidad
Un tercero MUST poder levantar el proyecto siguiendo el README: dependencias fijadas, esquema y
datos generados por scripts con semilla fija, variables de entorno documentadas en un
`.env.example`, y ningún secreto en el repositorio.
Fundamento: el criterio de aprobación pide código documentado y reproducible.

### V. Evaluación y observabilidad
Todo comportamiento del agente MUST tener al menos un caso en un conjunto de evaluación con
respuesta esperada. Las ejecuciones MUST quedar trazadas en LangSmith. Un cambio que empeora el
resultado del conjunto de evaluación MUST NOT integrarse sin justificación escrita.
Fundamento: sin casos de prueba no hay forma de afirmar que el agente funciona.

### VI. Simplicidad defendible
Cada componente MUST poder explicarse y justificarse por quien presenta el trabajo. No se agrega
una herramienta, librería o capa si no resuelve un requisito concreto de la especificación.
Fundamento: el trabajo se defiende en un coloquio oral, y lo que no se puede explicar no suma.

## Restricciones Técnicas

- Lenguaje del agente: Python.
- Orquestación del agente: LangGraph.
- Modelo de lenguaje: Gemini mediante su capa gratuita. Los límites de uso de esa capa MUST
  tenerse en cuenta en el diseño (pocas llamadas por pregunta, reintentos con espera).
- Base de datos relacional y almacén vectorial: PostgreSQL con la extensión pgvector. Puede ser un
  servicio en la nube (por ejemplo Supabase) o un Postgres local con Docker. La conexión se define
  por variables de entorno, sin cambios en el código.
- Interfaz: Streamlit.
- Todos los datos MUST ser sintéticos. No se usan datos reales de ninguna planta, empresa ni
  proyecto de terceros. Los documentos PDF son originales y ficticios.
- El agente MUST aceptar preguntas en castellano y en inglés.

## Flujo de Desarrollo y Puertas de Calidad

- Se sigue Spec Driven Development con Spec Kit en este orden: constitución, especificación,
  plan, tareas e implementación. Los artefactos de cada etapa se conservan en el repositorio.
- No se implementa una tarea que no figure en `tasks.md`. Si surge trabajo nuevo, primero se
  agrega a las tareas.
- Antes de la entrega se verifica cada criterio de aprobación y de promoción del enunciado
  contra el sistema funcionando, y se deja constancia en el informe.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Una enmienda requiere
dejar escrito el cambio y su motivo en este archivo y actualizar la versión: MAJOR si se
elimina o redefine un principio, MINOR si se agrega un principio o se amplía una regla, PATCH
para aclaraciones de redacción. Antes de cerrar cada etapa del flujo se revisa que el
resultado cumpla estos principios, y cualquier excepción se justifica por escrito en el plan.

### Enmiendas

- **1.1.0 (2026-10-12)**. Se amplió la restricción técnica de la base de datos. Antes exigía
  "PostgreSQL en Supabase". Motivo: todo el desarrollo, las pruebas y la evaluación se hicieron
  con el Postgres local de Docker, y Supabase no se llegó a probar. La restricción escrita no
  describía el sistema real. Ningún principio cambió. Es MINOR porque amplía una regla.

**Version**: 1.1.0 | **Ratified**: 2026-10-09 | **Last Amended**: 2026-10-12
