import os
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

VECTOR_DB_PATH = Path(__file__).parent.parent / "vector_db"
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)


class VectorStore:
    """Manages ChromaDB + FAISS vector storage for NBA documents."""

    def __init__(self, collection_name: str = "nba_documents"):
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.faiss_index = None
        self.faiss_metadata: List[Dict] = []
        self._chroma_ready = False
        self._faiss_ready = False
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB and FAISS."""
        self._init_chromadb()
        self._init_faiss()

    def _init_chromadb(self):
        """Initialize ChromaDB persistent client."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.chroma_client = chromadb.PersistentClient(
                path=str(VECTOR_DB_PATH / "chroma"),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._chroma_ready = True
            logger.info(f"ChromaDB initialized. Collection: {self.collection_name}")
        except ImportError:
            logger.error("chromadb not installed.")
            self._chroma_ready = False
        except Exception as e:
            logger.error(f"ChromaDB init error: {e}")
            self._chroma_ready = False

    def _init_faiss(self):
        """Initialize FAISS index."""
        try:
            import faiss

            faiss_path = VECTOR_DB_PATH / "faiss.index"
            meta_path = VECTOR_DB_PATH / "faiss_meta.npy"

            if faiss_path.exists() and meta_path.exists():
                self.faiss_index = faiss.read_index(str(faiss_path))
                self.faiss_metadata = list(np.load(str(meta_path), allow_pickle=True))
                logger.info(f"FAISS loaded: {self.faiss_index.ntotal} vectors")
            else:
                self.faiss_index = faiss.IndexFlatIP(384)  # all-MiniLM-L6-v2 dim
                self.faiss_metadata = []

            self._faiss_ready = True
        except ImportError:
            logger.error("faiss-cpu not installed.")
            self._faiss_ready = False
        except Exception as e:
            logger.error(f"FAISS init error: {e}")
            self._faiss_ready = False

    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> bool:
        """Add documents to both ChromaDB and FAISS."""
        if not texts:
            return False

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]

        success = True

        # ChromaDB
        if self._chroma_ready:
            try:
                self.collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
            except Exception as e:
                logger.error(f"ChromaDB add error: {e}")
                success = False

        # FAISS
        if self._faiss_ready:
            try:
                import faiss
                import numpy as np

                vecs = np.array(embeddings, dtype=np.float32)
                faiss.normalize_L2(vecs)
                self.faiss_index.add(vecs)
                self.faiss_metadata.extend(
                    [{"id": i, "text": t, "meta": m} for i, t, m in zip(ids, texts, metadatas)]
                )
                self._save_faiss()
            except Exception as e:
                logger.error(f"FAISS add error: {e}")
                success = False

        return success

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        results = []

        if self._chroma_ready:
            try:
                where = None
                if source_filter:
                    where = {"source": source_filter}

                query_result = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, max(1, self.collection.count())),
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )

                if query_result["documents"]:
                    for doc, meta, dist in zip(
                        query_result["documents"][0],
                        query_result["metadatas"][0],
                        query_result["distances"][0],
                    ):
                        results.append({
                            "text": doc,
                            "metadata": meta,
                            "score": 1 - dist,  # Convert cosine distance to similarity
                            "source": meta.get("source", "Unknown"),
                        })
            except Exception as e:
                logger.error(f"ChromaDB search error: {e}")

        return results

    def _save_faiss(self):
        """Persist FAISS index to disk."""
        try:
            import faiss
            import numpy as np

            faiss_path = VECTOR_DB_PATH / "faiss.index"
            meta_path = VECTOR_DB_PATH / "faiss_meta.npy"
            faiss.write_index(self.faiss_index, str(faiss_path))
            np.save(str(meta_path), np.array(self.faiss_metadata, dtype=object))
        except Exception as e:
            logger.error(f"FAISS save error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Return vector store statistics."""
        chroma_count = 0
        if self._chroma_ready and self.collection:
            try:
                chroma_count = self.collection.count()
            except Exception:
                pass

        faiss_count = self.faiss_index.ntotal if self._faiss_ready and self.faiss_index else 0

        return {
            "chroma_ready": self._chroma_ready,
            "faiss_ready": self._faiss_ready,
            "chroma_count": chroma_count,
            "faiss_count": faiss_count,
            "total_vectors": chroma_count,
        }

    def delete_collection(self) -> bool:
        """Clear the entire collection."""
        try:
            if self._chroma_ready:
                self.chroma_client.delete_collection(self.collection_name)
                self._init_chromadb()

            if self._faiss_ready:
                import faiss
                self.faiss_index = faiss.IndexFlatIP(384)
                self.faiss_metadata = []
                self._save_faiss()
            return True
        except Exception as e:
            logger.error(f"Delete collection error: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        return self._chroma_ready or self._faiss_ready


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
