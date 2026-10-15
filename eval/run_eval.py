"""Evaluacion del agente con verificaciones deterministas (sin un modelo que haga de juez).

Para cada caso de eval/golden.jsonl:
- Ruta: la fuente que eligio el agente coincide con la esperada.
- Resultado SQL: las filas que devolvio el agente contienen los valores de una consulta de
  referencia que se ejecuta en el momento (asi los esperados nunca quedan desactualizados) y la
  respuesta en texto menciona esos valores.
- Documentos: la fuente citada es el archivo y la pagina esperados, y la respuesta contiene el dato.
- Rechazo: el pedido se rechaza y, al final, ninguna tabla cambio de cantidad de filas.
- Sin evidencia: el agente declara que no tiene la informacion y no cita fuentes.
- Casos borde: equipo que no existe, pregunta ambigua (pide precisar) y resultado recortado (lo avisa).

Uso:
    python eval/run_eval.py --check-refs        muestra los valores de referencia (sin modelo, sin cuota)
    python eval/run_eval.py                     corre todos los casos
    python eval/run_eval.py --only sql-01,doc-01 --delay 6
    python eval/run_eval.py --category docs

Con LANGSMITH_TRACING=true y LANGSMITH_API_KEY cada ejecucion queda trazada, etiquetada con el
id del caso, y se le adjunta el resultado (caso_aprobado) como feedback.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from telemetry_agent.config import ALLOWED_TABLES, get_settings, tracing_enabled  # noqa: E402
from telemetry_agent.db import connect_admin  # noqa: E402
from telemetry_agent.graph import quota_scope  # noqa: E402

GOLDEN = Path(__file__).with_name("golden.jsonl")
RESULTS = Path(__file__).with_name("results")
QUOTA_WAIT_SECONDS = 65  # el limite por minuto de la capa gratuita se libera en ese plazo

# Umbrales de exito de la especificacion (spec.md, seccion Success Criteria).
SC001_MIN_PASS = 0.85
SC005_MIN_ROUTE = 0.90
SC006_MAX_SECONDS = 20


# ---------------------------------------------------------------- referencias
def _plain(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value.__class__.__name__ == "Decimal":
        return float(value)
    return value


def run_reference(conn, sql: str) -> list[tuple]:
    return [tuple(_plain(v) for v in row) for row in conn.execute(sql).fetchall()]


def flatten(rows: list[tuple]) -> list[Any]:
    return [v for row in rows for v in row]


def fold(text: Any) -> str:
    """Minusculas y sin tildes: la base guarda 'vibracion' y el agente puede escribir 'vibración'."""
    decomposed = unicodedata.normalize("NFD", str(text))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").strip().lower()


def same_value(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.011
    return fold(a) == fold(b)


def rows_contain_values(agent_rows: list[dict] | None, ref_values: list[Any]) -> bool:
    if agent_rows is None:
        return False
    available = [v for row in agent_rows for v in row.values()]
    return all(any(same_value(av, rv) for av in available) for rv in ref_values)


def text_mentions(answer: str, value: Any) -> bool:
    low = answer.lower()
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        num = float(value)
        forms = {f"{num:.2f}", f"{num:.1f}", f"{num:.0f}", str(value)}
        forms |= {f.replace(".", ",") for f in forms}
        if num == int(num):
            forms |= {f"{int(num):,}".replace(",", "."), f"{int(num):,}"}
        return any(re.search(rf"(?<![\d.,]){re.escape(f)}(?![\d])", low) for f in forms)
    return fold(value) in fold(answer)


def answer_has_values(answer: str, ref_values: list[Any]) -> bool:
    if len(ref_values) > 8:  # listas largas: se verifica el resultado en las filas, no el texto
        return True
    return all(text_mentions(answer, v) for v in ref_values)


# ------------------------------------------------------------------- casos
def load_cases() -> list[dict]:
    return [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]


def table_counts(conn) -> dict[str, int]:
    return {t: conn.execute(f"select count(*) from {t}").fetchone()[0] for t in ALLOWED_TABLES}


def evaluate_case(case: dict, resp, ref_values: list[Any] | None) -> dict[str, bool]:
    """Devuelve un diccionario de verificaciones aplicables; el caso aprueba si todas son True."""
    checks: dict[str, bool] = {}
    answer = resp.answer or ""

    if case.get("expect_refused"):
        checks["rechazado"] = bool(resp.refused or resp.route == "refuse")
        return checks

    if "expect_route" in case:
        checks["ruta"] = resp.route == case["expect_route"]
    if "expect_grounded" in case:
        checks["sin_evidencia_declarada"] = resp.grounded is False and not resp.sources
    if ref_values is not None:
        checks["filas_correctas"] = rows_contain_values(resp.rows, ref_values)
        if case.get("category") not in ("both",):
            checks["respuesta_menciona_valor"] = answer_has_values(answer, ref_values)
    if "expect_max_rows" in case:  # un resumen (por ejemplo por dia) entra completo, sin recorte
        rows = resp.rows or []
        checks["resultado_resumido"] = 0 < len(rows) <= case["expect_max_rows"] and not resp.rows_truncated
    if case.get("expect_truncated"):
        checks["resultado_recortado"] = bool(resp.rows_truncated) and resp.rows is not None
    if "expect_source" in case:
        want = case["expect_source"]
        checks["fuente_citada"] = any(
            s.archivo == want["archivo"] and s.pagina == want["pagina"] for s in resp.sources
        )
    if "answer_contains" in case:
        checks["respuesta_contiene"] = all(t.lower() in answer.lower() for t in case["answer_contains"])
    if "answer_regex" in case:
        checks["respuesta_regex"] = re.search(case["answer_regex"], answer) is not None
    if "answer_excludes" in case:  # lo que la respuesta no debe decir (por ejemplo, un dato de conocimiento propio)
        checks["respuesta_no_incluye"] = not any(fold(t) in fold(answer) for t in case["answer_excludes"])
    if case.get("category") == "none":
        checks["sin_sql_ni_fuentes"] = resp.sql is None and not resp.sources
    return checks


def stop_scope(error: str | None) -> str | None:
    """Motivo por el que un caso no se pudo correr por causas ajenas al agente.

    "day" o "minute" si se alcanzo un limite de cuota, "service" si el servicio del modelo no
    estaba disponible (errores 503 y 504, o la conexion se corto), None si el caso corrio.
    """
    scope = quota_scope(error)
    if scope:
        return scope
    if error and any(k in error for k in ("503", "UNAVAILABLE", "504", "DEADLINE_EXCEEDED", "10054",
                                           "ConnectionReset", "Connection aborted", "RemoteProtocolError",
                                           "getaddrinfo", "11001", "ConnectError")):
        return "service"
    return None


def run_with_quota_retry(run_case, case: dict, sleep=time.sleep):
    """Corre un caso cuidando la cuota y la disponibilidad del modelo.

    run_case(case) devuelve (respuesta, error, segundos, run_id). Ante el limite por minuto o una
    caida del servicio se espera y se reintenta una sola vez. Devuelve ese resultado y el motivo
    que quedo sin resolver ("day", "minute", "service" o None). Si no es None hay que cortar la
    corrida: esos errores no dicen nada sobre el agente y no se cuentan como casos fallados.
    """
    def scope_of(outcome) -> str | None:
        resp, error = outcome[0], outcome[1]
        return stop_scope(error or getattr(resp, "error", None))

    outcome = run_case(case)
    scope = scope_of(outcome)
    if scope in ("minute", "service"):
        print(f"  {scope} en {case['id']}: espero {QUOTA_WAIT_SECONDS} s y reintento el caso")
        sleep(QUOTA_WAIT_SECONDS)
        outcome = run_case(case)
        scope = scope_of(outcome)
    return outcome, scope


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-refs", action="store_true", help="solo mostrar los valores de referencia")
    ap.add_argument("--only", help="ids separados por coma")
    ap.add_argument("--category", help="una categoria: sql, docs, both, refuse, no_evidence, none, follow_up")
    ap.add_argument("--delay", type=float, default=4.0, help="segundos entre casos (cuidar la cuota gratuita)")
    args = ap.parse_args()

    cases = load_cases()
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]

    with connect_admin() as conn:
        refs: dict[str, list[tuple]] = {}
        for c in cases:
            if "reference_sql" in c:
                refs[c["id"]] = run_reference(conn, c["reference_sql"])
        before = table_counts(conn)

        if args.check_refs:
            problems = 0
            for c in cases:
                if c["id"] in refs:
                    print(f"{c['id']:10s} {refs[c['id']][:6]}")
                    if not refs[c["id"]]:
                        print(f"  AVISO: la referencia de {c['id']} no devuelve filas")
                        problems += 1
                if "unique_top" in c:
                    top = [r[0] for r in run_reference(conn, c["unique_top"])]
                    tie = len(top) > 1 and top[0] == top[1]
                    print(f"  empate en {c['id']}: {'SI (ambiguo)' if tie else 'no'}  {top}")
                    problems += int(tie)
            print(f"\n{len(cases)} casos, {problems} problemas en las referencias.")
            return

    from langchain_core.tracers.context import collect_runs

    from telemetry_agent.graph import Agent

    agent = Agent()
    client = None
    if tracing_enabled():
        from langsmith import Client

        client = Client()

    def run_case(case: dict):
        thread = uuid.uuid4().hex
        started = time.perf_counter()
        error = None
        resp = None
        run_id = None
        try:
            with collect_runs() as cb:
                for turn in case.get("turns") or [case["question"]]:
                    resp = agent.ask(turn, thread, metadata={"case_id": case["id"]}, tags=["eval", case["category"]])
                if cb.traced_runs:
                    run_id = cb.traced_runs[-1].id
        except Exception as exc:  # noqa: BLE001
            error = str(exc).splitlines()[0][:300]
        return resp, error, time.perf_counter() - started, run_id

    results: list[dict] = []
    stop_reason = None
    for i, case in enumerate(cases):
        turns = case.get("turns") or [case["question"]]
        (resp, error, elapsed, run_id), scope = run_with_quota_retry(run_case, case)
        if scope:
            stop_reason = (error or resp.error or "")[-120:]
            print(f"  corte ({scope}) en {case['id']}: {stop_reason}")
            break

        ref_values = flatten(refs[case["id"]]) if case["id"] in refs else None
        checks = evaluate_case(case, resp, ref_values) if resp is not None else {"sin_error_tecnico": False}
        if resp is not None and resp.error:
            checks["sin_error_tecnico"] = False
        passed = bool(checks) and all(checks.values())
        results.append({
            "id": case["id"], "category": case["category"], "question": turns[-1], "passed": passed,
            "checks": checks, "seconds": round(elapsed, 1), "route": getattr(resp, "route", None),
            "answer": getattr(resp, "answer", None), "sql": getattr(resp, "sql", None),
            "sources": [(s.archivo, s.pagina) for s in getattr(resp, "sources", [])],
            "grounded": getattr(resp, "grounded", None), "error": error or getattr(resp, "error", None),
        })
        print(f"[{i + 1}/{len(cases)}] {'OK  ' if passed else 'FALLA'} {case['id']:10s} {elapsed:5.1f}s "
              f"ruta={getattr(resp, 'route', '-')} " + ("" if passed else f"-> {checks} {error or ''}"))

        if client is not None and run_id is not None:
            try:
                client.create_feedback(run_id, key="caso_aprobado", score=1.0 if passed else 0.0,
                                       comment=json.dumps(checks, ensure_ascii=False))
            except Exception as exc:  # noqa: BLE001
                print(f"  (no se pudo adjuntar el feedback a LangSmith: {str(exc)[:120]})")
        if i < len(cases) - 1:
            time.sleep(args.delay)

    with connect_admin() as conn:
        after = table_counts(conn)
    intact = before == after

    summary = summarize(results, intact)
    done = {r["id"] for r in results}
    run_info = {
        "model": get_settings().gemini_model,
        "planned": len(cases),
        "not_run": [c["id"] for c in cases if c["id"] not in done],
        "stop_reason": stop_reason,
    }
    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (RESULTS / f"{stamp}.json").write_text(
        json.dumps({"run": run_info, "summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md = to_markdown(summary, results, run_info)
    (RESULTS / "latest.md").write_text(md, encoding="utf-8")
    print("\n" + md)


def pct(n: int, d: int) -> float:
    return round(100 * n / d, 1) if d else 0.0


def summarize(results: list[dict], data_intact: bool) -> dict:
    total = len(results)
    passed = sum(r["passed"] for r in results)
    by_cat: dict[str, tuple[int, int]] = {}
    for r in results:
        p, t = by_cat.get(r["category"], (0, 0))
        by_cat[r["category"]] = (p + r["passed"], t + 1)

    route_cases = [r for r in results if "ruta" in r["checks"]]
    route_ok = sum(r["checks"]["ruta"] for r in route_cases)
    refuse = [r for r in results if r["category"] == "refuse"]
    refuse_ok = sum(r["passed"] for r in refuse)
    docs_grounded = [r for r in results if r["category"] in ("docs", "both") and r["grounded"]]
    docs_cited = sum(bool(r["sources"]) for r in docs_grounded)
    noev = [r for r in results if r["category"] == "no_evidence"]
    noev_ok = sum(r["passed"] for r in noev)
    times = sorted(r["seconds"] for r in results)
    p90 = times[int(0.9 * (len(times) - 1))] if times else 0.0

    return {
        "total": total, "passed": passed, "pass_rate": pct(passed, total),
        "by_category": {k: {"passed": p, "total": t} for k, (p, t) in by_cat.items()},
        "SC-001": {"value": pct(passed, total), "target": SC001_MIN_PASS * 100, "ok": passed / total >= SC001_MIN_PASS if total else False},
        "SC-002": {"refused": f"{refuse_ok}/{len(refuse)}", "data_intact": data_intact, "ok": bool(refuse) and refuse_ok == len(refuse) and data_intact},
        "SC-003": {"cited": f"{docs_cited}/{len(docs_grounded)}", "ok": bool(docs_grounded) and docs_cited == len(docs_grounded)},
        "SC-004": {"declared_no_info": f"{noev_ok}/{len(noev)}", "ok": bool(noev) and noev_ok == len(noev)},
        "SC-005": {"value": pct(route_ok, len(route_cases)), "target": SC005_MIN_ROUTE * 100, "ok": (route_ok / len(route_cases) >= SC005_MIN_ROUTE) if route_cases else False},
        "SC-006": {"p90_seconds": p90, "target": SC006_MAX_SECONDS, "ok": p90 < SC006_MAX_SECONDS, "median_seconds": round(statistics.median(times), 1) if times else 0.0},
    }


def to_markdown(summary: dict, results: list[dict], run_info: dict | None = None) -> str:
    def mark(ok: bool) -> str:
        return "cumple" if ok else "NO cumple"

    run_lines: list[str] = []
    if run_info:
        run_lines = [f"Modelo: `{run_info['model']}`. Casos ejecutados: {summary['total']} de {run_info['planned']}.", ""]
        if run_info["not_run"]:
            run_lines += [
                "**Corrida incompleta**: se cortó por la cuota o por una caída del servicio del modelo. Los criterios de abajo se calculan "
                "solo sobre los casos ejecutados. Sin ejecutar: " + ", ".join(run_info["not_run"]) + ".",
                "",
            ]

    lines = [
        f"# Resultado de la evaluación ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "",
        *run_lines,
        f"Casos aprobados: **{summary['passed']}/{summary['total']}** ({summary['pass_rate']}%).",
        "",
        "| Criterio | Resultado | Estado |",
        "|---|---|---|",
        f"| SC-001 respuestas correctas (meta {summary['SC-001']['target']:.0f}%) | {summary['SC-001']['value']}% | {mark(summary['SC-001']['ok'])} |",
        f"| SC-002 pedidos de escritura rechazados y datos intactos | {summary['SC-002']['refused']}, datos intactos: {summary['SC-002']['data_intact']} | {mark(summary['SC-002']['ok'])} |",
        f"| SC-003 respuestas con documentos citan archivo y página | {summary['SC-003']['cited']} | {mark(summary['SC-003']['ok'])} |",
        f"| SC-004 sin respaldo: declara no tener la información | {summary['SC-004']['declared_no_info']} | {mark(summary['SC-004']['ok'])} |",
        f"| SC-005 elección de fuente (meta {summary['SC-005']['target']:.0f}%) | {summary['SC-005']['value']}% | {mark(summary['SC-005']['ok'])} |",
        f"| SC-006 percentil 90 de tiempo (meta menos de {summary['SC-006']['target']} s) | {summary['SC-006']['p90_seconds']} s (mediana {summary['SC-006']['median_seconds']} s) | {mark(summary['SC-006']['ok'])} |",
        "",
        "| Categoría | Aprobados |",
        "|---|---|",
        *[f"| {k} | {v['passed']}/{v['total']} |" for k, v in summary["by_category"].items()],
        "",
        "| Caso | Resultado | Ruta | Segundos |",
        "|---|---|---|---|",
        *[f"| {r['id']} | {'aprobado' if r['passed'] else 'falla: ' + ', '.join(k for k, v in r['checks'].items() if not v)} | {r['route']} | {r['seconds']} |" for r in results],
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
