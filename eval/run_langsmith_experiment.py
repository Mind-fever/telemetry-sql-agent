"""Corre la evaluacion como un experimento de LangSmith.

Hace lo mismo que eval/run_eval.py, pero usando la evaluacion propia de LangSmith:
1. Sube los casos de eval/golden.jsonl como un conjunto de datos (si todavia no existe).
2. Corre el agente sobre cada caso. Cada ejecucion queda trazada y vinculada a su caso.
3. Aplica las mismas verificaciones deterministas de run_eval.py y guarda el resultado de cada
   una como feedback del experimento.

El resultado se ve en LangSmith, en "Datasets & Experiments". No reemplaza a run_eval.py, que
sigue siendo la forma de evaluar sin depender de LangSmith.

Uso:
    python eval/run_langsmith_experiment.py
    python eval/run_langsmith_experiment.py --delay 12

Requiere LANGSMITH_API_KEY y GEMINI_API_KEY en .env.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

import run_eval as ev  # noqa: E402

from telemetry_agent.config import get_settings  # noqa: E402
from telemetry_agent.db import connect_admin  # noqa: E402
from telemetry_agent.graph import quota_scope  # noqa: E402
from telemetry_agent.models import AgentResponse  # noqa: E402

DATASET = "agente-sql-telemetria-golden"
# Claves del caso que describen lo esperado; van a "outputs" del ejemplo en LangSmith.
EXPECTED_KEYS = ("expect_route", "expect_refused", "expect_grounded", "expect_source", "expect_truncated",
                 "answer_contains", "answer_regex", "answer_excludes", "reference_sql")


def ensure_dataset(client, cases: list[dict]) -> None:
    """Crea el conjunto de datos con un ejemplo por caso. Si ya existe, agrega solo los casos nuevos
    (no modifica ni borra los ejemplos que ya estan)."""
    if client.has_dataset(dataset_name=DATASET):
        dataset = client.read_dataset(dataset_name=DATASET)
        known = {(e.metadata or {}).get("case_id") for e in client.list_examples(dataset_id=dataset.id)}
        missing = [c for c in cases if c["id"] not in known]
        print(f"El conjunto de datos '{DATASET}' ya existe ({len(known)} ejemplos).")
    else:
        dataset = client.create_dataset(
            DATASET, description="Casos de evaluacion del agente SQL de telemetria (eval/golden.jsonl)."
        )
        missing = cases
    if not missing:
        return
    client.create_examples(
        dataset_id=dataset.id,
        examples=[
            {
                "inputs": {"turns": case.get("turns") or [case["question"]]},
                "outputs": {k: case[k] for k in EXPECTED_KEYS if k in case},
                "metadata": {"case_id": case["id"], "category": case["category"]},
            }
            for case in missing
        ],
    )
    print(f"Se agregaron {len(missing)} ejemplos: {', '.join(c['id'] for c in missing)}.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=10.0, help="segundos antes de cada caso (cuidar la cuota gratuita)")
    args = ap.parse_args()

    from langsmith import Client, evaluate

    from telemetry_agent.graph import Agent

    cases = ev.load_cases()
    with connect_admin() as conn:
        refs = {c["id"]: ev.flatten(ev.run_reference(conn, c["reference_sql"])) for c in cases if "reference_sql" in c}
        before = ev.table_counts(conn)

    client = Client()
    ensure_dataset(client, cases)
    agent = Agent()

    def ask_all(turns: list[str]) -> AgentResponse:
        thread = uuid.uuid4().hex
        resp = None
        for turn in turns:
            resp = agent.ask(turn, thread, tags=["experimento"])
        return resp

    def target(inputs: dict) -> dict:
        time.sleep(args.delay)
        resp = ask_all(inputs["turns"])
        if quota_scope(resp.error) == "minute":
            time.sleep(ev.QUOTA_WAIT_SECONDS)
            resp = ask_all(inputs["turns"])
        if quota_scope(resp.error):
            raise RuntimeError(f"Cuota del modelo agotada: {resp.error[-120:]}")
        return resp.model_dump()

    def checks(run, example) -> list[dict]:
        meta = example.metadata or {}
        case = {**(example.outputs or {}), "id": meta.get("case_id"), "category": meta.get("category")}
        if not run.outputs or "answer" not in run.outputs:
            return [{"key": "caso_aprobado", "score": 0, "comment": str(run.error)[:200]}]
        resp = AgentResponse(**run.outputs)
        result = ev.evaluate_case(case, resp, refs.get(case["id"]))
        if resp.error:
            result["sin_error_tecnico"] = False
        out = [{"key": name, "score": int(ok)} for name, ok in result.items()]
        out.append({"key": "caso_aprobado", "score": int(bool(result) and all(result.values()))})
        return out

    model = get_settings().gemini_model
    results = evaluate(
        target,
        data=DATASET,
        evaluators=[checks],
        experiment_prefix=model,
        description="Agente SQL de telemetria: verificaciones deterministas sobre eval/golden.jsonl.",
        metadata={"modelo": model},
        max_concurrency=1,
        client=client,
    )

    passed = total = 0
    for row in results:
        scores = {r.key: r.score for r in row["evaluation_results"]["results"]}
        total += 1
        passed += int(scores.get("caso_aprobado") == 1)
    with connect_admin() as conn:
        intact = ev.table_counts(conn) == before
    print(f"\nExperimento: {results.experiment_name}")
    print(f"Casos aprobados: {passed}/{total}. Datos intactos: {intact}.")


if __name__ == "__main__":
    main()
