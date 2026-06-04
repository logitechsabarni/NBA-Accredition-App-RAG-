

from typing import List, Dict, Any
import math


class Reranker:
    """
    Simple production-ready reranker for retrieved documents.
    Combines semantic score + keyword overlap + recency bias.
    """

    def __init__(self, weight_semantic: float = 0.6, weight_keyword: float = 0.3, weight_recency: float = 0.1):
        self.weight_semantic = weight_semantic
        self.weight_keyword = weight_keyword
        self.weight_recency = weight_recency

    def _keyword_score(self, query: str, text: str) -> float:
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())

        if not query_tokens:
            return 0.0

        overlap = len(query_tokens.intersection(text_tokens))
        return overlap / len(query_tokens)

    def _recency_score(self, metadata: Dict[str, Any]) -> float:
        """
        Expects metadata to optionally contain:
        - 'timestamp' or 'recency_score'
        """
        if not metadata:
            return 0.5

        if "recency_score" in metadata:
            return float(metadata["recency_score"])

        return 0.5

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank retrieved documents using weighted scoring.
        """

        scored_results = []

        for item in results:
            text = item.get("text", "")
            metadata = item.get("metadata", {})
            semantic_score = float(item.get("score", 0.0))

            keyword_score = self._keyword_score(query, text)
            recency_score = self._recency_score(metadata)

            final_score = (
                self.weight_semantic * semantic_score +
                self.weight_keyword * keyword_score +
                self.weight_recency * recency_score
            )

            item["final_score"] = final_score
            scored_results.append(item)

        scored_results.sort(key=lambda x: x["final_score"], reverse=True)

        return scored_results[:top_k]