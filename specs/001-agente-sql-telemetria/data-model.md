# Modelo de datos: Agente SQL de Telemetría y Mantenimiento Industrial

**Fecha**: 2026-10-09 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Todos los datos son sintéticos. Cada tabla de negocio tiene más de 15 registros (FR-001). El
seed usa una semilla fija, así que dos corridas generan exactamente los mismos datos.

## Tablas de negocio (las consulta el agente por SQL)

### areas
Áreas de proceso de una planta ficticia (por ejemplo "Bombeo de agua", "Compresión de aire").

| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| nombre | text, único | |
| descripcion | text | |

Volumen real del seed: 18 filas.

### tecnicos
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| nombre | text | nombres inventados |
| especialidad | text | mecanica, electrica, instrumentacion, lubricacion |
| turno | text | manana, tarde, noche (sin tilde ni eñe, como todos los valores de opciones fijas) |
| fecha_ingreso | date | |

Volumen real del seed: 20 filas.

### equipos
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| codigo | text, único | etiqueta tipo `P-101`, `C-201`, `M-301` |
| nombre | text | |
| tipo | text | bomba, motor, compresor, ventilador, transformador |
| fabricante | text | fabricantes ficticios |
| area_id | int FK -> areas | |
| fecha_instalacion | date | |
| estado | text | operativo, en mantenimiento, fuera de servicio |
| criticidad | text | alta, media, baja |

Volumen real del seed: 40 filas.

### sensores
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| equipo_id | int FK -> equipos | |
| magnitud | text | temperatura, vibracion, presion, corriente |
| unidad | text | °C, mm/s, bar, A |
| umbral_alerta | numeric | valor a partir del cual se genera alarma |
| umbral_critico | numeric | valor a partir del cual la alarma es crítica |

Volumen real del seed: 108 filas (2 o 3 sensores por equipo según su tipo).

### lecturas
| Columna | Tipo | Notas |
|---|---|---|
| id | bigserial PK | |
| sensor_id | int FK -> sensores | |
| fecha_hora | timestamptz | |
| valor | numeric | |

Volumen real del seed: 38.880 filas (108 sensores, 30 días, una lectura cada 2 horas), con
una evolución diaria y algunos episodios de valores elevados que dan lugar a alarmas.

### alarmas
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| sensor_id | int FK -> sensores | |
| lectura_id | bigint FK -> lecturas | lectura que la originó |
| severidad | text | alerta, critica |
| fecha_inicio | timestamptz | |
| fecha_fin | timestamptz, nulo | nulo si sigue abierta |
| descripcion | text | |

Volumen real del seed: 171 filas, generadas de forma determinista a partir de las lecturas
que superan los umbrales, así que son coherentes con ellas.

### ordenes_mantenimiento
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| equipo_id | int FK -> equipos | |
| tecnico_id | int FK -> tecnicos | |
| alarma_id | int FK -> alarmas, nulo | solo en las correctivas originadas por una alarma |
| tipo | text | preventivo, correctivo |
| prioridad | text | alta, media, baja |
| estado | text | abierta, en curso, cerrada |
| fecha_creacion | date | |
| fecha_cierre | date, nulo | |
| descripcion | text | |
| horas_trabajadas | numeric, nulo | |

Volumen real del seed: 153 filas.

## Relaciones

```text
areas 1---N equipos 1---N sensores 1---N lecturas
                    |             \---N alarmas ---0..1 ordenes_mantenimiento
                    \---N ordenes_mantenimiento N---1 tecnicos
```

## Tabla de documentos (la usa el RAG, no el agente por SQL)

### doc_chunks
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| archivo | text | nombre del PDF |
| pagina | int | número de página de origen |
| orden | int | posición del fragmento dentro de la página |
| texto | text | |
| embedding | vector(768) | |

La tabla no está en la lista de tablas permitidas para el SQL generado por el modelo.

## Reglas de validación

- Las claves foráneas se declaran en el esquema y el seed las respeta.
- `umbral_critico` es mayor que `umbral_alerta` en cada sensor.
- `fecha_cierre` solo existe cuando `estado = 'cerrada'`.
- Una alarma con `fecha_fin` nulo está abierta.
- Los códigos de equipo del seed coinciden con los que nombran los PDF, de modo que las
  preguntas combinadas sean posibles.

## Descripción para el modelo

Cada tabla y columna lleva un comentario en el esquema (`COMMENT ON`), en castellano. El
agente arma su descripción del esquema a partir de esos comentarios y de los nombres, y se la
da al modelo al generar SQL.
