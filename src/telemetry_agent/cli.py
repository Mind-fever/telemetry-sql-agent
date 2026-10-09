"""Preguntarle al agente desde la terminal.

Uso:
    python -m telemetry_agent.cli "¿Cuántas alarmas críticas hubo en septiembre?"
    python -m telemetry_agent.cli            (modo conversacion; salir con Ctrl+C o una linea vacia)
"""

from __future__ import annotations

import sys
import uuid

from .graph import Agent
from .models import AgentResponse

ROUTE_LABEL = {
    "sql": "base de datos",
    "docs": "documentos",
    "both": "base de datos y documentos",
    "none": "ninguna",
    "refuse": "rechazo (solo lectura)",
}


def show(res: AgentResponse) -> None:
    print(f"\n{res.answer}\n")
    print(f"[fuente: {ROUTE_LABEL.get(res.route, res.route)}] {res.route_reason}")
    if res.sql:
        print(f"[sql]\n{res.sql}")
    if res.rows is not None:
        shown = res.rows[:5]
        print(f"[filas: {len(res.rows)}{'+' if res.rows_truncated else ''}] {shown}")
    for s in res.sources:
        print(f"[documento] {s.archivo}, pagina {s.pagina}")
    if res.error:
        print(f"[error] {res.error}")


def main() -> None:
    agent = Agent()
    thread = uuid.uuid4().hex
    if len(sys.argv) > 1:
        show(agent.ask(" ".join(sys.argv[1:]), thread))
        return
    print("Asistente de telemetria y mantenimiento. Linea vacia para salir.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            break
        show(agent.ask(question, thread))


if __name__ == "__main__":
    main()
