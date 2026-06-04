"""
RAG Ingestion Pipeline
End-to-end document ingestion: parse → chunk → embed → store.
Supports PDF, plain text, JSON, and HTML input formats.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.rag.chunking import ChunkConfig, ChunkStrategy, TextChunker
from backend.rag.embedder import Embedder, EmbeddingModel, EmbeddingRequest
from backend.rag.retriever import Retriever
from backend.rag.vector_store import BaseVectorStore, VectorDocument

logger = logging.getLogger(__name__)


class DocumentFormat(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class IngestionDocument(BaseModel):
    content: str
    format: DocumentFormat = DocumentFormat.TEXT
    source: str = ""
    doc_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionConfig(BaseModel):
    chunk_config: ChunkConfig = Field(default_factory=ChunkConfig)
    embedding_model: EmbeddingModel = EmbeddingModel.OPENAI_SMALL
    batch_size: int = Field(default=50, ge=1, le=500)
    update_sparse_index: bool = True
    dedup_enabled: bool = True


class IngestionResult(BaseModel):
    document_id: str
    chunks_created: int
    vectors_stored: int
    tokens_used: int
    latency_ms: float
    source: str
    deduplicated: bool = False


class BatchIngestionResult(BaseModel):
    results: list[IngestionResult]
    total_chunks: int
    total_tokens: int
    total_latency_ms: float
    failed_count: int


class IngestionPipeline:
    """
    Full-cycle ingestion pipeline:
      1. Parse raw content by format
      2. Chunk using configured strategy
      3. Embed in batches
      4. Upsert to vector store
      5. Optionally update BM25 sparse index
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: Embedder,
        retriever: Retriever | None = None,
        config: IngestionConfig | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._retriever = retriever
        self._config = config or IngestionConfig()
        self._chunker = TextChunker(self._config.chunk_config)
        self._seen_hashes: set[str] = set()

        logger.info(
            "IngestionPipeline initialised",
            extra={
                "chunk_strategy": self._config.chunk_config.strategy,
                "batch_size": self._config.batch_size,
            },
        )

    async def ingest(self, document: IngestionDocument) -> IngestionResult:
        """Ingest a single document through the full pipeline."""
        start = time.monotonic()
        doc_id = document.doc_id or self._generate_id(document.content)

        if self._config.dedup_enabled:
            content_hash = self._hash(document.content)
            if content_hash in self._seen_hashes:
                logger.info(
                    "Duplicate document skipped",
                    extra={"doc_id": doc_id},
                )
                return IngestionResult(
                    document_id=doc_id,
                    chunks_created=0,
                    vectors_stored=0,
                    tokens_used=0,
                    latency_ms=0.0,
                    source=document.source,
                    deduplicated=True,
                )
            self._seen_hashes.add(content_hash)

        # 1. Parse
        clean_text = self._parse(document)

        # 2. Chunk
        chunk_result = self._chunker.chunk(
            clean_text,
            metadata={
                "doc_id": doc_id,
                "source": document.source,
                **document.metadata,
            },
        )

        if not chunk_result.chunks:
            logger.warning("No chunks produced", extra={"doc_id": doc_id})
            return IngestionResult(
                document_id=doc_id,
                chunks_created=0,
                vectors_stored=0,
                tokens_used=0,
                latency_ms=(time.monotonic() - start) * 1000,
                source=document.source,
            )

        # 3. Embed in batches
        chunk_texts = [c.text for c in chunk_result.chunks]
        embedding_req = EmbeddingRequest(
            texts=chunk_texts,
            model=self._config.embedding_model,
            batch_size=self._config.batch_size,
        )
        embedding_result = await self._embedder.embed(embedding_req)

        # 4. Build VectorDocuments
        vector_docs: list[VectorDocument] = []
        for chunk, emb in zip(chunk_result.chunks, embedding_result.embeddings):
            vector_docs.append(
                VectorDocument(
                    id=f"{doc_id}::chunk::{chunk.index}",
                    text=chunk.text,
                    embedding=emb,
                    metadata=chunk.metadata,
                )
            )

        # 5. Store
        stored_ids = await self._vector_store.add_documents(vector_docs)

        # 6. Update sparse index
        if self._config.update_sparse_index and self._retriever is not None:
            await self._retriever.add_to_sparse_index(vector_docs)

        latency_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Document ingested",
            extra={
                "doc_id": doc_id,
                "chunks": len(chunk_result.chunks),
                "tokens": embedding_result.tokens_used,
                "latency_ms": round(latency_ms, 2),
            },
        )

        return IngestionResult(
            document_id=doc_id,
            chunks_created=len(chunk_result.chunks),
            vectors_stored=len(stored_ids),
            tokens_used=embedding_result.tokens_used,
            latency_ms=round(latency_ms, 2),
            source=document.source,
        )

    async def ingest_batch(
        self, documents: list[IngestionDocument]
    ) -> BatchIngestionResult:
        """Ingest multiple documents concurrently with a semaphore."""
        sem = asyncio.Semaphore(8)
        start = time.monotonic()

        async def _guarded(doc: IngestionDocument) -> IngestionResult | Exception:
            async with sem:
                try:
                    return await self.ingest(doc)
                except Exception as exc:
                    logger.error(
                        "Ingestion failed",
                        extra={"source": doc.source, "error": str(exc)},
                    )
                    return exc

        tasks = [asyncio.create_task(_guarded(doc)) for doc in documents]
        raw_results = await asyncio.gather(*tasks)

        results: list[IngestionResult] = []
        failed = 0
        for r in raw_results:
            if isinstance(r, Exception):
                failed += 1
            else:
                results.append(r)

        total_latency_ms = (time.monotonic() - start) * 1000

        return BatchIngestionResult(
            results=results,
            total_chunks=sum(r.chunks_created for r in results),
            total_tokens=sum(r.tokens_used for r in results),
            total_latency_ms=round(total_latency_ms, 2),
            failed_count=failed,
        )

    async def ingest_file(self, path: str | Path) -> IngestionResult:
        """Convenience wrapper to ingest from a file path."""
        p = Path(path)
        suffix = p.suffix.lower()
        fmt_map = {
            ".txt": DocumentFormat.TEXT,
            ".md": DocumentFormat.MARKDOWN,
            ".pdf": DocumentFormat.PDF,
            ".html": DocumentFormat.HTML,
            ".htm": DocumentFormat.HTML,
            ".json": DocumentFormat.JSON,
        }
        fmt = fmt_map.get(suffix, DocumentFormat.TEXT)

        if fmt == DocumentFormat.PDF:
            content = await self._read_pdf(p)
        else:
            content = p.read_text(encoding="utf-8", errors="replace")

        doc = IngestionDocument(
            content=content,
            format=fmt,
            source=str(p),
            metadata={"filename": p.name},
        )
        return await self.ingest(doc)

    def _parse(self, document: IngestionDocument) -> str:
        """Format-specific text extraction."""
        match document.format:
            case DocumentFormat.HTML:
                return self._strip_html(document.content)
            case DocumentFormat.JSON:
                return self._flatten_json(document.content)
            case DocumentFormat.MARKDOWN:
                return self._strip_markdown(document.content)
            case _:
                return document.content

    @staticmethod
    def _strip_html(html: str) -> str:
        import re
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _flatten_json(json_str: str) -> str:
        import json

        try:
            obj = json.loads(json_str)
        except Exception:
            return json_str

        def _extract(o: Any) -> list[str]:
            if isinstance(o, str):
                return [o]
            if isinstance(o, dict):
                parts: list[str] = []
                for k, v in o.items():
                    parts.append(str(k))
                    parts.extend(_extract(v))
                return parts
            if isinstance(o, list):
                return [t for item in o for t in _extract(item)]
            return [str(o)]

        return " ".join(_extract(obj))

    @staticmethod
    def _strip_markdown(md: str) -> str:
        import re
        md = re.sub(r"!\[.*?\]\(.*?\)", "", md)
        md = re.sub(r"\[.*?\]\(.*?\)", lambda m: m.group(0).split("](")[0].lstrip("["), md)
        md = re.sub(r"`{1,3}[^`]*`{1,3}", " ", md, flags=re.DOTALL)
        md = re.sub(r"^#{1,6}\s+", "", md, flags=re.MULTILINE)
        md = re.sub(r"[*_~]{1,3}", "", md)
        md = re.sub(r"\s+", " ", md)
        return md.strip()

    @staticmethod
    async def _read_pdf(path: Path) -> str:
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            raise RuntimeError(
                "pypdf is required for PDF ingestion: pip install pypdf"
            )

    @staticmethod
    def _generate_id(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
