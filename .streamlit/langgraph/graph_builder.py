"""
LangGraph graph construction for NBA AI pipeline.
Builds a compiled StateGraph with all nodes and routing logic.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_graph = None


def build_nba_graph():
    """
    Build and compile the NBA AI LangGraph pipeline.

    Pipeline:
        intent_classification
            ↓ (route_after_intent)
        [copo_agent] (conditional)
            ↓
        validation
            ↓ (route_after_validation)
        [rag_retrieval] (conditional)
            ↓
        watsonx_generation
            ↓
        response_formatting
            ↓
        END
    """
    try:
        from langgraph.graph import StateGraph, END
        from langgraph.state import AgentState
        from langgraph.nodes import (
            intent_classification_node,
            copo_agent_node,
            validation_node,
            rag_retrieval_node,
            watsonx_generation_node,
            response_formatting_node,
        )
        from langgraph.router import (
            route_after_intent,
            route_after_validation,
        )

        graph = StateGraph(AgentState)

        # Register nodes
        graph.add_node("intent_classification", intent_classification_node)
        graph.add_node("copo_agent", copo_agent_node)
        graph.add_node("validation", validation_node)
        graph.add_node("rag_retrieval", rag_retrieval_node)
        graph.add_node("watsonx_generation", watsonx_generation_node)
        graph.add_node("response_formatting", response_formatting_node)

        # Entry point
        graph.set_entry_point("intent_classification")

        # Conditional routing after intent
        graph.add_conditional_edges(
            "intent_classification",
            route_after_intent,
            {
                "copo_agent": "copo_agent",
                "validation": "validation",
            },
        )

        # CO-PO agent → validation
        graph.add_edge("copo_agent", "validation")

        # Conditional routing after validation
        graph.add_conditional_edges(
            "validation",
            route_after_validation,
            {
                "rag_retrieval": "rag_retrieval",
                "watsonx_generation": "watsonx_generation",
            },
        )

        # RAG → generation
        graph.add_edge("rag_retrieval", "watsonx_generation")

        # Generation → formatting
        graph.add_edge("watsonx_generation", "response_formatting")

        # End
        graph.add_edge("response_formatting", END)

        compiled = graph.compile()
        logger.info("NBA LangGraph pipeline compiled successfully.")
        return compiled

    except ImportError as e:
        logger.warning(f"LangGraph not available ({e}). Using fallback pipeline.")
        return None
    except Exception as e:
        logger.error(f"Graph build error: {e}")
        return None


def get_graph():
    """Get or build the compiled graph (singleton)."""
    global _graph
    if _graph is None:
        _graph = build_nba_graph()
    return _graph


def run_pipeline(user_query: str, chat_history=None, session_id: str = "default"):
    """
    Execute the full NBA AI pipeline for a given query.

    Falls back to direct RAG + Watsonx if LangGraph unavailable.
    """
    from langgraph.state import create_initial_state

    state = create_initial_state(user_query, chat_history, session_id)
    graph = get_graph()

    if graph is not None:
        try:
            final_state = graph.invoke(state)
            return {
                "response": final_state["final_response"],
                "sources": final_state["source_citations"],
                "intent": final_state["intent"],
                "nodes_executed": final_state["nodes_executed"],
                "total_latency_ms": final_state["total_latency_ms"],
                "context_used": bool(final_state["context_text"]),
            }
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")

    # Fallback: direct RAG + Watsonx
    from utils.rag_engine import get_rag_engine
    rag = get_rag_engine()
    result = rag.generate(user_query, chat_history=chat_history, use_rag=True)
    return {
        "response": result["response"],
        "sources": result.get("sources", []),
        "intent": "general_nba",
        "nodes_executed": ["rag_retrieval", "watsonx_generation"],
        "total_latency_ms": 0,
        "context_used": result.get("context_used", False),
    }
