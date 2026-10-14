"""Pruebas del camino SQL contra la base real (FR-006, FR-007, SC-002).
Se saltean si no hay una base cargada. No escriben nada en la base."""

from __future__ import annotations

import pytest

from telemetry_agent.embeddings import HashEmbedder
from telemetry_agent.graph import Agent
from telemetry_agent.llm import FakeLLM
from telemetry_agent.models import RouteDecision, SynthesisOutput


@pytest.fixture(autouse=True)
def _need_db(db_available):
    if not db_available:
        pytest.skip("No hay base cargada.")


def count_alarms():
    from telemetry_agent.db import connect_admin

    with connect_admin() as conn:
        return conn.execute("select count(*) from alarmas").fetchone()[0]


def make_agent(script, retrieve_fn=None):
    llm = FakeLLM(script)
    return Agent(
        llm=llm, embedder=HashEmbedder(), retrieve_fn=retrieve_fn or (lambda q, e, k: [])
    ), llm


def sql_route():
    return RouteDecision(route="sql", reason="datos", language="es")


def synth(text="ok"):
    return SynthesisOutput(answer=text, grounded=True, used_fragments=[])


def test_sql_path_returns_the_real_number():
    agent, llm = make_agent([
        sql_route(),
        "```sql\nselect count(*) as n from alarmas where severidad = 'critica'\n```",
        synth("Hubo alarmas criticas."),
    ])
    res = agent.ask("¿cuántas alarmas críticas hubo?")
    from telemetry_agent.db import connect_admin

    with connect_admin() as conn:
        expected = conn.execute("select count(*) from alarmas where severidad = 'critica'").fetchone()[0]
    assert res.route == "sql"
    assert res.rows == [{"n": expected}]
    assert "critica" in res.sql
    assert len(llm.calls) == 3


def test_synthesis_receives_the_executed_query_so_it_knows_the_filters():
    agent, llm = make_agent([
        sql_route(),
        "select codigo from equipos where estado = 'fuera de servicio'",
        synth(),
    ])
    agent.ask("¿qué equipos están fuera de servicio?")
    evidence = llm.calls[2]["user"]
    assert "estado = 'fuera de servicio'" in evidence
    assert '"filas"' in evidence


def test_synthesis_receives_the_period_covered_by_the_data():
    agent, llm = make_agent([sql_route(), "select count(*) as n from ordenes_mantenimiento", synth()])
    agent.ask("¿cuántas órdenes se cerraron el mes pasado?")
    evidence = llm.calls[2]["user"]
    assert '"periodo_con_datos": "2026-09-01 a 2026-09-30"' in evidence


def test_the_schema_given_to_the_model_comes_from_the_database():
    agent, llm = make_agent([sql_route(), "select 1 as x from areas limit 1", synth()])
    agent.ask("probar")
    system_prompt = llm.calls[1]["system"]
    assert "Tabla alarmas" in system_prompt
    assert "'critica'" in system_prompt  # valores reales de la columna categorica
    assert "P-101" in system_prompt


def test_database_error_is_fed_back_and_the_model_corrects_the_query():
    agent, llm = make_agent([
        sql_route(),
        "select columna_inexistente from alarmas",
        "select count(*) as n from alarmas",
        synth(),
    ])
    res = agent.ask("¿cuántas alarmas hay?")
    assert res.rows and res.rows[0]["n"] > 0
    retry_prompt = llm.calls[2]["user"]
    assert "columna_inexistente" in retry_prompt  # el modelo ve por que fallo
    assert len(llm.calls) == 4


def test_write_attempt_is_refused_and_the_database_is_untouched():
    before = count_alarms()
    agent, llm = make_agent([sql_route(), "DELETE FROM alarmas"])
    res = agent.ask("borrá las alarmas de ayer")
    assert res.refused is True
    assert res.sql is None
    assert count_alarms() == before
    assert len(llm.calls) == 2  # no se reintenta un pedido de escritura ni se llama a la sintesis


def test_write_attempt_hidden_behind_a_select_is_refused():
    before = count_alarms()
    # El modelo insiste tres veces con una segunda sentencia escondida: el validador la rechaza cada vez.
    agent, llm = make_agent([sql_route()] + ["select 1; delete from alarmas"] * 3)
    res = agent.ask("trucos")
    assert count_alarms() == before
    assert res.rows is None
    assert res.grounded is False
    assert res.error is None  # termino por el limite de reintentos, no por una falla tecnica
    assert len(llm.calls) == 4


def test_gives_up_after_the_retry_limit_without_inventing_an_answer():
    agent, llm = make_agent([sql_route()] + ["select * from tabla_que_no_existe"] * 3)
    res = agent.ask("¿cuántas alarmas?")
    assert res.grounded is False
    assert res.rows is None
    assert len(llm.calls) == 4  # router + 3 intentos (1 + 2 reintentos); sin llamada de sintesis


def test_row_limit_is_applied_and_reported():
    agent, _ = make_agent([sql_route(), "select id from lecturas order by id", synth()])
    res = agent.ask("listá todas las lecturas")
    assert res.rows_truncated is True
    assert len(res.rows) == 50


def test_both_route_uses_sql_result_to_build_the_retrieval_query():
    seen = {}

    def fake_retrieve(query, embedder, k):
        seen["query"] = query
        return [{"archivo": "procedimiento_respuesta_alarmas.pdf", "pagina": 3, "orden": 1,
                 "texto": "Alarma critica de vibracion", "distancia": 0.1}]

    agent, llm = make_agent([
        RouteDecision(route="both", reason="dato + procedimiento", language="es"),
        "select a.severidad, s.magnitud from alarmas a join sensores s on s.id = a.sensor_id "
        "join equipos e on e.id = s.equipo_id where e.codigo = 'C-201' and s.magnitud = 'vibracion' "
        "order by a.fecha_inicio desc limit 1",
        SynthesisOutput(answer="Aplica el procedimiento de alarma critica.", grounded=True, used_fragments=[1]),
    ], retrieve_fn=fake_retrieve)
    res = agent.ask("¿qué procedimiento corresponde a la última alarma de vibración del compresor C-201?")
    assert res.route == "both"
    assert res.rows == [{"severidad": "critica", "magnitud": "vibracion"}]
    assert "critica" in seen["query"]  # el dato de la base orienta la busqueda en los documentos
    assert res.sources and res.sources[0].pagina == 3
