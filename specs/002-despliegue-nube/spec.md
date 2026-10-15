# Feature Specification: Despliegue del agente en la nube

**Feature Branch**: `002-despliegue-nube`

**Created**: 2026-10-15

**Status**: Implementada y desplegada (2026-10-15)

**Input**: User description: "Desplegar el agente en la nube para cumplir el criterio de promoción de despliegue. La interfaz de chat tiene que quedar accesible por internet y la base de datos en un servicio externo, los dos gratuitos. El agente tiene que comportarse igual que la versión local, con las mismas protecciones de solo lectura y respondiendo las mismas preguntas. La van a usar solo el autor y el jurado del trabajo. La versión local con Docker tiene que seguir funcionando igual que ahora."

## Clarifications

### Session 2026-10-15

- Q: ¿La aplicación desplegada está restringida a cuentas autorizadas o la abre cualquiera con el enlace? → A: Pública mientras dura la evaluación, hasta el 30 de octubre de 2026 inclusive (la última fecha de coloquio). Después se apaga o se restringe. La cuota se protege con la clave del modelo aparte.
- Q: ¿Qué tiene que estar terminado el jueves a las 20:00 para que la funcionalidad no se abandone? → A: Que la aplicación responda desde su dirección pública (SC-001) y que la base remota coincida con la local (SC-002). La evidencia, el README y el informe se terminan después, el mismo jueves o el viernes antes de la entrega.
- Q: ¿Qué casos de la evaluación se corren contra la base remota para comprobar que da lo mismo que la local? → A: 8 casos del conjunto principal, uno por categoría (sql, edge, docs, refuse, both, no_evidence, none y follow_up), elegidos de antemano y comparados con su resultado local.
- Q: ¿Las trazas de la aplicación en la nube van al mismo proyecto de LangSmith que las locales o a uno propio? → A: A uno propio, `agente-sql-telemetria-nube`. El proyecto local (`agente-sql-telemetria`) no cambia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El jurado usa el agente desde un enlace (Priority: P1)

Un integrante del jurado abre el enlace de la aplicación en su navegador, sin instalar nada, y hace
preguntas sobre la planta. El agente responde igual que en la máquina del autor: consulta los datos, los
documentos o ambos, indica la fuente y rechaza los pedidos de modificar datos.

**Why this priority**: es lo que pide el criterio de promoción. Sin esto la funcionalidad no aporta nada.

**Independent Test**: desde otro dispositivo, distinto de la computadora del autor, abrir el enlace y hacer una pregunta
de cada tipo (datos, documentos, combinada, sin respaldo y pedido de modificación). Cada una se responde
como en la versión local.

**Acceptance Scenarios**:

1. **Given** la aplicación desplegada, **When** se abre el enlace desde un navegador, **Then** aparece la
   interfaz de chat lista para recibir preguntas.
2. **Given** la interfaz abierta, **When** se pregunta por un dato de telemetría o mantenimiento, **Then**
   el agente responde con el valor que está en la base remota e indica que la fuente son los datos.
3. **Given** la interfaz abierta, **When** se pregunta por un procedimiento de los manuales, **Then** el
   agente responde con el contenido del documento e indica el archivo y la página.
4. **Given** la interfaz abierta, **When** se pide borrar o modificar datos, **Then** el agente lo rechaza
   y los datos de la base remota quedan iguales.
5. **Given** la base remota sin uso durante horas, **When** llega la primera pregunta, **Then** el agente
   responde aunque tarde más que de costumbre, sin mostrar un error.

---

### User Story 2 - El autor comprueba que la versión en la nube es equivalente (Priority: P2)

El autor verifica que la base remota tiene los mismos datos que la local y que el agente conectado a ella
pasa los mismos casos de evaluación. Deja la evidencia (captura, traza y resultado de los casos) en el
informe.

**Why this priority**: el criterio de promoción se defiende con evidencia. Sin la comparación, no se puede
afirmar que la versión en la nube es la misma que se evaluó.

**Independent Test**: comparar la cantidad de filas de cada tabla entre las dos bases y correr los 8
casos de SC-003 contra la base remota.

**Acceptance Scenarios**:

1. **Given** la base remota cargada, **When** se cuentan las filas de cada tabla, **Then** coinciden con
   la base local (18, 20, 40, 108, 38.880, 171 y 153 filas, y 18 fragmentos de documentos).
