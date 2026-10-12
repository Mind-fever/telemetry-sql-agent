"""Pruebas de GeminiEmbedder con un cliente falso: no gastan cuota ni requieren API key.

Cubren el error de la primera ingesta real: el modelo devolvio un solo vector para un lote de
textos y la ingesta guardo 2 fragmentos en vez de 18 sin avisar.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from telemetry_agent.embeddings import GeminiEmbedder


class FakeModels:
    def __init__(self, vectors_per_call: int | None = None) -> None:
        self.calls: list[list] = []
        self._fixed = vectors_per_call

    def embed_content(self, model, contents, config):
        self.calls.append(contents)
        n = self._fixed if self._fixed is not None else len(contents)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1, 0.2]) for _ in range(n)])


def make_embedder(models: FakeModels) -> GeminiEmbedder:
    embedder = object.__new__(GeminiEmbedder)  # sin __init__: no hace falta API key
    embedder._client = SimpleNamespace(models=models)
    embedder._model = "gemini-embedding-2"
    embedder.dimensions = 2
    embedder._prefixed = True
    return embedder


def test_each_text_is_sent_as_its_own_content_and_gets_its_own_vector():
    models = FakeModels()
    vectors = make_embedder(models).embed_documents([("a.pdf", f"texto {i}") for i in range(18)])
    assert len(vectors) == 18
    assert [len(batch) for batch in models.calls] == [16, 2]
    first = models.calls[0][0]
    assert not isinstance(first, str) and first.parts[0].text == "title: a.pdf | text: texto 0"


def test_fails_if_the_model_returns_fewer_vectors_than_texts():
    embedder = make_embedder(FakeModels(vectors_per_call=1))
    with pytest.raises(RuntimeError, match="1 vectores para 3 textos"):
        embedder.embed_documents([("a.pdf", "uno"), ("a.pdf", "dos"), ("a.pdf", "tres")])
