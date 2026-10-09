"""Tipos compartidos: la salida estructurada del modelo y la respuesta del agente.

AgentResponse es el contrato descrito en specs/001-agente-sql-telemetria/contracts/agent-response.md.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Route = Literal["sql", "docs", "both", "none", "refuse"]


class RouteDecision(BaseModel):
    """Decision del nodo router: que fuente usar para esta pregunta."""

    route: Route = Field(description="sql, docs, both, none o refuse")
    reason: str = Field(description="Justificacion de una frase de por que se eligio esa ruta")
    language: Literal["es", "en"] = Field(description="Idioma de la pregunta del usuario")
    direct_reply: str | None = Field(
        default=None,
        description="Solo para none o refuse: la respuesta final al usuario, en su idioma. Vacio en las demas rutas.",
    )


class SynthesisOutput(BaseModel):
    """Salida del nodo synthesize."""

    answer: str = Field(description="Respuesta final, en el idioma de la pregunta, basada solo en la evidencia")
    grounded: bool = Field(description="False si la evidencia no alcanza para responder")
    used_fragments: list[int] = Field(
        default_factory=list,
        description="Numeros de los fragmentos de documentos que se usaron para responder (los de la lista)",
    )


class Source(BaseModel):
    archivo: str
    pagina: int
    texto: str


class AgentResponse(BaseModel):
    answer: str
    route: Route
    route_reason: str = ""
    sql: str | None = None
    rows: list[dict[str, Any]] | None = None
    rows_truncated: bool = False
    sources: list[Source] = Field(default_factory=list)
    refused: bool = False
    grounded: bool = True
    error: str | None = None