2. **Given** el agente conectado a la base remota, **When** se corren los 8 casos elegidos (uno por
   categoría), **Then** cada caso obtiene el mismo resultado que contra la base local.
3. **Given** una pregunta hecha desde la aplicación desplegada, **When** se revisan las trazas, **Then**
   la ejecución aparece en el proyecto `agente-sql-telemetria-nube`, con la fuente elegida y la consulta
   generada.

---

### User Story 3 - La versión local sigue igual (Priority: P3)

El autor, o un tercero que sigue el README, levanta el proyecto en su máquina con la base de Docker,
igual que antes de esta funcionalidad.

**Why this priority**: la entrega actual ya cumple el enunciado con la versión local. El despliegue no
puede ponerla en riesgo.

**Independent Test**: sin las variables de la nube, levantar el proyecto siguiendo el README, correr las
pruebas automáticas y hacer una pregunta. Todo funciona contra la base local.

**Acceptance Scenarios**:

1. **Given** la configuración local sin cambios, **When** se inicia la aplicación, **Then** se conecta a
   la base de Docker y no a la remota.
2. **Given** el proyecto con los cambios de esta funcionalidad, **When** se corren las pruebas
   automáticas, **Then** pasan las mismas que antes.

---

### Edge Cases

- ¿Qué pasa si el enlace llega a alguien ajeno al trabajo? Puede usar la aplicación, porque es pública
  hasta el 30 de octubre (FR-006). Solo puede leer, igual que cualquier usuario, y lo que gasta sale de la
  clave aparte, no de la cuota del autor.
- ¿Qué pasa si se agota la cuota diaria del modelo mientras el jurado prueba la aplicación? El agente
  muestra el mismo aviso de cuota agotada que en la versión local, sin un error técnico.
- ¿Qué pasa si la base remota tarda en despertar? La primera pregunta espera la conexión en lugar de
  fallar (ver FR-008).
- ¿Qué pasa si falta una clave o la conexión en la configuración de la nube? La aplicación muestra un
  mensaje que dice qué falta, sin exponer valores secretos.
- ¿Qué pasa si se intenta escribir en la base remota con las credenciales que usa la aplicación? La
  base lo rechaza, porque la aplicación solo tiene credenciales de lectura.
- ¿Qué pasa si el servicio gratuito pausa la aplicación o la base por falta de uso antes del coloquio?
  El autor puede reactivarla siguiendo un paso documentado en el README.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La interfaz de chat MUST quedar accesible desde internet en una dirección fija, sin que
  quien la usa tenga que instalar nada.
- **FR-002**: La base de datos MUST estar en un servicio externo, con los mismos datos, tablas y
  fragmentos de documentos que la base local.
- **FR-003**: El servicio de la interfaz y el de la base MUST ser gratuitos, sin tarjeta de crédito.
- **FR-004**: El agente desplegado MUST ser el mismo que el local: el mismo comportamiento, los mismos
  prompts y las mismas reglas de respuesta. Esta funcionalidad MUST NOT cambiar cómo responde el agente.
- **FR-005**: La aplicación desplegada MUST conectarse a la base remota solo con un usuario de lectura.
  Las credenciales con permiso de escritura MUST NOT cargarse en el servicio de la interfaz. Se mantienen
  el validador de consultas, el límite de filas y el tiempo máximo por consulta.
- **FR-006**: La aplicación desplegada MUST poder abrirse sin iniciar sesión, por cualquiera que tenga el
  enlace, hasta el 30 de octubre de 2026 inclusive. Después de esa fecha MUST apagarse o restringirse.
  La cuota del modelo se protege con la clave aparte de FR-011, no con el control de acceso.
- **FR-007**: Las ejecuciones de la aplicación desplegada MUST quedar trazadas en LangSmith, en un
  proyecto propio llamado `agente-sql-telemetria-nube`, separado del proyecto local
  (`agente-sql-telemetria`), que no cambia.
- **FR-008**: Si la base remota está suspendida por falta de uso, la primera pregunta MUST esperar a que
  se reactive y responder, sin mostrar un error.
- **FR-009**: La configuración de la nube (claves y conexión) MUST cargarse en los paneles de cada
  servicio. Ningún secreto MUST quedar en el repositorio.
