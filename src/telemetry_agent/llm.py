"""Modelo de lenguaje.

GeminiLLM usa ChatGoogleGenerativeAI de LangChain: asi cada llamada aparece como una ejecucion
de LLM dentro de la traza de LangSmith. FakeLLM es la version falsa para las pruebas automaticas.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from .config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLM(Protocol):
    def text(self, system: str, user: str) -> str: ...

    def structured(self, system: str, user: str, schema: type[T]) -> T: ...


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for part in content or []:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict) and part.get("type") == "text":
            parts.append(part.get("text", ""))
    return "".join(parts)


class GeminiLLM:
    def __init__(self) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("Falta GEMINI_API_KEY en el entorno (ver .env.example).")
        # max_retries reintenta con espera ante errores transitorios, incluido el limite de cuota.
        self._chat = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
            max_retries=4,
            timeout=60,
        )

    def _messages(self, system: str, user: str):
        from langchain_core.messages import HumanMessage, SystemMessage

        return [SystemMessage(content=system), HumanMessage(content=user)]

    def text(self, system: str, user: str) -> str:
        reply = self._chat.invoke(self._messages(system, user))
        return _content_to_text(reply.content).strip()

    def structured(self, system: str, user: str, schema: type[T]) -> T:
        result = self._chat.with_structured_output(schema).invoke(self._messages(system, user))
        if isinstance(result, dict):
            return schema(**result)
        return result  # type: ignore[return-value]


class FakeLLM:
    """Modelo falso con respuestas guionadas, consumidas en orden. Solo para pruebas."""

    def __init__(self, script: list[Any]) -> None:
        self._script = list(script)
        self.calls: list[dict[str, Any]] = []

    def _next(self, kind: str, system: str, user: str) -> Any:
        self.calls.append({"kind": kind, "system": system, "user": user})
        if not self._script:
            raise AssertionError("FakeLLM: se pidio mas respuestas de las guionadas.")
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def text(self, system: str, user: str) -> str:
        return str(self._next("text", system, user))

    def structured(self, system: str, user: str, schema: type[T]) -> T:
        item = self._next("structured", system, user)
        if isinstance(item, dict):
            return schema(**item)
        return item


def get_llm() -> LLM:
    return GeminiLLM()
