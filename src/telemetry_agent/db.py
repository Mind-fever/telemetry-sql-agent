"""Acceso a la base de datos.

Hay dos caminos y no se mezclan:
- connect_admin(): con permisos de escritura, solo para los scripts de carga.
- run_readonly(): con el rol agent_ro, una transaccion de solo lectura, timeout y tope de filas.
  Es lo unico que usa el agente (principio I).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql

from .config import TIMEZONE, get_settings


def connect_admin() -> psycopg.Connection:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("Falta DATABASE_URL en el entorno (ver .env.example).")
    return psycopg.connect(url)


def connect_readonly() -> psycopg.Connection:
    url = get_settings().database_url_ro
    if not url:
        raise RuntimeError("Falta DATABASE_URL_RO en el entorno (ver .env.example).")
    return psycopg.connect(url)


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool


def run_readonly(query: str, params: tuple | None = None, max_rows: int | None = None) -> QueryResult:
    """Ejecuta una consulta de lectura con todas las protecciones.

    - La conexion usa el rol agent_ro (solo SELECT).
    - La transaccion se abre en modo READ ONLY.
    - statement_timeout corta las consultas lentas.
    - Se piden max_rows + 1 filas para saber si hubo recorte.
    """
    settings = get_settings()
    limit = max_rows or settings.sql_max_rows
    with connect_readonly() as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("set local statement_timeout = {}").format(sql.Literal(settings.sql_timeout_ms))
            )
            cur.execute(sql.SQL("set local timezone = {}").format(sql.Literal(TIMEZONE)))
            cur.execute(query, params)  # type: ignore[arg-type]
            columns = [d.name for d in cur.description] if cur.description else []
            fetched = cur.fetchmany(limit + 1)
        conn.rollback()
    truncated = len(fetched) > limit
    fetched = fetched[:limit]
    rows = [dict(zip(columns, _jsonable(row))) for row in fetched]
    return QueryResult(columns=columns, rows=rows, truncated=truncated)


def _jsonable(row: tuple) -> list[Any]:
    """Convierte fechas y decimales a tipos simples para mostrar y comparar."""
    out: list[Any] = []
    for value in row:
        if hasattr(value, "isoformat"):
            out.append(value.isoformat())
        elif value.__class__.__name__ == "Decimal":
            out.append(float(value))
        else:
            out.append(value)
    return out
