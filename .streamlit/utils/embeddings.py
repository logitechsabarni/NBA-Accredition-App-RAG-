import logging
import numpy as np
from typing import List, Optional
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class EmbeddingModel:
    """Sentence Transformer embeddings for NBA document indexing."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.model = None
        self._ready = False
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self._ready = True
            logger.info(f"Embedding model loaded: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed.")
            self._ready = False
        except Exception as e:
            logger.error(f"Embedding model load error: {e}")
            self._ready = False

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts."""
        if not self._ready:
            raise RuntimeError("Embedding model not available.")
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32,
                normalize_embeddings=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

    def similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Cosine similarity between two embeddings."""
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def dimension(self) -> int:
        return 384  # all-MiniLM-L6-v2 output dimension


_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model(model_name: str = DEFAULT_MODEL) -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None or _embedding_model.model_name != model_name:
        _embedding_model = EmbeddingModel(model_name)
    return _embedding_model
