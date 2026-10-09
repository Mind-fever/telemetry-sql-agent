"""Crea el esquema y el rol de solo lectura. Recrea todo desde cero.

Uso: python scripts/setup_db.py
Requiere DATABASE_URL (con permisos de administracion) y DATABASE_URL_RO (define el usuario
y la clave del rol agent_ro) en el entorno o en .env.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from telemetry_agent.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.database_url or not settings.database_url_ro:
        raise SystemExit("Faltan DATABASE_URL y/o DATABASE_URL_RO (ver .env.example).")

    ro = conninfo_to_dict(settings.database_url_ro)
    role = ro.get("user") or "agent_ro"
    password = ro.get("password")
    if role != "agent_ro" or not password:
        raise SystemExit("DATABASE_URL_RO debe usar el usuario agent_ro y una clave.")

    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        print("Esquema creado.")

        exists = conn.execute("select 1 from pg_roles where rolname = %s", (role,)).fetchone()
        if exists:
            conn.execute(
                sql.SQL("alter role {} with login password {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
        else:
            conn.execute(
                sql.SQL("create role {} with login password {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
        conn.execute((ROOT / "db" / "roles.sql").read_text(encoding="utf-8"))
        print("Rol agent_ro listo con permisos de solo lectura.")


if __name__ == "__main__":
    main()
