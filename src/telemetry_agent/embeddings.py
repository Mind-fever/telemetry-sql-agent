"""Embeddings para el RAG.

GeminiEmbedder llama al modelo real. HashEmbedder es una version falsa y determinista que se usa
en las pruebas automaticas: no entiende significado, solo comparte palabras, pero alcanza para
comprobar que la recuperacion y el ordenamiento funcionan sin gastar cuota ni requerir API key.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from typing import Protocol

from .config import get_settings


class Embedder(Protocol):
    dimensions: int

    def embed_documents(self, items: list[tuple[str, str]]) -> list[list[float]]:
        """items: lista de (titulo, texto)."""

    def embed_query(self, text: str) -> list[float]: ...


class GeminiEmbedder:
    """Embeddings de Gemini con el SDK oficial google-genai.

    gemini-embedding-2 no admite task_type: la tarea se indica con un prefijo en el texto.
    Para gemini-embedding-001 si se usa task_type. Ver specs/001-agente-sql-telemetria/research.md (D2).
    """

    BATCH = 16

    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("Falta GEMINI_API_KEY en el entorno (ver .env.example).")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self._prefixed = "embedding-2" in self._model

    def _embed(self, contents: list[str], task_type: str | None) -> list[list[float]]:
        from google.genai import types

        config_args: dict = {"output_dimensionality": self.dimensions}
        if task_type and not self._prefixed:
            config_args["task_type"] = task_type
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                result = self._client.models.embed_content(
                    model=self._model, contents=contents, config=types.EmbedContentConfig(**config_args)
                )
                return [list(e.values) for e in result.embeddings]
            except Exception as exc:  # cuota o error transitorio: espera creciente
                last_error = exc
                time.sleep(2 * (attempt + 1) ** 2)
        raise RuntimeError(f"No se pudo calcular el embedding: {last_error}")

    def embed_documents(self, items: list[tuple[str, str]]) -> list[list[float]]:
        texts = [
            f"title: {title or 'none'} | text: {text}" if self._prefixed else text for title, text in items
        ]
        out: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH):
            out.extend(self._embed(texts[i:i + self.BATCH], "RETRIEVAL_DOCUMENT"))
        return out

    def embed_query(self, text: str) -> list[float]:
        content = f"task: search result | query: {text}" if self._prefixed else text
        return self._embed([content], "RETRIEVAL_QUERY")[0]


_WORD = re.compile(r"[a-z0-9]+")


def _strip_accents(text: str) -> str:
    table = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return text.translate(table)


class HashEmbedder:
    """Embedding falso: bolsa de palabras con hashing, normalizado. Solo para pruebas."""

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for word in _WORD.findall(_strip_accents(text).lower()):
            if len(word) < 3:
                continue
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[h % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, items: list[tuple[str, str]]) -> list[list[float]]:
        return [self._vector(f"{title} {text}") for title, text in items]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def get_embedder() -> Embedder:
    return GeminiEmbedder()
