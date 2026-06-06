"""
End-to-end document processing pipeline for the NBA knowledge base.
Handles PDF loading, chunking, embedding, and vector store ingestion.
"""
import logging
import io
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Full pipeline: PDF → text → chunks → embeddings → vector store.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._embedder = None
        self._vector_store = None

    def _get_deps(self):
        if self._embedder is None:
            from utils.embeddings import get_embedding_model
            self._embedder = get_embedding_model()
        if self._vector_store is None:
            from utils.vector_store import get_vector_store
            self._vector_store = get_vector_store()

    def load_pdf(self, file_input: Union[bytes, str, Path]) -> Dict[str, Any]:
        """Load and extract text from a PDF."""
        from utils.pdf_loader import load_pdf
        return load_pdf(file_input)

    def chunk_document(
        self,
        pdf_data: Dict[str, Any],
        source_name: str,
        strategy: str = "fixed",
    ) -> List[Dict[str, Any]]:
        """Chunk PDF page texts into searchable segments."""
        from rag.chunker import chunk_document

        all_chunks = []
        for page_idx, page_text in enumerate(pdf_data.get("page_texts", [])):
            if not page_text.strip():
                continue
            page_chunks = chunk_document(
                text=page_text,
                strategy=strategy,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
                source=source_name,
                page=page_idx + 1,
            )
            all_chunks.extend(page_chunks)

        return all_chunks

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for all chunks."""
        self._get_deps()
        texts = [c["text"] for c in chunks]
        return self._embedder.embed(texts)

    def ingest(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> bool:
        """Store chunks and embeddings in vector store."""
        self._get_deps()
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        return self._vector_store.add_documents(texts, embeddings, metadatas)

    def process(
        self,
        file_input: Union[bytes, str, Path],
        source_name: str,
        strategy: str = "fixed",
    ) -> Dict[str, Any]:
        """
        Full processing pipeline for a single document.

        Returns:
            Dict with: success, pages, chunks_total, vectors_added, source, error.
        """
        try:
            # 1. Load PDF
            pdf_data = self.load_pdf(file_input)

            # 2. Chunk
            chunks = self.chunk_document(pdf_data, source_name, strategy)
            if not chunks:
                return {
                    "success": False,
                    "error": "No text extracted from PDF.",
                    "pages": 0,
                    "chunks_total": 0,
                    "vectors_added": 0,
                    "source": source_name,
                }

            # 3. Embed
            embeddings = self.embed_chunks(chunks)

            # 4. Ingest
            ok = self.ingest(chunks, embeddings)

            return {
                "success": ok,
                "pages": pdf_data["pages"],
                "chunks_total": len(chunks),
                "vectors_added": len(chunks) if ok else 0,
                "source": source_name,
                "error": None if ok else "Vector store ingestion failed.",
            }

        except Exception as e:
            logger.error(f"Document processing failed for {source_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pages": 0,
                "chunks_total": 0,
                "vectors_added": 0,
                "source": source_name,
            }

    def process_batch(
        self,
        files: List[Dict[str, Any]],
        strategy: str = "fixed",
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents.

        Args:
            files: List of {"content": bytes, "name": str}
            strategy: Chunking strategy.

        Returns:
            List of processing results.
        """
        results = []
        for file_info in files:
            result = self.process(
                file_input=file_info["content"],
                source_name=file_info["name"],
                strategy=strategy,
            )
            results.append(result)
        return results


_processor: Optional[DocumentProcessor] = None


def get_document_processor(chunk_size: int = 1000, chunk_overlap: int = 200) -> DocumentProcessor:
    global _processor
    if _processor is None:
        _processor = DocumentProcessor(chunk_size, chunk_overlap)
    return _processor
