"""
RAG retriever — semantic search with re-ranking and filtering.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class NBARetriever:
    """
    Advanced retriever for NBA knowledge base with optional re-ranking.
    """

    def __init__(self, top_k: int = 5, score_threshold: float = 0.25):
        self.top_k = top_k
        self.score_threshold = score_threshold
        self._vector_store = None
        self._embedder = None

    def _get_deps(self):
        if self._vector_store is None:
            from utils.vector_store import get_vector_store
            self._vector_store = get_vector_store()
        if self._embedder is None:
            from utils.embeddings import get_embedding_model
            self._embedder = get_embedding_model()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Natural language query.
            top_k: Number of results (overrides default).
            source_filter: Restrict to a specific document source.
            min_score: Minimum cosine similarity threshold.

        Returns:
            List of result dicts: {text, metadata, score, source}.
        """
        self._get_deps()
        k = top_k or self.top_k
        threshold = min_score if min_score is not None else self.score_threshold

        if not self._embedder.is_ready:
            logger.warning("Embedding model not available.")
            return []

        query_emb = self._embedder.embed_single(query)
        results = self._vector_store.search(query_emb, top_k=k, source_filter=source_filter)
        filtered = [r for r in results if r.get("score", 0) >= threshold]
        return filtered

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        window: int = 0,
    ) -> str:
        """
        Retrieve and format context string.

        Args:
            query: Search query.
            top_k: Number of chunks.
            window: Not implemented yet (future: surrounding context).

        Returns:
            Formatted context string.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        parts = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "Unknown")
            page = r.get("metadata", {}).get("page", "")
            page_str = f" (Page {page})" if page else ""
            parts.append(f"[Context {i} — {source}{page_str}]\n{r['text']}")

        return "\n\n---\n\n".join(parts)

    def mmr_retrieve(
        self,
        query: str,
        top_k: int = 5,
        lambda_mult: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Maximal Marginal Relevance (MMR) retrieval for diversity.
        Reduces redundancy in retrieved chunks.

        Args:
            query: Search query.
            top_k: Final number of results.
            lambda_mult: Relevance vs diversity trade-off (1=pure relevance, 0=pure diversity).

        Returns:
            Diverse list of results.
        """
        import numpy as np

        self._get_deps()
        # Retrieve more candidates first
        candidates = self.retrieve(query, top_k=top_k * 3)
        if len(candidates) <= top_k:
            return candidates

        # Get embeddings for candidates
        candidate_texts = [c["text"] for c in candidates]
        candidate_embs = self._embedder.embed(candidate_texts)

        query_emb = self._embedder.embed_single(query)
        query_arr = np.array(query_emb)

        selected_indices = []
        remaining = list(range(len(candidates)))

        for _ in range(min(top_k, len(candidates))):
            if not remaining:
                break

            if not selected_indices:
                # First: pick highest relevance
                scores = [np.dot(query_arr, candidate_embs[i]) for i in remaining]
                best = remaining[int(np.argmax(scores))]
            else:
                # MMR score: lambda * relevance - (1-lambda) * max_similarity_to_selected
                scores = []
                for i in remaining:
                    relevance = np.dot(query_arr, candidate_embs[i])
                    sim_to_selected = max(
                        np.dot(candidate_embs[i], candidate_embs[j]) for j in selected_indices
                    )
                    mmr = lambda_mult * relevance - (1 - lambda_mult) * sim_to_selected
                    scores.append(mmr)
                best = remaining[int(np.argmax(scores))]

            selected_indices.append(best)
            remaining.remove(best)

        return [candidates[i] for i in selected_indices]

    def get_stats(self) -> Dict[str, Any]:
        self._get_deps()
        return {
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "embedding_ready": self._embedder.is_ready if self._embedder else False,
            "vector_store_ready": self._vector_store.is_ready if self._vector_store else False,
        }


_retriever: Optional[NBARetriever] = None


def get_retriever(top_k: int = 5) -> NBARetriever:
    global _retriever
    if _retriever is None:
        _retriever = NBARetriever(top_k=top_k)
    return _retriever
