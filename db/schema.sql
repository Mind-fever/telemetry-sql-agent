-- Esquema del agente SQL de telemetria y mantenimiento industrial.
-- Todos los datos son ficticios. Ejecutar con scripts/setup_db.py (recrea todo desde cero).

create extension if not exists vector;

drop table if exists doc_chunks cascade;
drop table if exists ordenes_mantenimiento cascade;
drop table if exists alarmas cascade;
drop table if exists lecturas cascade;
drop table if exists sensores cascade;
drop table if exists equipos cascade;
drop table if exists tecnicos cascade;
drop table if exists areas cascade;

create table areas (
    id          serial primary key,
    nombre      text not null unique,
    descripcion text not null
);
comment on table areas is 'Areas de proceso de la planta ficticia. Cada equipo pertenece a un area.';
comment on column areas.id is 'Identificador del area.';
comment on column areas.nombre is 'Nombre del area, por ejemplo Bombeo de agua.';
comment on column areas.descripcion is 'Descripcion breve de lo que se hace en el area.';

create table tecnicos (
    id            serial primary key,
    nombre        text not null,
    especialidad  text not null check (especialidad in ('mecanica', 'electrica', 'instrumentacion', 'lubricacion')),
    turno         text not null check (turno in ('manana', 'tarde', 'noche')),
    fecha_ingreso date not null
);
comment on table tecnicos is 'Tecnicos de mantenimiento que ejecutan las ordenes de trabajo.';
comment on column tecnicos.id is 'Identificador del tecnico.';
comment on column tecnicos.nombre is 'Nombre y apellido (ficticios).';
comment on column tecnicos.especialidad is 'Especialidad: mecanica, electrica, instrumentacion o lubricacion.';
comment on column tecnicos.turno is 'Turno de trabajo: manana, tarde o noche.';
comment on column tecnicos.fecha_ingreso is 'Fecha en que ingreso a la empresa.';

create table equipos (
    id                serial primary key,
    codigo            text not null unique,
    nombre            text not null,
    tipo              text not null check (tipo in ('bomba', 'motor', 'compresor', 'ventilador', 'transformador')),
    fabricante        text not null,
    area_id           int not null references areas (id),
    fecha_instalacion date not null,
    estado            text not null check (estado in ('operativo', 'en mantenimiento', 'fuera de servicio')),
    criticidad        text not null check (criticidad in ('alta', 'media', 'baja'))
);
comment on table equipos is 'Maquinas y activos de la planta (bombas, motores, compresores, ventiladores, transformadores).';
comment on column equipos.id is 'Identificador interno del equipo.';
comment on column equipos.codigo is 'Etiqueta del equipo en la planta, por ejemplo P-101 (bomba), C-201 (compresor), M-301 (motor).';
comment on column equipos.nombre is 'Nombre descriptivo del equipo.';
comment on column equipos.tipo is 'Tipo de equipo: bomba, motor, compresor, ventilador o transformador.';
comment on column equipos.fabricante is 'Fabricante (ficticio).';
comment on column equipos.area_id is 'Area donde esta instalado el equipo (areas.id).';
comment on column equipos.fecha_instalacion is 'Fecha de instalacion.';
comment on column equipos.estado is 'Estado actual: operativo, en mantenimiento o fuera de servicio.';
comment on column equipos.criticidad is 'Importancia del equipo para el proceso: alta, media o baja.';

create table sensores (
    id             serial primary key,
    equipo_id      int not null references equipos (id),
    magnitud       text not null check (magnitud in ('temperatura', 'vibracion', 'presion', 'corriente')),
    unidad         text not null,
    umbral_alerta  numeric not null,
    umbral_critico numeric not null,
    check (umbral_critico > umbral_alerta)
);
comment on table sensores is 'Sensores instalados en los equipos. Cada sensor mide una magnitud.';
comment on column sensores.id is 'Identificador del sensor.';
comment on column sensores.equipo_id is 'Equipo donde esta instalado (equipos.id).';
comment on column sensores.magnitud is 'Magnitud medida: temperatura, vibracion, presion o corriente.';
comment on column sensores.unidad is 'Unidad de medida: C (grados), mm/s, bar o A.';
comment on column sensores.umbral_alerta is 'Valor a partir del cual se genera una alarma de severidad alerta.';
comment on column sensores.umbral_critico is 'Valor a partir del cual la alarma es de severidad critica.';

