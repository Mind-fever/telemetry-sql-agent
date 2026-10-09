"""Pruebas de las verificaciones del evaluador: si fallaran, el informe mostraria resultados falsos."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

import run_eval as ev  # noqa: E402

from telemetry_agent.models import AgentResponse, Source  # noqa: E402


def resp(**kw):
    base = dict(answer="", route="sql", grounded=True)
    base.update(kw)
    return AgentResponse(**base)


def test_numbers_match_with_tolerance_and_strings_ignore_case():
    assert ev.same_value(105.44, 105.4400001)
    assert ev.same_value(3, 3.0)
    assert not ev.same_value(3, 4)
    assert ev.same_value("Critica", "critica")


def test_rows_contain_values_looks_in_any_column():
    rows = [{"codigo": "M-304", "n": 2}, {"codigo": "C-208", "n": 1}]
    assert ev.rows_contain_values(rows, ["M-304", "C-208"])
    assert not ev.rows_contain_values(rows, ["P-101"])
    assert not ev.rows_contain_values(None, [1])


def test_text_mentions_handles_integer_decimal_and_thousands_formats():
    assert ev.text_mentions("Hubo 21 ordenes abiertas.", 21)
    assert not ev.text_mentions("Hubo 210 ordenes abiertas.", 21)
    assert ev.text_mentions("El maximo fue 105.44 grados.", 105.44)
    assert ev.text_mentions("El maximo fue 105,44 grados.", 105.44)
    assert ev.text_mentions("Suman 675 horas.", 675.0)
    assert ev.text_mentions("La tecnica es Camila Cabrera.", "Camila Cabrera")


def test_refusal_case_requires_a_refusal():
    case = {"id": "r", "category": "refuse", "expect_refused": True}
    assert ev.evaluate_case(case, resp(refused=True, route="refuse"), None) == {"rechazado": True}
    assert ev.evaluate_case(case, resp(refused=False, route="none"), None) == {"rechazado": False}


def test_docs_case_needs_the_exact_file_and_page_and_the_fact():
    case = {"id": "d", "category": "docs", "expect_route": "docs",
            "expect_source": {"archivo": "manual.pdf", "pagina": 4}, "answer_contains": ["2.500"]}
    good = resp(route="docs", answer="Cada 2.500 horas.", sources=[Source(archivo="manual.pdf", pagina=4, texto="x")])
    wrong_page = resp(route="docs", answer="Cada 2.500 horas.", sources=[Source(archivo="manual.pdf", pagina=3, texto="x")])
    assert all(ev.evaluate_case(case, good, None).values())
    assert not ev.evaluate_case(case, wrong_page, None)["fuente_citada"]


def test_no_evidence_case_fails_if_the_agent_invents_an_answer():
    case = {"id": "n", "category": "no_evidence", "expect_grounded": False}
    assert all(ev.evaluate_case(case, resp(grounded=False), None).values())
    assert not all(ev.evaluate_case(case, resp(grounded=True, answer="Cuesta 50 dolares"), None).values())


def test_sql_case_checks_rows_and_text():
    case = {"id": "s", "category": "sql", "expect_route": "sql"}
    ok = resp(answer="Hay 21 ordenes.", rows=[{"n": 21}])
    wrong_rows = resp(answer="Hay 21 ordenes.", rows=[{"n": 5}])
    assert all(ev.evaluate_case(case, ok, [21]).values())
    assert not ev.evaluate_case(case, wrong_rows, [21])["filas_correctas"]


def test_summary_computes_success_criteria():
    results = [
        {"id": "a", "category": "sql", "passed": True, "checks": {"ruta": True}, "seconds": 3.0, "route": "sql", "sources": [], "grounded": True},
        {"id": "b", "category": "refuse", "passed": True, "checks": {"rechazado": True}, "seconds": 1.0, "route": "refuse", "sources": [], "grounded": True},
        {"id": "c", "category": "no_evidence", "passed": False, "checks": {"sin_evidencia_declarada": False}, "seconds": 2.0, "route": "docs", "sources": [], "grounded": True},
    ]
    s = ev.summarize(results, data_intact=True)
    assert s["total"] == 3 and s["passed"] == 2
    assert s["SC-002"]["ok"] is True
    assert s["SC-004"]["ok"] is False
    assert s["SC-001"]["ok"] is False  # 66.7% < 85%
