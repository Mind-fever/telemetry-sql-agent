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


def test_text_comparison_ignores_accents_but_not_different_words():
    assert ev.text_mentions("Hay 34 sensores de vibración y 18 de presión.", "vibracion")
    assert ev.text_mentions("Hay 34 sensores de vibración y 18 de presión.", "presion")
    assert not ev.text_mentions("Hay 34 sensores de temperatura.", "vibracion")
    assert ev.same_value("Vibración", "vibracion")
    assert not ev.same_value("critica", "alerta")


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


def test_truncated_case_requires_the_system_flag_and_the_warning_in_the_answer():
    case = {"id": "e", "category": "edge", "expect_route": "sql", "expect_truncated": True,
            "answer_regex": "(?i)recort"}
    good = resp(answer="Se muestran 50; el resultado fue recortado.", rows=[{"id": 1}], rows_truncated=True)
    silent = resp(answer="Estas son las alarmas.", rows=[{"id": 1}], rows_truncated=True)
    not_cut = resp(answer="El resultado fue recortado.", rows=[{"id": 1}], rows_truncated=False)
    assert all(ev.evaluate_case(case, good, None).values())
    assert not ev.evaluate_case(case, silent, None)["respuesta_regex"]
    assert not ev.evaluate_case(case, not_cut, None)["resultado_recortado"]


def test_summary_case_requires_few_rows_and_no_truncation():
    case = {"id": "s", "category": "edge", "expect_route": "sql", "expect_max_rows": 31}
    by_day = resp(rows=[{"dia": d, "promedio": 3.1} for d in range(30)])
    raw = resp(rows=[{"valor": 3.1}] * 50, rows_truncated=True)
    empty = resp(rows=[])
    assert all(ev.evaluate_case(case, by_day, None).values())
    assert not ev.evaluate_case(case, raw, None)["resultado_resumido"]
    assert not ev.evaluate_case(case, empty, None)["resultado_resumido"]


def test_off_topic_case_fails_if_the_agent_answers_from_its_own_knowledge():
    case = {"id": "o", "category": "edge", "expect_route": "none",
            "answer_regex": "(?i)planta|mantenimiento", "answer_excludes": ["Cervantes"]}
    declines = resp(route="none", answer="Solo puedo ayudarte con la operación de la planta.")
    answers = resp(route="none", answer="Lo escribió Miguel de Cervantes. Además ayudo con la planta.")
    assert all(ev.evaluate_case(case, declines, None).values())
    assert not ev.evaluate_case(case, answers, None)["respuesta_no_incluye"]


def _quota_runner(errors):
    """run_case de mentira: devuelve en orden los errores dados (None = el caso corrio bien)."""
    calls = []

    def run_case(case):
        error = errors[len(calls)]
        calls.append(case["id"])
        return resp(error=error), None, 1.0, None

    return run_case, calls


DAY = "429 RESOURCE_EXHAUSTED [cuota: GenerateRequestsPerDayPerProjectPerModel-FreeTier, limite 20]"
MINUTE = "429 RESOURCE_EXHAUSTED [cuota: GenerateRequestsPerMinutePerProjectPerModel-FreeTier, limite 15]"


def test_daily_quota_stops_the_run_without_retrying():
    run_case, calls = _quota_runner([DAY])
    waits = []
    _, scope = ev.run_with_quota_retry(run_case, {"id": "c"}, sleep=waits.append)
    assert scope == "day" and len(calls) == 1 and waits == []


def test_per_minute_quota_waits_and_retries_once():
    run_case, calls = _quota_runner([MINUTE, None])
    waits = []
    (answer, *_), scope = ev.run_with_quota_retry(run_case, {"id": "c"}, sleep=waits.append)
    assert scope is None and len(calls) == 2 and waits == [ev.QUOTA_WAIT_SECONDS]
    assert answer.error is None


def test_per_minute_quota_twice_in_a_row_stops_the_run():
    run_case, calls = _quota_runner([MINUTE, MINUTE])
    _, scope = ev.run_with_quota_retry(run_case, {"id": "c"}, sleep=lambda s: None)
    assert scope == "minute" and len(calls) == 2


SERVICE = "503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand.'}}"


def test_service_outage_is_not_a_quota_error_but_also_stops_the_run():
    assert ev.stop_scope(SERVICE) == "service"
    assert ev.stop_scope("504 DEADLINE_EXCEEDED. Deadline expired") == "service"
    assert ev.stop_scope(DAY) == "day" and ev.stop_scope(MINUTE) == "minute"
    assert ev.stop_scope(None) is None and ev.stop_scope("syntax error at or near") is None


def test_service_outage_waits_and_retries_once_then_stops():
    run_case, calls = _quota_runner([SERVICE, None])
    waits = []
    _, scope = ev.run_with_quota_retry(run_case, {"id": "c"}, sleep=waits.append)
    assert scope is None and len(calls) == 2 and waits == [ev.QUOTA_WAIT_SECONDS]

    run_case, calls = _quota_runner([SERVICE, SERVICE])
    _, scope = ev.run_with_quota_retry(run_case, {"id": "c"}, sleep=lambda s: None)
    assert scope == "service" and len(calls) == 2


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


def test_report_names_the_model_and_flags_an_incomplete_run():
    results = [{"id": "a", "category": "sql", "passed": True, "checks": {"ruta": True}, "seconds": 3.0,
                "route": "sql", "sources": [], "grounded": True}]
    summary = ev.summarize(results, data_intact=True)
    full = ev.to_markdown(summary, results, {"model": "modelo-x", "planned": 1, "not_run": [], "stop_reason": None})
    cut = ev.to_markdown(summary, results, {"model": "modelo-x", "planned": 3, "not_run": ["b", "c"], "stop_reason": "x"})
    assert "modelo-x" in full and "Corrida incompleta" not in full
    assert "Casos ejecutados: 1 de 3" in cut
    assert "Corrida incompleta" in cut and "b, c" in cut
