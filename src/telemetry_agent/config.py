"""Configuracion del agente a partir de variables de entorno (ver .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

TIMEZONE = "America/Argentina/Buenos_Aires"  # zona horaria de la planta ficticia

# Tablas que puede consultar el SQL generado por el modelo (principio I de la constitucion).
# doc_chunks queda afuera a proposito: solo la lee el modulo de recuperacion.
ALLOWED_TABLES = (
    "areas",
    "tecnicos",
    "equipos",
    "sensores",
    "lecturas",
    "alarmas",
    "ordenes_mantenimiento",
)


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_url_ro: str
    gemini_api_key: str
    gemini_model: str
    embedding_model: str
    embedding_dimensions: int
    sql_max_rows: int
    sql_timeout_ms: int
    sql_max_retries: int
    retrieval_top_k: int
    langsmith_tracing: bool
    langsmith_project: str


def get_settings() -> Settings:
    """Lee la configuracion cada vez, asi las pruebas pueden cambiar el entorno."""
    return Settings(
        database_url=os.getenv("DATABASE_URL", ""),
        database_url_ro=os.getenv("DATABASE_URL_RO", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"),
        embedding_dimensions=_int("EMBEDDING_DIMENSIONS", 768),
        sql_max_rows=_int("SQL_MAX_ROWS", 50),
        sql_timeout_ms=_int("SQL_TIMEOUT_MS", 8000),
        sql_max_retries=_int("SQL_MAX_RETRIES", 2),
        retrieval_top_k=_int("RETRIEVAL_TOP_K", 4),
        langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "agente-sql-telemetria"),
    )


def tracing_enabled() -> bool:
    """El trazado con LangSmith se activa con LANGSMITH_TRACING=true y una API key.

    La propia libreria de LangSmith lee estas variables del entorno, por eso load_dotenv
    se llama al importar este modulo: antes de que se construya el grafo.
    """
    return get_settings().langsmith_tracing and bool(os.getenv("LANGSMITH_API_KEY"))
