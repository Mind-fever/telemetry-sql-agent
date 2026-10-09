"""Pruebas del enrutamiento del agente (principio III, FR-005). Usan un modelo falso guionado,
asi que no gastan cuota ni requieren API key."""

from __future__ import annotations

from telemetry_agent.embeddings import HashEmbedder
from telemetry_agent.graph import Agent
from telemetry_agent.llm import FakeLLM
from telemetry_agent.models import RouteDecision, SynthesisOutput


def make_agent(script, retrieve_fn=None, **kw):
    llm = FakeLLM(script)
    agent = Agent(
        llm=llm,
        embedder=HashEmbedder(),
        schema_text=lambda: "esquema de prueba",
        retrieve_fn=retrieve_fn or (lambda q, e, k: []),
        **kw,
    )
    return agent, llm


def route(r, reply=None, lang="es"):
    return RouteDecision(route=r, reason=f"prueba {r}", language=lang, direct_reply=reply)


def test_none_route_answers_directly_with_one_call():
    agent, llm = make_agent([route("none", "Hola, ¿en qué puedo ayudarte?")])
    res = agent.ask("hola")
    assert res.route == "none"
    assert res.answer == "Hola, ¿en qué puedo ayudarte?"
    assert res.sql is None and res.sources == [] and not res.refused
    assert len(llm.calls) == 1


def test_refuse_route_is_flagged_and_uses_one_call():
    agent, llm = make_agent([route("refuse", "Solo puedo consultar información.")])
    res = agent.ask("borrá todas las alarmas")
    assert res.route == "refuse"
    assert res.refused is True
    assert res.sql is None
    assert len(llm.calls) == 1


def test_missing_direct_reply_falls_back_to_a_default_message():
    agent, _ = make_agent([route("refuse", None, lang="en")])
    res = agent.ask("delete everything")
    assert res.refused and "can only look up" in res.answer


def test_follow_up_receives_previous_turn_as_context():
    agent, llm = make_agent([route("none", "uno"), route("none", "dos")])
    agent.ask("primera pregunta sobre la bomba P-101", thread_id="t1")
    agent.ask("¿y el mes anterior?", thread_id="t1")
    second_router_prompt = llm.calls[1]["user"]
    assert "primera pregunta sobre la bomba P-101" in second_router_prompt


def test_threads_do_not_share_history():
    agent, llm = make_agent([route("none", "uno"), route("none", "dos")])
    agent.ask("pregunta secreta de otro hilo", thread_id="a")
    agent.ask("hola", thread_id="b")
    assert "pregunta secreta de otro hilo" not in llm.calls[1]["user"]


def test_quota_error_is_reported_clearly_without_crashing():
    agent, _ = make_agent([RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")])
    res = agent.ask("¿cuántas alarmas hubo?")
    assert res.grounded is False
    assert "límite de uso" in res.answer
    assert res.error and "429" in res.error


def test_docs_route_does_not_touch_the_database():
    chunks = [{"archivo": "manual_mantenimiento_preventivo.pdf", "pagina": 4, "orden": 1,
               "texto": "Cada 2.500 horas", "distancia": 0.1}]
    agent, llm = make_agent(
        [route("docs"), SynthesisOutput(answer="Cada 2.500 horas.", grounded=True, used_fragments=[1])],
        retrieve_fn=lambda q, e, k: chunks,
    )
    res = agent.ask("¿cada cuánto se lubrican los rodamientos de un motor?")
    assert res.route == "docs"
    assert res.sql is None and res.rows is None
    assert len(llm.calls) == 2
