"""
RAG Vector Store
Abstraction layer supporting FAISS (local) and PGVector (Postgres).
Async-first design with full CRUD for document vectors.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VectorStoreBackend(str, Enum):
    FAISS = "faiss"
    PGVECTOR = "pgvector"
    MEMORY = "memory"


class VectorDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None


class SearchResult(BaseModel):
    documents: list[VectorDocument]
    query_latency_ms: float
    total_searched: int


class VectorStoreConfig(BaseModel):
    backend: VectorStoreBackend = VectorStoreBackend.FAISS
    dimension: int = 1536
    index_path: str | None = None
    pg_dsn: str | None = None
    pg_table: str = "nba_embeddings"
    faiss_nlist: int = 100
    faiss_nprobe: int = 10
    similarity_metric: str = "cosine"


class BaseVectorStore(ABC):
    """Abstract interface every vector store backend must implement."""

    @abstractmethod
    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Insert documents; returns list of assigned IDs."""

    @abstractmethod
    async def search(
        self, query_embedding: list[float], top_k: int, filter_metadata: dict | None
    ) -> SearchResult:
        """Nearest-neighbour search."""

    @abstractmethod
    async def delete(self, doc_ids: list[str]) -> int:
        """Delete documents by ID; returns deleted count."""

    @abstractmethod
    async def count(self) -> int:
        """Total document count."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if store is operational."""


# ---------------------------------------------------------------------------
# In-Memory Backend (development / testing)
# ---------------------------------------------------------------------------

class InMemoryVectorStore(BaseVectorStore):
    """Brute-force cosine search; suitable for dev and tests."""

    def __init__(self, config: VectorStoreConfig) -> None:
        self._config = config
        self._store: dict[str, VectorDocument] = {}
        logger.info("InMemoryVectorStore initialised")

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        ids: list[str] = []
        for doc in documents:
            self._store[doc.id] = doc
            ids.append(doc.id)
        logger.debug("Documents added", extra={"count": len(documents)})
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> SearchResult:
        start = time.monotonic()
        query_vec = np.array(query_embedding, dtype=np.float32)
        norm_q = np.linalg.norm(query_vec)
        if norm_q > 0:
            query_vec /= norm_q

        candidates = list(self._store.values())
        if filter_metadata:
            candidates = [
                d for d in candidates
                if all(d.metadata.get(k) == v for k, v in filter_metadata.items())
            ]

        scored: list[tuple[float, VectorDocument]] = []
        for doc in candidates:
            doc_vec = np.array(doc.embedding, dtype=np.float32)
            norm_d = np.linalg.norm(doc_vec)
            if norm_d > 0:
                doc_vec /= norm_d
            score = float(np.dot(query_vec, doc_vec))
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        results = [
            VectorDocument(**doc.model_dump(exclude={"score"}), score=score)
            for score, doc in top
        ]

        latency_ms = (time.monotonic() - start) * 1000
        return SearchResult(
            documents=results,
            query_latency_ms=round(latency_ms, 2),
            total_searched=len(candidates),
        )

    async def delete(self, doc_ids: list[str]) -> int:
        deleted = 0
        for doc_id in doc_ids:
            if doc_id in self._store:
                del self._store[doc_id]
                deleted += 1
        return deleted

    async def count(self) -> int:
        return len(self._store)

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# FAISS Backend
# ---------------------------------------------------------------------------

class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-backed vector store with IVF flat index.
    Falls back to flat index when corpus < nlist.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        import faiss  # type: ignore

        self._config = config
        self._faiss = faiss
        self._dimension = config.dimension
        self._id_map: dict[int, str] = {}
        self._doc_map: dict[str, VectorDocument] = {}
        self._next_int_id = 0
        self._index: Any = faiss.IndexFlatIP(config.dimension)
        logger.info(
            "FAISSVectorStore initialised",
            extra={"dimension": config.dimension},
        )

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        ids: list[str] = []
        vectors: list[list[float]] = []

        for doc in documents:
            int_id = self._next_int_id
            self._next_int_id += 1
            self._id_map[int_id] = doc.id
            self._doc_map[doc.id] = doc
            vectors.append(doc.embedding)
            ids.append(doc.id)

        if vectors:
            arr = np.array(vectors, dtype=np.float32)
            # Normalise for cosine similarity via inner product
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            arr /= norms
            self._index.add(arr)

        logger.debug("FAISS documents added", extra={"count": len(documents)})
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> SearchResult:
        start = time.monotonic()
        query_arr = np.array([query_embedding], dtype=np.float32)
        norm = np.linalg.norm(query_arr)
        if norm > 0:
            query_arr /= norm

        search_k = min(top_k * (3 if filter_metadata else 1), self._index.ntotal)
        if search_k == 0:
            return SearchResult(documents=[], query_latency_ms=0.0, total_searched=0)

        scores, int_ids = self._index.search(query_arr, search_k)
        results: list[VectorDocument] = []

        for score, int_id in zip(scores[0], int_ids[0]):
            if int_id < 0:
                continue
            doc_id = self._id_map.get(int(int_id))
            if not doc_id:
                continue
            doc = self._doc_map.get(doc_id)
            if not doc:
                continue
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            results.append(
                VectorDocument(**doc.model_dump(exclude={"score"}), score=float(score))
            )
            if len(results) >= top_k:
                break

        latency_ms = (time.monotonic() - start) * 1000
        return SearchResult(
            documents=results,
            query_latency_ms=round(latency_ms, 2),
            total_searched=self._index.ntotal,
        )

    async def delete(self, doc_ids: list[str]) -> int:
        # FAISS flat index doesn't support in-place delete;
        # rebuild index excluding deleted docs.
        deleted = 0
        remaining: list[VectorDocument] = []
        for doc_id, doc in self._doc_map.items():
            if doc_id in doc_ids:
                deleted += 1
            else:
                remaining.append(doc)

        self._doc_map = {d.id: d for d in remaining}
        self._id_map = {}
        self._next_int_id = 0
        self._index = self._faiss.IndexFlatIP(self._dimension)

        if remaining:
            await self.add_documents(remaining)

        return deleted

    async def count(self) -> int:
        return self._index.ntotal

    async def health_check(self) -> bool:
        try:
            _ = self._index.ntotal
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# PGVector Backend
# ---------------------------------------------------------------------------

