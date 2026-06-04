"""
Embedder — generates dense vector embeddings for RAG pipeline.
Supports OpenAI and local sentence-transformer backends.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class EmbedderBackend(str, Enum):
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    STUB = "stub"


class BaseEmbedder(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...


class OpenAIEmbedder(BaseEmbedder):
    _DIMENSION = 1536

    def __init__(self, model: str = "text-embedding-3-small", batch_size: int = 512) -> None:
        import openai
        self._client = openai.AsyncOpenAI()
        self._model = model
        self._batch_size = batch_size

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i: i + self._batch_size]
            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            results.extend([item.embedding for item in response.data])
            logger.debug(
                "Embedded batch | model=%s batch_size=%d offset=%d",
                self._model,
                len(batch),
                i,
            )
        return results

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed_texts([query])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._DIMENSION


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False),
        )
        return embeddings.tolist()

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed_texts([query])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._dim


class StubEmbedder(BaseEmbedder):
    """Deterministic stub embedder for testing — no external calls."""
    _DIM = 384

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        rng = np.random.default_rng(seed=42)
        return [rng.standard_normal(self._DIM).tolist() for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed_texts([query])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._DIM


def create_embedder(backend: EmbedderBackend, **kwargs: Any) -> BaseEmbedder:
    mapping: dict[EmbedderBackend, type[BaseEmbedder]] = {
        EmbedderBackend.OPENAI: OpenAIEmbedder,
        EmbedderBackend.SENTENCE_TRANSFORMERS: SentenceTransformerEmbedder,
        EmbedderBackend.STUB: StubEmbedder,
    }
    cls = mapping[backend]
    return cls(**kwargs)
