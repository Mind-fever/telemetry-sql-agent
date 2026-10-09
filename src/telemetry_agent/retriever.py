"""Busqueda de fragmentos de documentos por similitud (RAG)."""

from __future__ import annotations

from .config import get_settings
from .db import connect_readonly
from .embeddings import Embedder


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.7f}" for v in values) + "]"


def retrieve(query: str, embedder: Embedder, k: int | None = None) -> list[dict]:
    """Devuelve los k fragmentos mas cercanos a la consulta, con archivo y pagina de origen.

    Usa distancia coseno (operador <=> de pgvector). Como son pocos fragmentos no hace falta indice.
    """
    k = k or get_settings().retrieval_top_k
    vector = _vector_literal(embedder.embed_query(query))
    with connect_readonly() as conn:
        rows = conn.execute(
            "select archivo, pagina, orden, texto, embedding <=> %s::vector as distancia "
            "from doc_chunks order by distancia limit %s",
            (vector, k),
        ).fetchall()
        conn.rollback()
    return [
        {"archivo": r[0], "pagina": r[1], "orden": r[2], "texto": r[3], "distancia": float(r[4])}
        for r in rows
    ]
