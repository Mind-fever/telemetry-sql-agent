"""Validador de SQL (principio I de la constitucion: solo lectura).

Es la primera de varias capas. Las otras estan en la base: el rol agent_ro solo tiene SELECT,
la transaccion es de solo lectura y hay un timeout. Si este validador tuviera un hueco, esas
capas siguen impidiendo escribir.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from .config import ALLOWED_TABLES

# Tipos de nodo que indican escritura, cambio de estructura o comandos del servidor.
FORBIDDEN_NODES: tuple[type, ...] = tuple(
    t for t in (
        getattr(exp, name, None)
        for name in (
            "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Merge",
            "TruncateTable", "Command", "Copy", "Grant", "Revoke", "Set", "Use", "Transaction",
            "Commit", "Rollback", "Into", "Lock", "Analyze", "Pragma", "Kill", "Execute",
        )
    ) if t is not None
)

FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "lo_import",
    "lo_export", "dblink", "set_config", "pg_terminate_backend", "pg_cancel_backend",
    "pg_reload_conf", "current_setting", "txid_current", "pg_advisory_lock", "pg_notify",
}


@dataclass
class GuardResult:
    ok: bool
    reason: str = ""
    # "not_read_only": el pedido intenta escribir o cambiar estructura (se rechaza, no se reintenta)
    # "invalid": consulta mal formada o fuera de las reglas (el modelo puede corregirla)
    kind: str = ""
    sql: str = ""


def validate_sql(query: str) -> GuardResult:
    text = (query or "").strip().rstrip(";").strip()
    if not text:
        return GuardResult(False, "La consulta esta vacia.", "invalid")

    try:
        statements = sqlglot.parse(text, read="postgres")
    except ParseError as exc:
        return GuardResult(False, f"No se pudo interpretar la consulta: {exc}", "invalid")

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return GuardResult(False, "Se permite una sola sentencia por consulta.", "invalid")
    tree = statements[0]

    for node in tree.walk():
        if isinstance(node, FORBIDDEN_NODES):
            return GuardResult(False, "Solo se permiten consultas de lectura (SELECT).", "not_read_only")

    if not isinstance(tree, (exp.Select, exp.Union, exp.Except, exp.Intersect, exp.Subquery)):
        return GuardResult(False, "Solo se permiten consultas de lectura (SELECT).", "not_read_only")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if table.args.get("db") or table.args.get("catalog"):
            return GuardResult(False, f"No se permite el esquema explicito en la tabla '{table.sql()}'.", "invalid")
        if name in cte_names:
            continue
        if name not in ALLOWED_TABLES:
            return GuardResult(
                False,
                f"La tabla '{table.name}' no esta permitida. Tablas disponibles: {', '.join(ALLOWED_TABLES)}.",
                "invalid",
            )

    for func in tree.find_all(exp.Func):
        fname = (func.sql_name() if hasattr(func, "sql_name") else "").lower()
        anon = func.name.lower() if isinstance(func, exp.Anonymous) else ""
        for candidate in (fname, anon):
            if candidate in FORBIDDEN_FUNCTIONS or candidate.startswith("pg_"):
                return GuardResult(False, f"La funcion '{candidate}' no esta permitida.", "invalid")

    return GuardResult(True, "", "", text)
