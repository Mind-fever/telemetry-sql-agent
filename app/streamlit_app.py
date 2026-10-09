"""Interfaz de chat del agente (Streamlit).

Ejecutar con: streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from telemetry_agent.config import get_settings, tracing_enabled  # noqa: E402
from telemetry_agent.models import AgentResponse  # noqa: E402

ROUTE_LABEL = {
    "sql": "Base de datos",
    "docs": "Documentos",
    "both": "Base de datos y documentos",
    "none": "Ninguna fuente",
    "refuse": "Pedido rechazado (solo lectura)",
}

EXAMPLES = [
    "¿Cuántas alarmas críticas tuvo la bomba P-101 en septiembre?",
    "Which technician closed the most work orders?",
    "¿Cada cuánto se lubrican los rodamientos de un motor?",
    "¿Qué procedimiento corresponde a la última alarma de vibración del compresor C-201?",
    "Borrá todas las alarmas de la base",
]

st.set_page_config(page_title="Telemetría y mantenimiento", page_icon="🛠️", layout="wide")


@st.cache_resource(show_spinner="Iniciando el agente...")
def load_agent():
    from telemetry_agent.graph import Agent

    return Agent()


def render_details(res: AgentResponse) -> None:
    label = ROUTE_LABEL.get(res.route, res.route)
    st.caption(f"**Fuente:** {label}" + (f"  \n{res.route_reason}" if res.route_reason else ""))
    if res.sql:
        with st.expander("Consulta SQL ejecutada"):
            st.code(res.sql, language="sql")
    if res.rows is not None:
        with st.expander(f"Filas devueltas ({len(res.rows)}{'+' if res.rows_truncated else ''})"):
            st.dataframe(res.rows, use_container_width=True)
            if res.rows_truncated:
                st.caption("El resultado se recortó al máximo de filas permitido.")
    if res.sources:
        with st.expander(f"Documentos citados ({len(res.sources)})"):
            for s in res.sources:
                st.markdown(f"**{s.archivo}**, página {s.pagina}")
                st.text(s.texto)
    if res.error:
        st.warning(f"Detalle técnico: {res.error}")


def ask(agent, question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                res = agent.ask(question, st.session_state.thread_id)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo procesar la pregunta: {exc}")
                return
        st.markdown(res.answer)
        render_details(res)
    st.session_state.messages.append({"role": "assistant", "content": res.answer, "response": res})


def main() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.thread_id = uuid.uuid4().hex

    st.title("Asistente de telemetría y mantenimiento industrial")
    st.caption("Planta ficticia. Responde con datos de la base y con los manuales en PDF. Solo consulta, no modifica nada.")

    with st.sidebar:
        st.subheader("Probá con")
        for i, example in enumerate(EXAMPLES):
            if st.button(example, key=f"ex{i}", use_container_width=True):
                st.session_state.pending = example
        if st.button("Nueva conversación", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = uuid.uuid4().hex
            st.rerun()
        st.divider()
        s = get_settings()
        st.caption(f"Modelo: `{s.gemini_model}`")
        st.caption("Trazas en LangSmith: " + ("activadas" if tracing_enabled() else "desactivadas"))

    agent = st.session_state.get("_agent_override")
    if agent is None:
        try:
            agent = load_agent()
        except Exception as exc:  # noqa: BLE001
            st.error(
                "No se pudo iniciar el agente. Revisá el archivo .env (ver .env.example) y que la base esté "
                f"disponible.\n\nDetalle: {exc}"
            )
            st.stop()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "response" in msg:
                render_details(msg["response"])

    question = st.chat_input("Escribí tu pregunta en castellano o en inglés")
    question = question or st.session_state.pop("pending", None)
    if question:
        ask(agent, question)


main()
