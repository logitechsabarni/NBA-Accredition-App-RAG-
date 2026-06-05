import logging
from typing import List, Dict, Any, Optional, Generator
from utils.watsonx_client import get_watsonx_client
from utils.vector_store import get_vector_store
from utils.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

NBA_SYSTEM_PROMPT = """You are an expert NBA (National Board of Accreditation) consultant AI assistant for Indian engineering colleges.

You have deep expertise in:
- NBA Accreditation processes (Tier I and Tier II institutions)
- Outcome-Based Education (OBE) framework
- Course Outcomes (COs) and Program Outcomes (POs) mapping
- CO and PO Attainment calculation methods
- Self Assessment Report (SAR) preparation
- Continuous Quality Improvement (CQI) processes
- NBA criteria and their assessment
- Bloom's Taxonomy levels
- Direct and Indirect Assessment methods
- Program Educational Objectives (PEOs)
- Graduate Attributes

Always provide accurate, actionable, and specific guidance for NBA accreditation.
Cite the relevant context provided when answering questions.
If information is not in the context, state that clearly and provide general NBA guidance.

Format responses clearly with headings, bullet points, and specific examples where appropriate.
"""


class RAGEngine:
    """Retrieval Augmented Generation engine for NBA knowledge base."""

    def __init__(
        self,
        top_k: int = 5,
        temperature: float = 0.7,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.top_k = top_k
        self.temperature = temperature
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = get_vector_store()
        self.embedder = get_embedding_model()
        self.watsonx = get_watsonx_client()

    def retrieve(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks for a query."""
        if not self.embedder.is_ready:
            logger.warning("Embedding model not ready.")
            return []

        k = top_k or self.top_k
        query_emb = self.embedder.embed_single(query)
        results = self.vector_store.search(query_emb, top_k=k)
        return results

    def build_context(self, results: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved results."""
        if not results:
            return ""

        context_parts = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "Unknown")
            page = r.get("metadata", {}).get("page", "")
            page_str = f" (Page {page})" if page else ""
            context_parts.append(
                f"[Source {i}: {source}{page_str}]\n{r['text']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def format_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Format source citations."""
        seen = set()
        sources = []
        for r in results:
            source = r.get("source", "Unknown")
            page = r.get("metadata", {}).get("page", "")
            score = r.get("score", 0)
            key = f"{source}-{page}"
            if key not in seen:
                seen.add(key)
                page_str = f", Page {page}" if page else ""
                sources.append(f"📄 {source}{page_str} (relevance: {score:.2f})")
        return sources

    def generate(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None,
        use_rag: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate an AI response with optional RAG context.

        Returns:
            Dict with 'response', 'sources', 'context_used', 'query'.
        """
        sources = []
        context = ""

        if use_rag and self.vector_store.is_ready:
            results = self.retrieve(query)
            if results:
                context = self.build_context(results)
                sources = self.format_sources(results)

        # Build prompt
        history_text = ""
        if chat_history:
            for msg in chat_history[-6:]:  # Last 3 exchanges
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"\n{role.capitalize()}: {content}"

        if context:
            prompt = f"""Based on the following NBA documentation context, answer the question.

CONTEXT:
{context}

CHAT HISTORY:{history_text if history_text else " None"}

QUESTION: {query}

ANSWER:"""
        else:
            prompt = f"""CHAT HISTORY:{history_text if history_text else " None"}

QUESTION: {query}

ANSWER:"""

        try:
            response = self.watsonx.generate_response(
                prompt=prompt,
                max_tokens=1024,
                temperature=self.temperature,
                top_k=self.top_k,
                system_prompt=NBA_SYSTEM_PROMPT,
            )
        except Exception as e:
            response = f"⚠️ AI generation failed: {str(e)}\n\nPlease ensure IBM Watsonx credentials are configured in Settings."

        return {
            "response": response,
            "sources": sources,
            "context_used": bool(context),
            "query": query,
            "chunks_retrieved": len(sources),
        }

    def ingest_document(
        self,
        chunks: List[Dict[str, Any]],
        source_name: str,
    ) -> Dict[str, Any]:
        """Ingest document chunks into the vector store."""
        if not self.embedder.is_ready:
            return {"success": False, "error": "Embedding model not available.", "count": 0}

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        try:
            embeddings = self.embedder.embed(texts)
            success = self.vector_store.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            return {
                "success": success,
                "count": len(chunks),
                "source": source_name,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Ingestion error for {source_name}: {e}")
            return {"success": False, "error": str(e), "count": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Return RAG system statistics."""
        vs_stats = self.vector_store.get_stats()
        return {
            "rag_ready": self.vector_store.is_ready and self.embedder.is_ready,
            "vector_store": vs_stats,
            "embedding_model": self.embedder.model_name,
            "embedding_ready": self.embedder.is_ready,
            "top_k": self.top_k,
            "temperature": self.temperature,
        }


_rag_engine: Optional[RAGEngine] = None


def get_rag_engine(**kwargs) -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(**kwargs)
    else:
        # Update params if provided
        for k, v in kwargs.items():
            if hasattr(_rag_engine, k):
                setattr(_rag_engine, k, v)
    return _rag_engine
