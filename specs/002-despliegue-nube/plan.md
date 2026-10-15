# Implementation Plan: Despliegue del agente en la nube

**Branch**: `002-despliegue-nube` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-despliegue-nube/spec.md`

## Summary

Publicar el agente de la 001, sin cambiar su código, con dos servicios gratuitos:

- **Base de datos**: Neon, PostgreSQL 18 con pgvector. Se carga con los scripts y el volcado que ya están en
  el repositorio.
- **Interfaz**: Streamlit Community Cloud, desplegada desde `master` del repo
  `Mind-fever/telemetry-sql-agent`. Recibe las claves como secretos de primer nivel, que Streamlit expone
  como variables de entorno ([research.md](research.md) R5).

La app en la nube se conecta solo con el rol `agent_ro`. La conexión con permiso de escritura se usa una vez,
desde la máquina del autor, para cargar la base. Después no se usa más ni sale de `.env`.

La equivalencia con la versión local se demuestra de dos formas:

- Contando las filas de las 8 tablas.
- Corriendo 8 casos de la evaluación, uno por categoría, contra Neon.

**Plazo**: SC-001 y SC-002 tienen que cumplirse el jueves 15 de octubre a las 20:00. Si no, se abandona y se
entrega `master` como está.

## Technical Context

**Language/Version**: Python 3.13, igual que en local. En Streamlit Cloud se elige en Advanced settings (R6).

**Primary Dependencies**: las de `requirements.txt`, sin cambios: LangGraph, langchain-google-genai,
Streamlit 1.65, psycopg 3 y LangSmith.

**Storage**:
- Nube: Neon, con PostgreSQL 18.6 y pgvector 0.8.6, en la base `neondb` (comprobado, R1).
- Local: Docker, PostgreSQL 16 con pgvector. No cambia.

**Testing**:
- Las pruebas automáticas existentes (`pytest`), con la configuración local, para SC-006.
- `eval/run_eval.py --cases eval/nube.jsonl` contra Neon, para SC-003. Son los 8 casos copiados del
  conjunto principal (R9).
- Un recorrido manual desde la dirección pública, para SC-001 y SC-004.

**Target Platform**: Streamlit Community Cloud (Linux) y Neon (AWS). Los usuarios entran desde cualquier
navegador.

**Project Type**: aplicación web de un solo proyecto, ya existente. Lo que se despliega es configuración, no
código nuevo.

**Performance Goals**:
- Primera respuesta con la base recién despertada: menos de 60 s.
- Respuestas siguientes: menos de 20 s, igual que en local (SC-005).

**Constraints**:
- Costo cero y sin tarjeta.
- Ningún secreto en el repositorio.
- `DATABASE_URL` y `DATABASE_URL_RO` de `.env` no se modifican.
- En la nube, solo la conexión de `agent_ro`.
- Código del agente sin cambios, salvo el plan B de R5 si hace falta.
- Cuota del modelo: la app usa una clave aparte. La prueba contra Neon gasta unos 20 pedidos de la clave
  local.

**Scale/Scope**: el autor y el jurado, pocas preguntas por día. La app es pública hasta el 30 de octubre de
2026 y después se apaga o se restringe.

No queda ningún NEEDS CLARIFICATION: [research.md](research.md) resuelve todos los puntos abiertos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple | Estado |
|---|---|---|
| I. Solo lectura (NON-NEGOTIABLE) | La app usa solo `DATABASE_URL_RO` con `agent_ro`. `db/roles.sql` le da solo SELECT. Se mantienen el validador, la transacción READ ONLY, el tope de 50 filas y el timeout de 8 s, sin cambios. `DATABASE_URL` nunca se carga en Streamlit (R8). `refuse-01` se corre contra Neon (R9). | Cumple |
| II. Respuestas fundadas | Mismo agente y mismos prompts. La base remota tiene los mismos datos y fragmentos, verificado por conteo (SC-002). | Cumple |
| III. Decisión de fuente explícita | Sin cambios en el grafo. Se verifica con los 8 casos, que cubren las rutas sql, docs, both, refuse y none. | Cumple |
| IV. Reproducibilidad | El README explica cómo crear la base remota, cargarla y publicar la app, con los nombres de las variables. Las claves viven solo en `.env` y en los paneles. `.env.example` documenta `NUBE_DATABASE_URL` y `NUBE_DATABASE_URL_RO` sin valores. | Cumple |
| V. Evaluación y observabilidad | Trazas de la nube en el proyecto `agente-sql-telemetria-nube`. Los 8 casos contra Neon se comparan con la corrida local. No se cambia el comportamiento del agente, así que no hace falta otra evaluación completa. | Cumple |
| VI. Simplicidad defendible | No hay servicios nuevos aparte de los dos gratuitos que pide el criterio. No se agregan scripts: la carga usa `setup_db.py` y el volcado existentes. Se descartaron un proceso para mantener la app despierta y el recorte de `requirements.txt` (R6, R10). | Cumple |
| Restricción técnica de la base | Ya admite "un servicio en la nube" con conexión por variables de entorno, desde la enmienda 1.1.0. | Cumple |
| Flujo SDD | Todo el trabajo va en `tasks.md`, incluso los pasos manuales en los paneles. | Cumple |

Resultado: pasa sin excepciones. No hace falta la tabla de Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-despliegue-nube/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones R1 a R11
├── data-model.md        # Fase 1: base remota, configuración y evidencia
├── quickstart.md        # Fase 1: pasos para desplegar y validar
├── contracts/
│   └── configuracion-nube.md   # Variables de cada entorno (local, carga, nube)
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

Esta funcionalidad no agrega código. Toca solo estos archivos existentes:

```text
README.md                     # Sección nueva: despliegue en la nube, reactivar y apagar
.env.example                  # Se agregan NUBE_DATABASE_URL y NUBE_DATABASE_URL_RO, sin valores
docs/                         # Informe: fila del criterio de despliegue y su evidencia
eval/nube.jsonl               # Nuevo: los 8 casos de SC-003, copiados de golden.jsonl con un campo "origen" (y "nota" en noev-02), R9
eval/results/                 # Resultado de los 8 casos contra Neon (latest-nube.md, <fecha>-nube.json)
app/streamlit_app.py          # Solo si hace falta el plan B de R5 (copiar st.secrets a os.environ)
```

Lo que no se toca: `src/telemetry_agent/`, `db/`, `scripts/`, `requirements.txt`, ni `DATABASE_URL` y
`DATABASE_URL_RO` en `.env`.

**Structure Decision**: se mantiene el proyecto único de la 001. Lo nuevo es configuración en dos paneles
externos y en `.env`, y está descrito en [contracts/configuracion-nube.md](contracts/configuracion-nube.md).

## Orden de trabajo y puntos de corte

1. **Base remota** (para SC-002): generar la clave de `agent_ro`, correr `setup_db.py` contra Neon, cargar
   el volcado y contar las filas.
2. **Agente local contra Neon**: una pregunta de prueba y después los 8 casos (SC-003). Si esto falla, la
   falla está en la base y no en Streamlit.
3. **App en Streamlit Cloud** (para SC-001): desplegar desde `master` con Python 3.13 y los secretos.
   Hacer una pregunta de cada tipo desde otra computadora o desde el celular.
4. **A las 20:00**: si se cumplen SC-001 y SC-002, se sigue. Si no, se anota en `tasks.md` qué falló y se
   abandona.
5. **Evidencia y documentación** (SC-004, SC-007, FR-012, FR-013): captura, traza, README e informe. Hay
   tiempo hasta el viernes a las 23:59.
6. **Fusionar `002-despliegue-nube` a `master` y subir.**

## Constitution Check (después del diseño)

Se volvió a revisar después de escribir [data-model.md](data-model.md),
[contracts/configuracion-nube.md](contracts/configuracion-nube.md) y [quickstart.md](quickstart.md):

- El contrato de configuración deja `DATABASE_URL` fuera de la nube y muestra `agent_ro` como único usuario
  de la app (principio I).
- El quickstart usa solo scripts que ya existen (principios IV y VI).

Sigue cumpliendo sin excepciones.

## Complexity Tracking

Sin violaciones que justificar.
