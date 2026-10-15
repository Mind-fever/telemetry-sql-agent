"""Prueba de humo de la interfaz (US4) con un agente de mentira: no usa modelo ni base."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from telemetry_agent.models import AgentResponse, Source

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


class StubAgent:
    def __init__(self):
        self.questions = []

    def ask(self, question, thread_id):
        self.questions.append((question, thread_id))
        return AgentResponse(
            answer="Hubo 3 alarmas criticas.",
            route="both",
            route_reason="Necesita un dato y un procedimiento.",
            sql="select count(*) as n from alarmas",
            rows=[{"n": 3}],
            sources=[Source(archivo="procedimiento_respuesta_alarmas.pdf", pagina=3, texto="Reducir la carga.")],
        )


def run_with_stub():
    at = AppTest.from_file(APP, default_timeout=30)
    stub = StubAgent()
    at.session_state["_agent_override"] = stub
    at.run()
    return at, stub


def test_empty_app_shows_title_examples_and_input():
    at, _ = run_with_stub()
    assert not at.exception
    assert "Asistente de telemetría" in at.title[0].value
    assert len(at.sidebar.button) >= 5
    assert len(at.chat_input) == 1


def test_question_shows_answer_source_sql_rows_and_documents():
    at, stub = run_with_stub()
    at.chat_input[0].set_value("¿cuántas alarmas críticas?").run()
    assert not at.exception
    assert stub.questions and stub.questions[0][0] == "¿cuántas alarmas críticas?"
    texts = [m.value for m in at.markdown]
    assert any("Hubo 3 alarmas criticas." in t for t in texts)
    captions = " ".join(c.value for c in at.caption)
    assert "Base de datos y documentos" in captions
    labels = [e.label for e in at.expander]
    assert any("Consulta SQL" in l for l in labels)
    assert any("Filas devueltas" in l for l in labels)
    assert any("Documentos citados" in l for l in labels)


def test_example_button_asks_the_question():
    at, stub = run_with_stub()
    at.sidebar.button[0].click().run()
    assert stub.questions and "P-101" in stub.questions[0][0]


def test_missing_setting_names_the_variable_without_showing_values(monkeypatch):
    """Caso borde de la 002: en la nube falta una clave. La app dice cuál y no muestra conexiones."""
    import streamlit as st

    import telemetry_agent.graph as graph

    def failing_agent():
        raise RuntimeError("Falta DATABASE_URL_RO en el entorno (ver .env.example).")

    monkeypatch.setattr(graph, "Agent", failing_agent)
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    errors = " ".join(e.value for e in at.error)
    assert "No se pudo iniciar el agente" in errors
    assert "DATABASE_URL_RO" in errors
    assert "postgresql://" not in errors
    assert len(at.chat_input) == 0


def test_conversation_keeps_the_same_thread_and_new_conversation_resets_it():
    at, stub = run_with_stub()
    at.chat_input[0].set_value("primera").run()
    at.chat_input[0].set_value("segunda").run()
    assert stub.questions[0][1] == stub.questions[1][1]
    first_thread = stub.questions[0][1]
    next(b for b in at.sidebar.button if b.label == "Nueva conversación").click().run()
    at.chat_input[0].set_value("tercera").run()
    assert stub.questions[2][1] != first_thread
