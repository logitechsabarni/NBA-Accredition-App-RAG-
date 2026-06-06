"""
LangGraph routing logic — decides which node to execute next
based on current AgentState.
"""
from langgraph.state import AgentState, NBAQueryIntent


def route_after_intent(state: AgentState) -> str:
    """
    After intent classification, decide whether to activate
    the CO-PO specialist agent or go directly to validation.
    """
    intent = state.get("intent", NBAQueryIntent.GENERAL_NBA)
    if intent in [NBAQueryIntent.CO_PO_MAPPING, NBAQueryIntent.ATTAINMENT_CALCULATION]:
        return "copo_agent"
    return "validation"


def route_after_copo(state: AgentState) -> str:
    """After CO-PO agent, always validate."""
    return "validation"


def route_after_validation(state: AgentState) -> str:
    """
    After validation, decide whether to retrieve context from RAG
    or go straight to Watsonx generation.
    """
    # Always try RAG if the vector store has documents
    try:
        from utils.vector_store import get_vector_store
        vs = get_vector_store()
        stats = vs.get_stats()
        if stats.get("chroma_count", 0) > 0:
            return "rag_retrieval"
    except Exception:
        pass
    return "watsonx_generation"


def route_after_rag(state: AgentState) -> str:
    """After RAG, always generate with Watsonx."""
    return "watsonx_generation"


def route_after_watsonx(state: AgentState) -> str:
    """After generation, always format response."""
    return "response_formatting"


def route_end(state: AgentState) -> str:
    """Terminal node."""
    return "__end__"
