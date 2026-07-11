from __future__ import annotations

from functools import lru_cache
from typing import Protocol


class Embedder(Protocol):
    model_name: str

    def encode(self, texts: list[str], batch_size: int) -> list[list[float]]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str], batch_size: int) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.astype(float).tolist()


@lru_cache(maxsize=1)
def get_embedder(model_name: str) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(model_name)
