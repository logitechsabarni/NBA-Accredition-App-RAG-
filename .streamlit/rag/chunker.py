"""
Advanced text chunking strategies for NBA documents.
Supports sentence-aware, paragraph-aware, and fixed-size chunking.
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_by_sentences(text: str) -> List[str]:
    """Split text into sentences using simple regex."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_fixed_size(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    source: str = "",
    page: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Fixed-size character chunking with overlap.

    Args:
        text: Input text.
        chunk_size: Target chunk size in characters.
        overlap: Overlap between chunks.
        source: Source document name.
        page: Page number.

    Returns:
        List of chunk dicts.
    """
    text = clean_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try sentence boundary
        if end < len(text):
            for boundary_char in [".", "\n", "!", "?"]:
                last = text.rfind(boundary_char, start + chunk_size // 2, end)
                if last > start:
                    end = last + 1
                    break

        chunk = text[start:end].strip()
        if len(chunk) > 50:  # Ignore very short chunks
            chunks.append({
                "text": chunk,
                "metadata": {
                    "source": source,
                    "page": page,
                    "chunk_index": idx,
                    "start_char": start,
                    "end_char": end,
                    "strategy": "fixed_size",
                    "char_count": len(chunk),
                },
            })
            idx += 1

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def chunk_by_paragraph(
    text: str,
    max_chunk_size: int = 1500,
    source: str = "",
    page: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Paragraph-aware chunking. Keeps paragraphs together when possible.

    Args:
        text: Input text.
        max_chunk_size: Maximum size per chunk.
        source: Source name.
        page: Page number.

    Returns:
        List of chunk dicts.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    chunks = []
    current = ""
    idx = 0

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append({
                    "text": current,
                    "metadata": {
                        "source": source,
                        "page": page,
                        "chunk_index": idx,
                        "strategy": "paragraph",
                        "char_count": len(current),
                    },
                })
                idx += 1
            # If single paragraph > max_chunk_size, fall back to fixed chunking
            if len(para) > max_chunk_size:
                sub_chunks = chunk_fixed_size(para, max_chunk_size, 100, source, page)
                for sc in sub_chunks:
                    sc["metadata"]["chunk_index"] = idx
                    chunks.append(sc)
                    idx += 1
                current = ""
            else:
                current = para

    if current:
        chunks.append({
            "text": current,
            "metadata": {
                "source": source,
                "page": page,
                "chunk_index": idx,
                "strategy": "paragraph",
                "char_count": len(current),
            },
        })

    return chunks


def chunk_document(
    text: str,
    strategy: str = "fixed",
    chunk_size: int = 1000,
    overlap: int = 200,
    source: str = "",
    page: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Unified chunking interface.

    Args:
        text: Input text.
        strategy: 'fixed' | 'paragraph'
        chunk_size: Target chunk size.
        overlap: Overlap (for fixed strategy).
        source: Document source name.
        page: Page number.

    Returns:
        List of chunk dicts.
    """
    if strategy == "paragraph":
        return chunk_by_paragraph(text, max_chunk_size=chunk_size, source=source, page=page)
    return chunk_fixed_size(text, chunk_size=chunk_size, overlap=overlap, source=source, page=page)