class PGVectorStore(BaseVectorStore):
    """
    PostgreSQL pgvector backend using asyncpg.
    Table is auto-created on first connect.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        self._config = config
        self._pool: Any = None
        self._table = config.pg_table
        logger.info("PGVectorStore initialised", extra={"table": self._table})

    async def _get_pool(self) -> Any:
        if self._pool is None:
            import asyncpg  # type: ignore

            self._pool = await asyncpg.create_pool(self._config.pg_dsn)
            await self._ensure_table()
        return self._pool

    async def _ensure_table(self) -> None:
        pool = self._pool
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding vector({self._config.dimension}),
                    metadata JSONB DEFAULT '{{}}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self._table}_embedding_idx
                ON {self._table} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """
            )

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        import json as _json

        pool = await self._get_pool()
        ids: list[str] = []
        async with pool.acquire() as conn:
            for doc in documents:
                vec_str = "[" + ",".join(map(str, doc.embedding)) + "]"
                await conn.execute(
                    f"""
                    INSERT INTO {self._table} (id, text, embedding, metadata)
                    VALUES ($1, $2, $3::vector, $4::jsonb)
                    ON CONFLICT (id) DO UPDATE
                        SET text = EXCLUDED.text,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                    """,
                    doc.id,
                    doc.text,
                    vec_str,
                    _json.dumps(doc.metadata),
                )
                ids.append(doc.id)
        logger.debug("PGVector documents upserted", extra={"count": len(documents)})
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> SearchResult:
        import json as _json

        start = time.monotonic()
        pool = await self._get_pool()
        vec_str = "[" + ",".join(map(str, query_embedding)) + "]"

        where_clause = ""
        params: list[Any] = [vec_str, top_k]

        if filter_metadata:
            conditions = []
            for i, (k, v) in enumerate(filter_metadata.items(), start=3):
                conditions.append(f"metadata->>'{k}' = ${i}")
                params.append(str(v))
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, text, embedding::text, metadata,
                   1 - (embedding <=> $1::vector) AS score
            FROM {self._table}
            {where_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT $2;
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results: list[VectorDocument] = []
        for row in rows:
            emb_str: str = row["embedding"]
            emb = [float(x) for x in emb_str.strip("[]").split(",")]
            results.append(
                VectorDocument(
                    id=row["id"],
                    text=row["text"],
                    embedding=emb,
                    metadata=_json.loads(row["metadata"]),
                    score=float(row["score"]),
                )
            )

        latency_ms = (time.monotonic() - start) * 1000
        return SearchResult(
            documents=results,
            query_latency_ms=round(latency_ms, 2),
            total_searched=-1,
        )

    async def delete(self, doc_ids: list[str]) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self._table} WHERE id = ANY($1::text[])", doc_ids
            )
        deleted = int(result.split()[-1])
        return deleted

    async def count(self) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self._table}")
        return row["count"]

    async def health_check(self) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_vector_store(config: VectorStoreConfig) -> BaseVectorStore:
    """Factory that returns the right backend based on config."""
    match config.backend:
        case VectorStoreBackend.FAISS:
            return FAISSVectorStore(config)
        case VectorStoreBackend.PGVECTOR:
            return PGVectorStore(config)
        case VectorStoreBackend.MEMORY:
            return InMemoryVectorStore(config)
        case _:
            raise ValueError(f"Unknown vector store backend: {config.backend}")