create table lecturas (
    id         bigserial primary key,
    sensor_id  int not null references sensores (id),
    fecha_hora timestamptz not null,
    valor      numeric not null
);
create index lecturas_sensor_fecha_idx on lecturas (sensor_id, fecha_hora);
comment on table lecturas is 'Mediciones de los sensores, una cada 2 horas. Es la tabla mas voluminosa.';
comment on column lecturas.id is 'Identificador de la lectura.';
comment on column lecturas.sensor_id is 'Sensor que realizo la medicion (sensores.id).';
comment on column lecturas.fecha_hora is 'Momento de la medicion.';
comment on column lecturas.valor is 'Valor medido, en la unidad del sensor.';

create table alarmas (
    id           serial primary key,
    sensor_id    int not null references sensores (id),
    lectura_id   bigint not null references lecturas (id),
    severidad    text not null check (severidad in ('alerta', 'critica')),
    fecha_inicio timestamptz not null,
    fecha_fin    timestamptz,
    descripcion  text not null
);
comment on table alarmas is 'Eventos generados cuando las lecturas de un sensor superan sus umbrales.';
comment on column alarmas.id is 'Identificador de la alarma.';
comment on column alarmas.sensor_id is 'Sensor que genero la alarma (sensores.id).';
comment on column alarmas.lectura_id is 'Primera lectura que supero el umbral (lecturas.id).';
comment on column alarmas.severidad is 'alerta si supero umbral_alerta; critica si supero umbral_critico.';
comment on column alarmas.fecha_inicio is 'Momento en que comenzo la alarma.';
comment on column alarmas.fecha_fin is 'Momento en que termino. Es nulo si la alarma sigue abierta.';
comment on column alarmas.descripcion is 'Texto descriptivo de la alarma.';

create table ordenes_mantenimiento (
    id               serial primary key,
    equipo_id        int not null references equipos (id),
    tecnico_id       int not null references tecnicos (id),
    alarma_id        int references alarmas (id),
    tipo             text not null check (tipo in ('preventivo', 'correctivo')),
    prioridad        text not null check (prioridad in ('alta', 'media', 'baja')),
    estado           text not null check (estado in ('abierta', 'en curso', 'cerrada')),
    fecha_creacion   date not null,
    fecha_cierre     date,
    descripcion      text not null,
    horas_trabajadas numeric,
    check ((estado = 'cerrada') = (fecha_cierre is not null))
);
comment on table ordenes_mantenimiento is 'Ordenes de trabajo de mantenimiento sobre los equipos.';
comment on column ordenes_mantenimiento.id is 'Identificador de la orden.';
comment on column ordenes_mantenimiento.equipo_id is 'Equipo sobre el que se trabaja (equipos.id).';
comment on column ordenes_mantenimiento.tecnico_id is 'Tecnico asignado (tecnicos.id).';
comment on column ordenes_mantenimiento.alarma_id is 'Alarma que origino la orden (alarmas.id). Es nulo en las preventivas.';
comment on column ordenes_mantenimiento.tipo is 'preventivo (programado) o correctivo (por una falla o alarma).';
comment on column ordenes_mantenimiento.prioridad is 'Prioridad: alta, media o baja.';
comment on column ordenes_mantenimiento.estado is 'Estado: abierta, en curso o cerrada.';
comment on column ordenes_mantenimiento.fecha_creacion is 'Fecha en que se creo la orden.';
comment on column ordenes_mantenimiento.fecha_cierre is 'Fecha de cierre. Solo tiene valor si el estado es cerrada.';
comment on column ordenes_mantenimiento.descripcion is 'Descripcion del trabajo.';
comment on column ordenes_mantenimiento.horas_trabajadas is 'Horas de trabajo registradas. Es nulo si la orden esta abierta.';

-- Fragmentos de los PDF para la busqueda semantica (RAG). No es una tabla de negocio:
-- el agente no la consulta con SQL generado por el modelo.
create table doc_chunks (
    id        serial primary key,
    archivo   text not null,
    pagina    int not null,
    orden     int not null,
    texto     text not null,
    embedding vector(768) not null
);
comment on table doc_chunks is 'Fragmentos de los documentos PDF con su embedding, para recuperacion por similitud.';
