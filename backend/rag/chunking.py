"""
Chunking strategies for RAG document ingestion.
Supports fixed-size, sentence-aware, and semantic chunking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChunkStrategy(str, Enum):
    FIXED = "fixed"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    RECURSIVE = "recursive"


@dataclass
class Chunk:
    content: str
    index: int
    source_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    char_start: int = 0
    char_end: int = 0

    @property
    def token_estimate(self) -> int:
        return max(1, len(self.content) // 4)


class FixedChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, source_id: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append(
                    Chunk(
                        content=content,
                        index=idx,
                        source_id=source_id,
                        metadata=metadata or {},
                        char_start=start,
                        char_end=end,
                    )
                )
                idx += 1
            start += self.chunk_size - self.overlap
        return chunks


class SentenceChunker:
    def __init__(self, max_sentences: int = 5, overlap_sentences: int = 1) -> None:
        self.max_sentences = max_sentences
        self.overlap_sentences = overlap_sentences
        self._sentence_pattern = re.compile(r"(?<=[.!?])\s+")

    def chunk(self, text: str, source_id: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        sentences = self._sentence_pattern.split(text.strip())
        chunks: list[Chunk] = []
        idx = 0
        pos = 0
        i = 0
        while i < len(sentences):
            batch = sentences[i: i + self.max_sentences]
            content = " ".join(batch).strip()
            char_start = text.find(batch[0], pos)
            char_end = char_start + len(content)
            if content:
                chunks.append(
                    Chunk(
                        content=content,
                        index=idx,
                        source_id=source_id,
                        metadata=metadata or {},
                        char_start=char_start,
                        char_end=char_end,
                    )
                )
                idx += 1
                pos = char_end
            i += self.max_sentences - self.overlap_sentences
        return chunks


class ParagraphChunker:
    def __init__(self, max_chars: int = 1024) -> None:
        self.max_chars = max_chars

    def chunk(self, text: str, source_id: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        raw_paragraphs = re.split(r"\n{2,}", text.strip())
        chunks: list[Chunk] = []
        idx = 0
        buffer = ""
        buf_start = 0
        current_pos = 0

        for para in raw_paragraphs:
            if len(buffer) + len(para) > self.max_chars and buffer:
                chunks.append(
                    Chunk(
                        content=buffer.strip(),
                        index=idx,
                        source_id=source_id,
                        metadata=metadata or {},
                        char_start=buf_start,
                        char_end=buf_start + len(buffer),
                    )
                )
                idx += 1
                buffer = ""
                buf_start = current_pos

            if not buffer:
                buf_start = current_pos
            buffer += para + "\n\n"
            current_pos += len(para) + 2

        if buffer.strip():
            chunks.append(
                Chunk(
                    content=buffer.strip(),
                    index=idx,
                    source_id=source_id,
                    metadata=metadata or {},
                    char_start=buf_start,
                    char_end=buf_start + len(buffer),
                )
            )

        return chunks


class RecursiveChunker:
    """
    Recursively splits on progressively smaller separators.
    Mirrors LangChain's RecursiveCharacterTextSplitter logic.
    """

    _SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, source_id: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        raw_chunks = self._split(text, self._SEPARATORS)
        result: list[Chunk] = []
        for idx, content in enumerate(raw_chunks):
            stripped = content.strip()
            if stripped:
                result.append(
                    Chunk(
                        content=stripped,
                        index=idx,
                        source_id=source_id,
                        metadata=metadata or {},
                    )
                )
        return result

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if not separators or len(text) <= self.chunk_size:
            return [text]

        sep = separators[0]
        parts = text.split(sep) if sep else list(text)
        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > self.chunk_size:
                    chunks.extend(self._split(part, separators[1:]))
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        merged: list[str] = []
        buffer = ""
        for chunk in chunks:
            if buffer and len(buffer) + len(chunk) + 1 <= self.chunk_size:
                buffer += " " + chunk
            else:
                if buffer:
                    merged.append(buffer)
                buffer = chunk
        if buffer:
            merged.append(buffer)

        return merged


def get_chunker(strategy: ChunkStrategy, **kwargs: Any):
    mapping = {
        ChunkStrategy.FIXED: FixedChunker,
        ChunkStrategy.SENTENCE: SentenceChunker,
        ChunkStrategy.PARAGRAPH: ParagraphChunker,
        ChunkStrategy.RECURSIVE: RecursiveChunker,
    }
    cls = mapping[strategy]
    return cls(**kwargs)