- **FR-010**: La versión local MUST seguir funcionando sin cambios en su configuración: con las
  variables locales, la aplicación usa la base de Docker.
- **FR-011**: La aplicación desplegada MUST usar una clave del modelo distinta de la que usa el autor
  para desarrollo y evaluación, para que el uso en la nube no agote la cuota local.
- **FR-012**: El README MUST explicar cómo reproducir el despliegue (crear la base remota, cargarla y
  publicar la aplicación) y cómo reactivar los servicios si se pausan.
- **FR-013**: El informe MUST incluir el criterio de despliegue con su evidencia: la dirección pública,
  una captura de la aplicación respondiendo, una traza de esa ejecución y el resultado de los casos de
  evaluación corridos contra la base remota.

### Key Entities

- **Base remota**: copia de la base local en un servicio externo. Mismas tablas, mismas filas, mismos
  fragmentos de documentos y el mismo usuario de solo lectura.
- **Aplicación desplegada**: la interfaz de chat con el agente, publicada en una dirección fija.
- **Configuración de la nube**: claves del modelo y de las trazas, más la conexión de solo lectura a la
  base remota. Vive en los paneles de los servicios, no en el repositorio.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde otro dispositivo, distinto de la computadora del autor (otra computadora o un celular), la aplicación responde correctamente una
  pregunta de cada uno de los cinco tipos (datos, documentos, combinada, sin respaldo y pedido de
  modificación).
- **SC-002**: Las 8 tablas de la base remota (incluida la de fragmentos de documentos) tienen la misma cantidad de filas que la base
  local.
- **SC-003**: 8 casos del conjunto principal de evaluación, uno por categoría (sql, edge, docs, refuse,
  both, no_evidence, none y follow_up) y elegidos antes de correrlos, obtienen contra la base remota el
  mismo resultado caso por caso que contra la base local. El conjunto reservado no se usa.
- **SC-004**: El 100% de los pedidos de modificación hechos desde la aplicación desplegada se rechazan y
  los datos remotos quedan intactos.
- **SC-005**: Con la base remota recién despertada, la primera respuesta llega en menos de 60 segundos;
  las siguientes, en el mismo tiempo que la versión local (menos de 20 segundos).
- **SC-006**: Con la configuración local, las pruebas automáticas pasan igual que antes de esta
  funcionalidad.
- **SC-007**: La aplicación sigue disponible desde su enlace en las fechas del coloquio (23 y 30 de
  octubre de 2026), o se reactiva en menos de 10 minutos siguiendo el README.

## Assumptions

- Plazo: el jueves 15 de octubre de 2026 a las 20:00 tienen que cumplirse SC-001 (la aplicación responde
  desde su dirección pública) y SC-002 (la base remota coincide con la local). El resto de los criterios
  (evidencia, README e informe) puede terminarse después, hasta la entrega del viernes 16 a las 23:59. Si
  a las 20:00 no se cumplen SC-001 y SC-002, se abandona: la rama `002-despliegue-nube` no se fusiona, se anota en las tareas qué se
  intentó y por qué se descartó, y se entrega `master` como está. La versión local ya cumple el enunciado.
- La aplicación es pública solo mientras dura la evaluación. **Después del 30 de octubre de 2026, el autor
  tiene que apagar la aplicación o restringir el acceso**, y regenerar o borrar la clave del modelo que usa
  la nube.
- El autor crea las cuentas de los servicios y carga las claves en sus paneles. Las credenciales no se
  pegan en el chat de desarrollo.
- Se usa solo con fines de demostración y evaluación: pocos usuarios a la vez (el autor y el jurado) y
  pocas preguntas por día.
- Los documentos PDF no se suben a la base remota. Se cargan sus fragmentos ya procesados, igual que en la
  base local.
- La evaluación completa no se corre contra la base remota, para no gastar la cuota diaria del modelo
  (una evaluación completa usa unos 110 de los 500 pedidos diarios). Alcanza con los 8 casos de SC-003,
  unos 20 pedidos.
- Se acepta que la base remota se suspenda por falta de uso y tarde unos segundos en despertar.
- Fuera de alcance: dominio propio, alta disponibilidad, despliegue automático en cada cambio y control de
  acceso por cuenta durante la evaluación.
