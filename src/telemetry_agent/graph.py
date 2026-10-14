"""El agente como un grafo de LangGraph.

    router -> (sql_generate -> sql_validate -> sql_execute) -> retrieve -> synthesize
                       ^________ reintento con el motivo del error ______|

La decision de que fuente usar es un nodo propio (router), no algo implicito en un prompt largo
(principio III). Cada nodo aparece como un tramo separado en la traza de LangSmith.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, TypedDict

import psycopg
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .config import get_settings
from .db import QueryResult, run_readonly
from .embeddings import Embedder
from .llm import LLM
from .models import AgentResponse, RouteDecision, Source, SynthesisOutput
from .prompts import (
    ROUTER_SYSTEM,
    SQL_FEEDBACK,
    SQL_SYSTEM,
    SQL_USER,
    SYNTH_SYSTEM,
    SYNTH_USER,
)
from .retriever import retrieve as default_retrieve
from .schema_context import build_schema_context, data_period
from .sql_guard import validate_sql

HISTORY_TURNS = 4
MAX_EVIDENCE_ROWS = 50

MESSAGES = {
    "refused": {
        "es": "Solo puedo consultar informacion de la planta. No puedo crear, modificar ni borrar datos.",
        "en": "I can only look up plant information. I can't create, modify or delete data.",
    },
    "sql_failed": {
        "es": "No pude obtener ese dato de la base de datos. Probá reformular la pregunta.",
        "en": "I couldn't get that data from the database. Try rephrasing the question.",
    },
    "none": {
        "es": "Hola, soy el asistente de la planta. Puedo responder sobre equipos, alarmas y órdenes de mantenimiento, y sobre los manuales y procedimientos.",
        "en": "Hi, I'm the plant assistant. I can answer about equipment, alarms and maintenance orders, and about the manuals and procedures.",
    },
    "no_docs": {
        "es": "No encontré esa información en los documentos disponibles.",
        "en": "I couldn't find that information in the available documents.",
    },
    "error": {
        "es": "No pude completar la consulta por un problema técnico: {detail}",
        "en": "I couldn't complete the request because of a technical problem: {detail}",
    },
    "quota": {
        "es": "Se alcanzó el límite de uso del modelo de lenguaje (capa gratuita). Probá de nuevo en un minuto.",
        "en": "The language model usage limit was reached (free tier). Please try again in a minute.",
    },
    "quota_day": {
        "es": "Se alcanzó el límite diario de uso del modelo de lenguaje (capa gratuita). Se renueva al día siguiente.",
        "en": "The daily usage limit of the language model was reached (free tier). It resets the next day.",
    },
}


class AgentState(TypedDict, total=False):
    question: str
    history: list[dict[str, str]]
    route: str
    route_reason: str
    language: str
    direct_reply: str | None
    sql: str | None
    sql_attempts: int
    sql_feedback: str | None
    sql_status: str  # validated | invalid | refused | done | error
    sql_gave_up: bool
    columns: list[str]
    rows: list[dict[str, Any]] | None
    rows_truncated: bool
    chunks: list[dict[str, Any]]
    answer: str
    grounded: bool
    refused: bool
    sources: list[dict[str, Any]]
    error: str | None


def extract_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip()


def format_history(history: list[dict[str, str]] | None) -> str:
    if not history:
        return "(sin historial)"
    lines = []
    for turn in history[-HISTORY_TURNS:]:
        lines.append(f"Usuario: {turn['q']}")
        lines.append(f"Asistente: {turn['a'][:400]}")
    return "\n".join(lines)


def _message(key: str, language: str, **kw: str) -> str:
    return MESSAGES[key].get(language, MESSAGES[key]["es"]).format(**kw)


_QUOTA_ID = re.compile(r"quotaId['\"]: ['\"]([^'\"]+)")
_QUOTA_VALUE = re.compile(r"quotaValue['\"]: ['\"](\d+)")


def quota_scope(text: str | None) -> str | None:
    """Que limite de la capa gratuita se alcanzo: "day", "minute", o None si no es un error de cuota.

    Gemini lo informa en el campo quotaId del error, por ejemplo
    GenerateRequestsPerDayPerProjectPerModel-FreeTier.
    """
    if not text or not any(k in text for k in ("429", "RESOURCE_EXHAUSTED", "quota", "Quota")):
        return None
    return "day" if "PerDay" in text else "minute"


def _friendly_error(exc: Exception) -> tuple[str, bool]:
    """Devuelve (detalle corto, es_error_de_cuota)."""
    text = str(exc)
    detail = text.splitlines()[0][:300] if text else exc.__class__.__name__
    scope = quota_scope(text)
    if scope:
        # El detalle se recorta, asi que se le agrega el limite alcanzado para no perderlo.
        ids, values = _QUOTA_ID.findall(text), _QUOTA_VALUE.findall(text)
        pick = next((i for i, q in enumerate(ids) if "PerDay" in q), 0)
        if ids:
            limit = f", limite {values[pick]}" if pick < len(values) else ""
            detail += f" [cuota: {ids[pick]}{limit}]"
    return detail, scope is not None


def _with_history(state: AgentState, answer: str) -> list[dict[str, str]]:
    history = list(state.get("history") or [])
    history.append({"q": state["question"], "a": answer})
    return history[-HISTORY_TURNS:]


def build_graph(
    llm: LLM,
    embedder: Embedder,
    *,
    run_sql: Callable[[str], QueryResult] = run_readonly,
    schema_text: Callable[[], str] = build_schema_context,
    period_text: Callable[[], str] = data_period,
    retrieve_fn: Callable[..., list[dict]] = default_retrieve,
    checkpointer: Any = None,
):
    settings = get_settings()
    max_attempts = 1 + settings.sql_max_retries

    # ---------------------------------------------------------------- router
    def router(state: AgentState) -> dict:
        try:
            user = f"Historial reciente:\n{format_history(state.get('history'))}\n\nPregunta: {state['question']}"
            decision = llm.structured(ROUTER_SYSTEM, user, RouteDecision)
        except Exception as exc:  # noqa: BLE001
            return {"error": _fail_text(exc)}
        return {
            "route": decision.route,
            "route_reason": decision.reason,
            "language": decision.language,
            "direct_reply": (decision.direct_reply or "").strip() or None,
        }

    def after_router(state: AgentState) -> str:
        if state.get("error"):
            return "fail"
        route = state["route"]
        if route in ("none", "refuse"):
            return "reply_direct"
        if route == "docs":
            return "retrieve"
        return "sql_generate"

    def reply_direct(state: AgentState) -> dict:
        refused = state["route"] == "refuse"
        answer = state.get("direct_reply") or (
            _message("refused", state["language"]) if refused else _message("none", state["language"])
        )
        return {"answer": answer, "refused": refused, "grounded": True, "history": _with_history(state, answer)}

    # ------------------------------------------------------------------- sql
    def sql_generate(state: AgentState) -> dict:
        attempts = state.get("sql_attempts", 0) + 1
        feedback = ""
        if state.get("sql_feedback"):
            feedback = SQL_FEEDBACK.format(previous_sql=state.get("sql") or "", reason=state["sql_feedback"])
        try:
            text = llm.text(
                SQL_SYSTEM.format(schema=schema_text()),
                SQL_USER.format(
                    history=format_history(state.get("history")), question=state["question"], feedback=feedback
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": _fail_text(exc)}
        return {"sql": extract_sql(text), "sql_attempts": attempts}

    def sql_validate(state: AgentState) -> dict:
        result = validate_sql(state.get("sql") or "")
        if result.ok:
            return {"sql": result.sql, "sql_status": "validated", "sql_feedback": None}
        if result.kind == "not_read_only":
            return {"sql_status": "refused", "sql_feedback": result.reason}
        return {"sql_status": "invalid", "sql_feedback": result.reason}

    def after_validate(state: AgentState) -> str:
        if state.get("error"):
            return "fail"
        status = state["sql_status"]
        if status == "validated":
            return "sql_execute"
        if status == "refused":
            return "reply_refused"
        return "sql_generate" if state["sql_attempts"] < max_attempts else "sql_give_up"

    def reply_refused(state: AgentState) -> dict:
        answer = _message("refused", state.get("language", "es"))
        return {"answer": answer, "refused": True, "grounded": True, "sql": None,
                "history": _with_history(state, answer)}

    def sql_execute(state: AgentState) -> dict:
        try:
            result = run_sql(state["sql"])
        except psycopg.Error as exc:
            reason = str(exc).splitlines()[0][:300]
            return {"sql_status": "error", "sql_feedback": f"Error de la base de datos: {reason}"}
        return {
            "sql_status": "done",
            "columns": result.columns,
            "rows": result.rows,
            "rows_truncated": result.truncated,
        }

    def after_execute(state: AgentState) -> str:
        if state["sql_status"] == "done":
            return _after_sql(state)
        return "sql_generate" if state["sql_attempts"] < max_attempts else "sql_give_up"

    def sql_give_up(state: AgentState) -> dict:
        return {"sql_gave_up": True, "rows": None}

    def _after_sql(state: AgentState) -> str:
        return "retrieve" if state["route"] == "both" else "synthesize"

    # ------------------------------------------------------------- retrieval
    def retrieve(state: AgentState) -> dict:
        query = state["question"]
        rows = state.get("rows")
        if rows:
            query += "\n" + json.dumps(rows[:3], ensure_ascii=False, default=str)[:300]
        try:
            chunks = retrieve_fn(query, embedder, settings.retrieval_top_k)
        except Exception as exc:  # noqa: BLE001
            return {"error": _fail_text(exc)}
        return {"chunks": chunks}

    # ------------------------------------------------------------ synthesize
    def synthesize(state: AgentState) -> dict:
        language = state.get("language", "es")
        route = state["route"]
        chunks = state.get("chunks") or []
        uses_db = route in ("sql", "both")
        uses_docs = route in ("docs", "both")

        # Casos que se resuelven sin gastar una llamada al modelo.
        if route == "sql" and state.get("sql_gave_up"):
            answer = _message("sql_failed", language)
            return {"answer": answer, "grounded": False, "sources": [], "history": _with_history(state, answer)}
        if route == "docs" and not chunks:
            answer = _message("no_docs", language)
            return {"answer": answer, "grounded": False, "sources": [], "history": _with_history(state, answer)}

        if uses_db:
            if state.get("sql_gave_up"):
                db_evidence = "La consulta a la base de datos fallo y no se pudo obtener el dato."
            else:
                # La consulta va como contexto: sin ella la sintesis no sabe que filtros ya cumplen las filas.
                try:
                    period = period_text()
                except Exception:  # noqa: BLE001  sin el periodo la respuesta igual se puede armar
                    period = ""
                payload = {
                    "periodo_con_datos": period,
                    "consulta": state.get("sql"),
                    "columnas": state.get("columns", []),
                    "filas": (state.get("rows") or [])[:MAX_EVIDENCE_ROWS],
                }
                note = " (resultado recortado: hay mas filas que las mostradas)" if state.get("rows_truncated") else ""
                db_evidence = json.dumps(payload, ensure_ascii=False, default=str) + note
        else:
            db_evidence = "(no se consulto la base de datos)"

        if uses_docs and chunks:
            doc_evidence = "\n\n".join(
                f"[{i}] ({c['archivo']}, pagina {c['pagina']})\n{c['texto']}" for i, c in enumerate(chunks, start=1)
            )
        else:
            doc_evidence = "(no se consultaron documentos)"

        try:
            out = llm.structured(
                SYNTH_SYSTEM,
                SYNTH_USER.format(
                    question=state["question"],
                    history=format_history(state.get("history")),
                    db_evidence=db_evidence,
                    doc_evidence=doc_evidence,
                ),
                SynthesisOutput,
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": _fail_text(exc)}

        sources: list[dict[str, Any]] = []
        if out.grounded and uses_docs and chunks:
            picked = [chunks[i - 1] for i in out.used_fragments if 1 <= i <= len(chunks)]
            if not picked and route == "docs":
                picked = chunks[:1]  # una respuesta basada en documentos siempre cita al menos uno (SC-003)
            sources = [{"archivo": c["archivo"], "pagina": c["pagina"], "texto": c["texto"]} for c in picked]
        return {
            "answer": out.answer,
            "grounded": out.grounded,
            "sources": sources,
            "history": _with_history(state, out.answer),
        }

    # ------------------------------------------------------------------ fail
    def fail(state: AgentState) -> dict:
        detail = state.get("error") or ""
        language = state.get("language", "es")
        if detail.startswith("QUOTA:"):
            answer = _message("quota_day" if quota_scope(detail) == "day" else "quota", language)
        else:
            answer = _message("error", language, detail=detail)
        return {"answer": answer, "grounded": False, "sources": [], "history": _with_history(state, answer)}

    def after_retrieve(state: AgentState) -> str:
        return "fail" if state.get("error") else "synthesize"

    def after_synthesize(state: AgentState) -> str:
        return "fail" if state.get("error") else END

    g = StateGraph(AgentState)
    for name, fn in [
        ("router", router), ("reply_direct", reply_direct), ("sql_generate", sql_generate),
        ("sql_validate", sql_validate), ("reply_refused", reply_refused), ("sql_execute", sql_execute),
        ("sql_give_up", sql_give_up), ("retrieve", retrieve), ("synthesize", synthesize), ("fail", fail),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", after_router,
                            ["fail", "reply_direct", "retrieve", "sql_generate"])
    g.add_edge("reply_direct", END)
    g.add_conditional_edges("sql_generate", lambda s: "fail" if s.get("error") else "sql_validate",
                            ["fail", "sql_validate"])
    g.add_conditional_edges("sql_validate", after_validate,
                            ["fail", "sql_execute", "reply_refused", "sql_generate", "sql_give_up"])
    g.add_edge("reply_refused", END)
    g.add_conditional_edges("sql_execute", after_execute,
                            ["retrieve", "synthesize", "sql_generate", "sql_give_up"])
    g.add_conditional_edges("sql_give_up", _after_sql, ["retrieve", "synthesize"])
    g.add_conditional_edges("retrieve", after_retrieve, ["fail", "synthesize"])
    g.add_conditional_edges("synthesize", after_synthesize, ["fail", END])
    g.add_edge("fail", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())


def _fail_text(exc: Exception) -> str:
    detail, quota = _friendly_error(exc)
    return ("QUOTA:" if quota else "") + detail


_RESET: dict[str, Any] = {
    "route": "none", "route_reason": "", "language": "es", "direct_reply": None,
    "sql": None, "sql_attempts": 0, "sql_feedback": None, "sql_status": "", "sql_gave_up": False,
    "columns": [], "rows": None, "rows_truncated": False, "chunks": [],
    "answer": "", "grounded": True, "refused": False, "sources": [], "error": None,
}


class Agent:
    """Envuelve el grafo con una interfaz simple: preguntar y recibir un AgentResponse."""

    def __init__(self, llm: LLM | None = None, embedder: Embedder | None = None, **kwargs: Any) -> None:
        if llm is None:
            from .llm import get_llm

            llm = get_llm()
        if embedder is None:
            from .embeddings import get_embedder

            embedder = get_embedder()
        self.graph = build_graph(llm, embedder, **kwargs)

    def ask(
        self,
        question: str,
        thread_id: str = "default",
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> AgentResponse:
        """metadata y tags se adjuntan a la traza de LangSmith (la evaluacion los usa para
        vincular cada traza con su caso)."""
        state = self.graph.invoke(
            {"question": question, **_RESET},
            config={
                "configurable": {"thread_id": thread_id},
                "run_name": "agente-sql-telemetria",
                "tags": ["telemetria", "tp-integrador", *(tags or [])],
                "metadata": metadata or {},
            },
        )
        return AgentResponse(
            answer=state["answer"],
            route=state["route"],
            route_reason=state.get("route_reason", ""),
            sql=state.get("sql") if state["route"] in ("sql", "both") and not state.get("refused") else None,
            rows=state.get("rows"),
            rows_truncated=state.get("rows_truncated", False),
            sources=[Source(**s) for s in state.get("sources", [])],
            refused=state.get("refused", False),
            grounded=state.get("grounded", True),
            error=(state["error"].removeprefix("QUOTA:") or None) if state.get("error") else None,
        )
