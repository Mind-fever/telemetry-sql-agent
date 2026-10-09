"""Pruebas del camino de documentos (FR-008, FR-009, FR-010, SC-003, SC-004)."""

from __future__ import annotations

import math
from pathlib import Path

import ingest_docs
import pytest

from telemetry_agent.embeddings import HashEmbedder
from telemetry_agent.graph import Agent
from telemetry_agent.llm import FakeLLM
from telemetry_agent.models import RouteDecision, SynthesisOutput

DOCS = Path(__file__).resolve().parents[1] / "data" / "docs"


def _cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x * x for x in a)) or 1) * (math.sqrt(sum(y * y for y in b)) or 1))


@pytest.fixture(scope="module")
def local_retriever():
    """Recuperador en memoria: los fragmentos reales de los PDF ordenados con el embedding falso.
    Prueba el recorte, el ordenamiento y la cita sin tocar la base."""
    emb = HashEmbedder()
    chunks = [c for pdf in sorted(DOCS.glob("*.pdf")) for c in ingest_docs.chunks_from_pdf(pdf)]
    vectors = emb.embed_documents([(c["archivo"], c["texto"]) for c in chunks])

    def retrieve(query, embedder, k):
        q = embedder.embed_query(query)
        ranked = sorted(zip(chunks, vectors), key=lambda cv: -_cosine(q, cv[1]))[:k]
        return [{**c, "distancia": 1 - _cosine(q, v)} for c, v in ranked]

    return retrieve


def make_agent(script, retrieve_fn):
    llm = FakeLLM(script)
    return Agent(llm=llm, embedder=HashEmbedder(), schema_text=lambda: "x", retrieve_fn=retrieve_fn), llm


def decision(route):
    return RouteDecision(route=route, reason="prueba", language="es")


def test_answer_cites_file_and_page_of_the_fragment_used(local_retriever):
    agent, llm = make_agent(
        [decision("docs"), SynthesisOutput(answer="Cada 2.500 horas.", grounded=True, used_fragments=[1])],
        local_retriever,
    )
    res = agent.ask("motores electricos lubricacion de rodamientos de grasa de base litio horas de funcionamiento")
    assert res.grounded
    assert len(res.sources) == 1
    assert res.sources[0].archivo == "manual_mantenimiento_preventivo.pdf"
    assert res.sources[0].pagina == 4
    # el fragmento 1 se le paso al modelo con su archivo y pagina
    assert "manual_mantenimiento_preventivo.pdf, pagina 4" in llm.calls[1]["user"]


def test_docs_answer_without_declared_fragments_still_cites_one(local_retriever):
    agent, _ = make_agent(
        [decision("docs"), SynthesisOutput(answer="Respuesta.", grounded=True, used_fragments=[])],
        local_retriever,
    )
    res = agent.ask("plazo de atencion de una orden de prioridad alta")
    assert res.grounded and len(res.sources) == 1  # SC-003


def test_ungrounded_answer_has_no_sources_and_says_so(local_retriever):
    agent, _ = make_agent(
        [decision("docs"), SynthesisOutput(answer="No encontré esa información.", grounded=False, used_fragments=[])],
        local_retriever,
    )
    res = agent.ask("¿cuanto cuesta un rodamiento?")
    assert res.grounded is False
    assert res.sources == []


def test_no_fragments_available_answers_without_calling_the_model_again():
    agent, llm = make_agent([decision("docs")], lambda q, e, k: [])
    res = agent.ask("¿cada cuánto se lubrica?")
    assert res.grounded is False
    assert "No encontré" in res.answer
    assert len(llm.calls) == 1  # solo el router


def test_fragment_numbers_outside_the_list_are_ignored(local_retriever):
    agent, _ = make_agent(
        [decision("docs"), SynthesisOutput(answer="x", grounded=True, used_fragments=[99])],
        local_retriever,
    )
    res = agent.ask("bloqueo y etiquetado antes de intervenir")
    assert len(res.sources) == 1  # cae al primer fragmento recuperado, nunca a uno inexistente
