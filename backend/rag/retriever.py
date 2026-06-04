"""
RAG Retriever
Hybrid retrieval combining dense (vector) and sparse (BM25/keyword) search.
Includes score fusion, deduplication, and pluggable ranking.
"""

from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.rag.embedder import Embedder, EmbeddingModel
from backend.rag.vector_store import BaseVectorStore, VectorDocument

logger = logging.getLogger(__name__)


class RetrievalMode(str, Enum):
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"


class RetrieverConfig(BaseModel):
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = Field(default=5, ge=1, le=100)
    dense_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    rrf_k: int = Field(default=60, ge=1)
    embedding_model: EmbeddingModel = EmbeddingModel.OPENAI_SMALL
    filter_metadata: dict[str, Any] | None = None
    score_threshold: float = 0.0


class RetrievedDocument(BaseModel):
    id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    retrieval_method: str


class RetrievalResult(BaseModel):
    documents: list[RetrievedDocument]
    query: str
    mode_used: RetrievalMode
    latency_ms: float
    dense_candidates: int = 0
    sparse_candidates: int = 0


class BM25Index:
    """
    Lightweight in-process BM25 implementation.
    Used for keyword-based sparse retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._corpus: list[tuple[str, dict]] = []
        self._doc_freqs: dict[str, int] = defaultdict(int)
        self._idf: dict[str, float] = {}
        self._doc_lengths: list[int] = []
        self._avg_dl: float = 0.0
        self._built = False

    def index(self, documents: list[tuple[str, str, dict]]) -> None:
        """
        Index documents.
        documents: list of (doc_id, text, metadata)
        """
        self._corpus = []
        self._doc_freqs = defaultdict(int)
        self._doc_lengths = []

        tokenized: list[list[str]] = []
        for doc_id, text, meta in documents:
            tokens = self._tokenize(text)
            tokenized.append(tokens)
            self._corpus.append((doc_id, meta))
            self._doc_lengths.append(len(tokens))
            for token in set(tokens):
                self._doc_freqs[token] += 1

        n = len(self._corpus)
        self._avg_dl = sum(self._doc_lengths) / n if n > 0 else 1.0

        for token, df in self._doc_freqs.items():
            self._idf[token] = math.log(
                (n - df + 0.5) / (df + 0.5) + 1
            )

        self._tokenized_corpus = tokenized
        self._built = True

    def search(self, query: str, top_k: int) -> list[tuple[str, float, dict]]:
        """Returns list of (doc_id, score, metadata)."""
        if not self._built or not self._corpus:
            return []

        query_tokens = self._tokenize(query)
        scores: list[float] = [0.0] * len(self._corpus)

        for token in query_tokens:
            if token not in self._idf:
                continue
            idf = self._idf[token]
            for idx, doc_tokens in enumerate(self._tokenized_corpus):
                tf = doc_tokens.count(token)
                if tf == 0:
                    continue
                dl = self._doc_lengths[idx]
                tf_norm = (
                    tf * (self.k1 + 1)
                ) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl)
                )
                scores[idx] += idf * tf_norm

        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        return [
            (self._corpus[i][0], score, self._corpus[i][1])
            for i, score in ranked
            if score > 0
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        return [w for w in text.split() if len(w) > 1]


class Retriever:
    """
    Hybrid retriever combining dense vector search and BM25 sparse search.
    Uses Reciprocal Rank Fusion (RRF) to merge result lists.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: Embedder,
        config: RetrieverConfig | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._config = config or RetrieverConfig()
        self._bm25 = BM25Index()
        self._bm25_docs: list[tuple[str, str, dict]] = []
        logger.info(
            "Retriever initialised",
            extra={"mode": self._config.mode},
        )

    async def add_to_sparse_index(
        self, documents: list[VectorDocument]
    ) -> None:
        """Update sparse BM25 index with new documents."""
        for doc in documents:
            self._bm25_docs.append((doc.id, doc.text, doc.metadata))
        self._bm25.index(self._bm25_docs)
        logger.debug(
            "BM25 index updated",
            extra={"total_docs": len(self._bm25_docs)},
        )

    async def retrieve(
        self, query: str, top_k: int | None = None
    ) -> RetrievalResult:
        """Main retrieval entry point."""
        k = top_k or self._config.top_k
        start = time.monotonic()
        mode = self._config.mode

        dense_docs: list[VectorDocument] = []
        sparse_docs: list[tuple[str, float, dict]] = []

        if mode in (RetrievalMode.DENSE, RetrievalMode.HYBRID):
            query_emb = await self._embedder.embed_single(
                query, self._config.embedding_model
            )
            search_result = await self._vector_store.search(
                query_embedding=query_emb,
                top_k=k * 2,
                filter_metadata=self._config.filter_metadata,
            )
            dense_docs = search_result.documents

        if mode in (RetrievalMode.SPARSE, RetrievalMode.HYBRID):
            sparse_docs = self._bm25.search(query, top_k=k * 2)

        if mode == RetrievalMode.DENSE:
            final = self._dense_to_retrieved(dense_docs, k)
        elif mode == RetrievalMode.SPARSE:
            final = self._sparse_to_retrieved(sparse_docs, k)
        else:
            final = self._rrf_fusion(dense_docs, sparse_docs, k)

        if self._config.score_threshold > 0:
            final = [d for d in final if d.score >= self._config.score_threshold]

        latency_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Retrieval complete",
            extra={
                "query_len": len(query),
                "returned": len(final),
                "mode": mode,
                "latency_ms": round(latency_ms, 2),
            },
        )

        return RetrievalResult(
            documents=final,
            query=query,
            mode_used=mode,
            latency_ms=round(latency_ms, 2),
            dense_candidates=len(dense_docs),
            sparse_candidates=len(sparse_docs),
        )

    def _dense_to_retrieved(
        self, docs: list[VectorDocument], k: int
    ) -> list[RetrievedDocument]:
        return [
            RetrievedDocument(
                id=d.id,
                text=d.text,
                score=d.score or 0.0,
                rank=i,
                metadata=d.metadata,
                retrieval_method="dense",
            )
            for i, d in enumerate(docs[:k])
        ]

    def _sparse_to_retrieved(
        self, docs: list[tuple[str, float, dict]], k: int
    ) -> list[RetrievedDocument]:
        return [
            RetrievedDocument(
                id=doc_id,
                text="",
                score=score,
                rank=i,
                metadata=meta,
                retrieval_method="sparse",
            )
            for i, (doc_id, score, meta) in enumerate(docs[:k])
        ]

    def _rrf_fusion(
        self,
        dense_docs: list[VectorDocument],
        sparse_docs: list[tuple[str, float, dict]],
        k: int,
    ) -> list[RetrievedDocument]:
        """Reciprocal Rank Fusion across dense + sparse result lists."""
        rrf_scores: dict[str, float] = defaultdict(float)
        doc_lookup: dict[str, dict] = {}

        for rank, doc in enumerate(dense_docs):
            rrf_scores[doc.id] += 1.0 / (self._config.rrf_k + rank + 1)
            doc_lookup[doc.id] = {
                "text": doc.text,
                "metadata": doc.metadata,
                "method": "hybrid",
            }

        for rank, (doc_id, _score, meta) in enumerate(sparse_docs):
            rrf_scores[doc_id] += 1.0 / (self._config.rrf_k + rank + 1)
            if doc_id not in doc_lookup:
                doc_lookup[doc_id] = {
                    "text": "",
                    "metadata": meta,
                    "method": "hybrid",
                }

        sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

        results: list[RetrievedDocument] = []
        for rank, doc_id in enumerate(sorted_ids[:k]):
            info = doc_lookup[doc_id]
            results.append(
                RetrievedDocument(
                    id=doc_id,
                    text=info["text"],
                    score=rrf_scores[doc_id],
                    rank=rank,
                    metadata=info["metadata"],
                    retrieval_method=info["method"],
                )
            )

        return results
