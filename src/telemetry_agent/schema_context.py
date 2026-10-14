"""Descripcion del esquema para el modelo, armada a partir de la propia base.

Usa los COMMENT ON del esquema, las claves foraneas y los valores posibles de las columnas
categoricas. Asi el modelo ve los valores exactos ('critica', 'bomba', 'Bombeo de agua') y no los
inventa, y la descripcion nunca se desactualiza respecto de la base.
"""

from __future__ import annotations

from functools import lru_cache

from .config import ALLOWED_TABLES, TIMEZONE
from .db import connect_readonly

MAX_DISTINCT = 20

_COLUMNS_SQL = """
select c.relname, a.attname, format_type(a.atttypid, a.atttypmod),
       col_description(c.oid, a.attnum), obj_description(c.oid, 'pg_class')
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
join pg_attribute a on a.attrelid = c.oid
where n.nspname = 'public' and c.relkind = 'r' and c.relname = any(%s)
  and a.attnum > 0 and not a.attisdropped
order by c.relname, a.attnum
"""

_FK_SQL = """
select c.relname, pg_get_constraintdef(k.oid)
from pg_constraint k
join pg_class c on c.oid = k.conrelid
join pg_namespace n on n.oid = c.relnamespace
where k.contype = 'f' and n.nspname = 'public' and c.relname = any(%s)
order by c.relname
"""


@lru_cache(maxsize=1)
def build_schema_context() -> str:
    tables = list(ALLOWED_TABLES)
    lines: list[str] = []
    text_columns: list[tuple[str, str]] = []
    with connect_readonly() as conn:
        rows = conn.execute(_COLUMNS_SQL, (tables,)).fetchall()
        fks = conn.execute(_FK_SQL, (tables,)).fetchall()

        current = None
        for table, column, ctype, col_comment, table_comment in rows:
            if table != current:
                current = table
                lines.append(f"\nTabla {table}: {table_comment or ''}".rstrip())
            lines.append(f"  - {column} ({ctype}): {col_comment or ''}".rstrip())
            if ctype == "text":
                text_columns.append((table, column))

        lines.append("\nRelaciones (claves foraneas):")
        for table, definition in fks:
            lines.append(f"  - {table}: {definition}")

        lines.append("\nValores posibles de las columnas categoricas (usar exactamente estos textos):")
        for table, column in text_columns:
            if column in ("descripcion", "nombre") and table != "areas":
                continue
            values = [r[0] for r in conn.execute(
                f"select distinct {column} from {table} where {column} is not null order by 1 limit %s",
                (MAX_DISTINCT + 1,),
            ).fetchall()]
            if 0 < len(values) <= MAX_DISTINCT:
                lines.append(f"  - {table}.{column}: " + ", ".join(repr(v) for v in values))

        codes = [r[0] for r in conn.execute("select codigo from equipos order by codigo").fetchall()]
        lines.append("  - equipos.codigo: " + ", ".join(codes))

        lo, hi = conn.execute(
            "select min(fecha_hora) at time zone %s, max(fecha_hora) at time zone %s from lecturas",
            (TIMEZONE, TIMEZONE),
        ).fetchone()
        conn.rollback()

    if lo and hi:
        lines.append(
            f"\nLos datos de lecturas van desde {lo.isoformat()} hasta {hi.isoformat()}. "
            f"La fecha de referencia ('hoy', 'ahora') es {hi.date().isoformat()}; "
            f"'este mes' y 'el mes pasado' se refieren al mes de esa fecha de referencia. "
            f"Las columnas de fecha con hora son timestamptz y se interpretan en la zona horaria {TIMEZONE} (UTC-3)."
        )
    return "\n".join(lines).strip()


def data_period() -> str:
    """Periodo que cubren los datos, como 'AAAA-MM-DD a AAAA-MM-DD' (primera y ultima lectura).

    La sintesis lo usa para avisar cuando una pregunta cae fuera de ese periodo (FR-017).
    """
    with connect_readonly() as conn:
        lo, hi = conn.execute(
            "select min(fecha_hora) at time zone %s, max(fecha_hora) at time zone %s from lecturas",
            (TIMEZONE, TIMEZONE),
        ).fetchone()
        conn.rollback()
    return f"{lo.date().isoformat()} a {hi.date().isoformat()}" if lo and hi else ""


def reference_date() -> str:
    """Fecha de referencia de los datos (la ultima lectura), en formato ISO."""
    with connect_readonly() as conn:
        (hi,) = conn.execute(
            "select max(fecha_hora) at time zone %s from lecturas", (TIMEZONE,)
        ).fetchone()
        conn.rollback()
    return hi.date().isoformat() if hi else ""
