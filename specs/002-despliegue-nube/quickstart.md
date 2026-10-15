# Quickstart: desplegar y validar en la nube

**Plan**: [plan.md](plan.md) | **Variables**: [contracts/configuracion-nube.md](contracts/configuracion-nube.md)

Guía para comprobar de punta a punta que la funcionalidad anda. Cada paso dice qué se espera ver. Los
comandos de este archivo son para Git Bash en la máquina del autor. **Ninguno muestra una clave ni una
cadena de conexión en pantalla.** El detalle de cada comando queda para `tasks.md`.

## Requisitos previos

- [ ] El proyecto de Neon está creado y `NUBE_DATABASE_URL` está en `.env` (ya está, R1).
- [ ] La cuenta de Streamlit Community Cloud está vinculada a GitHub, con acceso a
  `Mind-fever/telemetry-sql-agent`.
- [ ] La clave de Gemini aparte para la nube está creada. La guarda el autor, no está en `.env`.
- [ ] La base de Docker está levantada (`docker compose up -d db`). Hace falta su `psql` para cargar el
  volcado (R4).
- [ ] `master` está subido a GitHub, porque Streamlit despliega desde ahí (R7).

## Escenario 1: la base remota coincide con la local (SC-002)

1. Generar la clave de `agent_ro` y agregar `NUBE_DATABASE_URL_RO` al final de `.env` (R3).
   **Se espera**: `.env` tiene una línea más; `DATABASE_URL` y `DATABASE_URL_RO` quedan igual.
2. Correr `python scripts/setup_db.py` con `DATABASE_URL` = conexión directa de Neon y
   `DATABASE_URL_RO` = `NUBE_DATABASE_URL_RO`, solo para ese proceso (R4).
   **Se espera**: "Esquema creado." y "Rol agent_ro listo con permisos de solo lectura."
3. Cargar `db/dump/telemetria_datos.sql` en Neon con el `psql` del contenedor, usando la conexión directa.
   **Se espera**: una línea `COPY n` por tabla, sin errores.
4. Contar las filas de las 8 tablas en Neon y compararlas con la base local.
   **Se espera**: 18, 20, 40, 108, 38.880, 171 y 153 filas, y 18 fragmentos, iguales en las dos bases.
5. Con `agent_ro` en Neon, intentar un `delete from alarmas`.
   **Se espera**: error de permisos y las mismas 171 alarmas.

## Escenario 2: el agente local responde contra Neon (SC-003)

1. Hacer una pregunta con el CLI del agente y `DATABASE_URL_RO=NUBE_DATABASE_URL_RO` para ese proceso, por
   ejemplo "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?".
   **Se espera**: la misma respuesta que con la base local.
2. Correr `python eval/run_eval.py --cases eval/nube.jsonl --delay 5` con tres variables definidas solo
   para ese comando: `DATABASE_URL_RO=NUBE_DATABASE_URL_RO`, `DATABASE_URL` = conexión directa de Neon y
   `LANGSMITH_PROJECT=agente-sql-telemetria-nube`. `.env` no cambia (R9).
   **Se espera**: los 8 casos pasan, igual que en `eval/results/20261015-001031.json`. Se generan
   `eval/results/latest-nube.md` y `<fecha>-nube.json`. `latest.md` no cambia.
3. En LangSmith, abrir el proyecto `agente-sql-telemetria-nube`.
   **Se espera**: las ejecuciones de los 8 casos.

## Escenario 3: la app pública responde (SC-001, SC-004, SC-005)

1. En share.streamlit.io, crear la app:
   - Repositorio `Mind-fever/telemetry-sql-agent`, rama `master`, archivo `app/streamlit_app.py`.
   - Subdominio propio.
   - En Advanced settings: Python 3.13 y los Secrets del contrato.
   **Se espera**: la construcción termina. En el registro aparece Python 3.13 (R6).
2. Abrir la dirección pública desde otro dispositivo (otra computadora o un celular), sin sesión iniciada.
   **Se espera**: la interfaz de chat. En la barra lateral dice "Trazas en LangSmith: activadas".
3. Hacer una pregunta de cada tipo:
   - Datos: "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?"
   - Documentos: "¿Cada cuánto se lubrican los rodamientos de un motor?"
   - Combinada: "¿Qué procedimiento corresponde a la última alarma de vibración del compresor C-201?"
   - Sin respaldo: "¿Cuánto cuesta un rodamiento de repuesto?"
   - Modificación: "Borrá todas las alarmas de la base"

   **Se espera**:
   - Cada respuesta indica su fuente, y la de documentos indica archivo y página.
   - La pregunta sin respaldo dice que no tiene la información.
   - La de modificación se rechaza, y en Neon siguen las 171 alarmas.
   - La primera respuesta tarda menos de 60 s y las demás menos de 20 s.
4. En LangSmith, en el proyecto `agente-sql-telemetria-nube`.
   **Se espera**: las 5 ejecuciones, con la ruta elegida y la consulta generada.

**Punto de corte**: si a las 20:00 del jueves 15 no se cumplen los escenarios 1 y 3, se abandona según la
especificación.

## Escenario 4: la versión local sigue igual (SC-006)

1. Sin variables extra en el entorno, correr `pytest`.
   **Se espera**: pasan las mismas pruebas que antes de la 002.
2. Correr `streamlit run app/streamlit_app.py` y hacer una pregunta.
   **Se espera**: responde con la base de Docker.

## Escenario 5: reactivar y apagar (SC-007, FR-006)

1. Después de 12 horas sin visitas, abrir la dirección pública.
   **Se espera**: un aviso de app dormida con un botón para despertarla. En menos de 10 minutos la app
   responde.
2. Después del 30 de octubre de 2026, seguir el paso del README.
   **Se espera**: la app queda borrada o privada, y la clave de Gemini de la nube queda regenerada o borrada.
