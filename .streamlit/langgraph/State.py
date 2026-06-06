"""
LangGraph state management for NBA AI pipeline.
Defines the TypedDict state that flows through all graph nodes.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class NBAQueryIntent:
    """Possible intents for NBA queries."""
    CO_PO_MAPPING = "co_po_mapping"
    ATTAINMENT_CALCULATION = "attainment_calculation"
    SAR_GUIDANCE = "sar_guidance"
    COMPLIANCE_CHECK = "compliance_check"
    GENERAL_NBA = "general_nba"
    DOCUMENT_SEARCH = "document_search"


class AgentState(TypedDict):
    """Central state object passed through the LangGraph pipeline."""

    # Input
    user_query: str
    chat_history: List[Dict[str, str]]
    session_id: str

    # Intent classification
    intent: Optional[str]
    intent_confidence: float
    entities: Dict[str, Any]  # Extracted entities: CO names, PO names, etc.

    # Retrieved context
    retrieved_chunks: List[Dict[str, Any]]
    context_text: str
    source_citations: List[str]
    retrieval_score: float

    # Validation
    compliance_issues: List[str]
    validation_passed: bool
    nba_criteria_relevant: List[int]

    # Agent routing
    route: str  # Which specialized agent handles this
    agent_notes: Annotated[List[str], operator.add]  # Accumulated notes

    # Generation
    raw_response: str
    final_response: str
    response_tokens: int

    # Metadata
    total_latency_ms: float
    nodes_executed: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    timestamp: str


def create_initial_state(
    user_query: str,
    chat_history: Optional[List[Dict]] = None,
    session_id: str = "default",
) -> AgentState:
    """Create a fresh AgentState for a new query."""
    return AgentState(
        user_query=user_query,
        chat_history=chat_history or [],
        session_id=session_id,
        intent=None,
        intent_confidence=0.0,
        entities={},
        retrieved_chunks=[],
        context_text="",
        source_citations=[],
        retrieval_score=0.0,
        compliance_issues=[],
        validation_passed=True,
        nba_criteria_relevant=[],
        route="general",
        agent_notes=[],
        raw_response="",
        final_response="",
        response_tokens=0,
        total_latency_ms=0.0,
        nodes_executed=[],
        errors=[],
        timestamp="",
    )
