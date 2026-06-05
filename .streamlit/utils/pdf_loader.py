import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import io

logger = logging.getLogger(__name__)


def load_pdf(file_input) -> Dict[str, Any]:
    """
    Load and extract text from a PDF.

    Args:
        file_input: File path (str/Path) or bytes-like object.

    Returns:
        Dict with 'text', 'pages', 'page_texts', 'metadata'.
    """
    all_text = []
    page_texts = []
    num_pages = 0

    try:
        import pdfplumber

        if isinstance(file_input, (str, Path)):
            cm = pdfplumber.open(file_input)
        else:
            if hasattr(file_input, "read"):
                data = file_input.read()
            else:
                data = file_input
            cm = pdfplumber.open(io.BytesIO(data))

        with cm as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                page_texts.append(text)
                all_text.append(text)

    except ImportError:
        logger.warning("pdfplumber not available, trying pypdf.")
        try:
            from pypdf import PdfReader

            if isinstance(file_input, (str, Path)):
                reader = PdfReader(file_input)
            else:
                if hasattr(file_input, "read"):
                    data = file_input.read()
                else:
                    data = file_input
                reader = PdfReader(io.BytesIO(data))

            num_pages = len(reader.pages)
            for page in reader.pages:
                text = page.extract_text() or ""
                page_texts.append(text)
                all_text.append(text)
        except ImportError:
            logger.error("Neither pdfplumber nor pypdf is installed.")
            raise RuntimeError("PDF parsing library not available.")
    except Exception as e:
        logger.error(f"PDF loading error: {e}")
        raise

    full_text = "\n\n".join(all_text)
    return {
        "text": full_text,
        "pages": num_pages,
        "page_texts": page_texts,
        "metadata": {
            "num_pages": num_pages,
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
        },
    }


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    source: str = "",
    page_num: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text.
        chunk_size: Target chunk size in characters.
        overlap: Overlap between consecutive chunks.
        source: Source document name.
        page_num: Optional page number.

    Returns:
        List of chunk dicts with 'text' and 'metadata'.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            boundary = max(last_period, last_newline)
            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk_text_content = text[start:end].strip()
        if chunk_text_content:
            chunks.append({
                "text": chunk_text_content,
                "metadata": {
                    "source": source,
                    "chunk_index": chunk_idx,
                    "start_char": start,
                    "end_char": end,
                    "page": page_num,
                    "char_count": len(chunk_text_content),
                },
            })
            chunk_idx += 1

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def process_pdf_document(
    file_input,
    source_name: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> Dict[str, Any]:
    """
    Full pipeline: load PDF → extract text → chunk.

    Returns:
        Dict with 'pages', 'chunks', 'metadata'.
    """
    pdf_data = load_pdf(file_input)
    all_chunks = []

    for page_idx, page_text in enumerate(pdf_data["page_texts"]):
        page_chunks = chunk_text(
            text=page_text,
            chunk_size=chunk_size,
            overlap=overlap,
            source=source_name,
            page_num=page_idx + 1,
        )
        all_chunks.extend(page_chunks)

    return {
        "pages": pdf_data["pages"],
        "chunks": all_chunks,
        "metadata": pdf_data["metadata"],
        "source": source_name,
    }
