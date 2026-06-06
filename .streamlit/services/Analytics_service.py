"""
Analytics service — aggregates platform metrics, usage stats, and attainment data.
"""
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Aggregates and serves platform-wide analytics."""

    def get_platform_summary(self, session_state) -> Dict[str, Any]:
        """Return key platform metrics from session state."""
        from utils.vector_store import get_vector_store
        from utils.rag_engine import get_rag_engine

        vs_stats = get_vector_store().get_stats()
        rag_stats = get_rag_engine().get_stats()

        return {
            "documents_indexed": len(session_state.get("documents", [])),
            "total_chunks": session_state.get("total_chunks", 0),
            "vector_count": vs_stats.get("chroma_count", 0),
            "ai_queries": session_state.get("ai_queries", 0),
            "workflow_runs": len(session_state.get("workflow_runs", [])),
            "watsonx_connected": session_state.get("watsonx_connected", False),
            "rag_ready": rag_stats.get("rag_ready", False),
            "chat_messages": len(session_state.get("chat_history", [])),
        }

    def generate_usage_time_series(
        self, days: int = 30, seed: int = 42
    ) -> Dict[str, Any]:
        """Generate synthetic usage time series data."""
        np.random.seed(seed)
        dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
        labels = [d.strftime("%b %d") for d in dates]
        queries = [max(0, int(np.random.normal(15, 5))) for _ in range(days)]
        docs = [max(0, int(np.random.normal(2, 1))) for _ in range(days)]
        latencies = [int(np.random.normal(850, 200)) for _ in range(days)]

        return {
            "labels": labels,
            "queries": queries,
            "documents": docs,
            "latencies": latencies,
            "total_queries": sum(queries),
            "total_documents": sum(docs),
            "avg_latency": round(sum(latencies) / len(latencies)),
            "peak_queries": max(queries),
        }

    def get_query_type_distribution(self) -> Dict[str, int]:
        """Return query type breakdown (from logs if available)."""
        from utils.helpers import load_query_logs
        logs = load_query_logs()
        if logs:
            # Count by source or keyword-based heuristics
            distribution = {
                "CO-PO Mapping": 0,
                "Attainment": 0,
                "SAR Guidance": 0,
                "Compliance": 0,
                "General NBA": 0,
            }
            for log in logs:
                q = log.get("query", "").lower()
                if any(k in q for k in ["co-po", "mapping", "co1", "po1"]):
                    distribution["CO-PO Mapping"] += 1
                elif any(k in q for k in ["attainment", "calculate", "score"]):
                    distribution["Attainment"] += 1
                elif any(k in q for k in ["sar", "report", "section"]):
                    distribution["SAR Guidance"] += 1
                elif any(k in q for k in ["compliance", "criteria", "criterion"]):
                    distribution["Compliance"] += 1
                else:
                    distribution["General NBA"] += 1
            # Only return non-zero
            return {k: v for k, v in distribution.items() if v > 0} or {"General NBA": 1}
        # Default synthetic
        return {
            "CO-PO Mapping": 32,
            "Attainment": 28,
            "SAR Guidance": 19,
            "Compliance": 12,
            "General NBA": 9,
        }

    def get_attainment_trends(
        self, cos: List[str], years: int = 4, seed: int = 10
    ) -> Dict[str, List[float]]:
        """Generate multi-year attainment trends."""
        np.random.seed(seed)
        trends = {}
        year_labels = [f"{2025 - years + i}-{str(2026 - years + i)[-2:]}" for i in range(years)]
        for co in cos:
            base = np.random.uniform(52, 70)
            vals = []
            for i in range(years):
                base = min(base + np.random.uniform(0, 5), 95)
                vals.append(round(base, 1))
            trends[co] = vals
        trends["_years"] = year_labels
        return trends

    def get_department_rankings(self) -> List[Dict[str, Any]]:
        """Return department rankings by readiness score."""
        from utils.helpers import department_benchmarks
        benchmarks = department_benchmarks()
        ranked = sorted(benchmarks.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "rank": i + 1,
                "department": name,
                "score": score,
                "status": "Ready" if score >= 60 else "In Progress",
                "tier": "Tier-I" if score >= 70 else "Tier-II",
            }
            for i, (name, score) in enumerate(ranked)
        ]


_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
