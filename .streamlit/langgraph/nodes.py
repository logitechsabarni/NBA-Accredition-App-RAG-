"""
LangGraph pipeline nodes for NBA AI platform.
Each node transforms AgentState and passes it forward.
"""
import time
import re
import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.state import AgentState, NBAQueryIntent

logger = logging.getLogger(__name__)

# ── Intent keywords ───────────────────────────────────────────────────────────
INTENT_KEYWORDS = {
    NBAQueryIntent.CO_PO_MAPPING: [
        "co-po", "co po", "course outcome", "program outcome", "mapping",
        "correlation", "matrix", "bloom", "co1", "co2", "po1", "po2", "heatmap",
    ],
    NBAQueryIntent.ATTAINMENT_CALCULATION: [
        "attainment", "calculate", "computation", "direct assessment", "indirect assessment",
        "score", "percentage", "threshold", "60%", "target", "achievement",
    ],
    NBAQueryIntent.SAR_GUIDANCE: [
        "sar", "self assessment report", "report", "document", "prepare",
        "section", "write", "criterion", "criteria",
    ],
    NBAQueryIntent.COMPLIANCE_CHECK: [
        "compliance", "nba requirement", "criteria", "tier", "tier-1", "tier-2",
        "criterion", "marks", "accreditation requirement", "nba mandate",
    ],
    NBAQueryIntent.DOCUMENT_SEARCH: [
        "find", "search", "where", "locate", "document", "guideline", "manual",
        "handbook", "reference",
    ],
}


def intent_classification_node(state: AgentState) -> AgentState:
    """Classify the query intent using keyword matching."""
    start = time.time()
    query_lower = state["user_query"].lower()

    scores: Dict[str, int] = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                scores[intent] += 1

    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    if best_score == 0:
        best_intent = NBAQueryIntent.GENERAL_NBA
        confidence = 0.5
    else:
        total = sum(scores.values())
        confidence = round(best_score / max(total, 1), 2)

    # Extract entities
    entities: Dict[str, Any] = {}
    co_matches = re.findall(r"\b(CO\d+)\b", state["user_query"], re.IGNORECASE)
    po_matches = re.findall(r"\b(PO\d{1,2})\b", state["user_query"], re.IGNORECASE)
    if co_matches:
        entities["cos"] = list(set(m.upper() for m in co_matches))
    if po_matches:
        entities["pos"] = list(set(m.upper() for m in po_matches))

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "intent": best_intent,
        "intent_confidence": confidence,
        "entities": entities,
        "route": best_intent,
        "nodes_executed": state["nodes_executed"] + ["intent_classification"],
        "agent_notes": state["agent_notes"] + [
            f"Intent: {best_intent} (confidence: {confidence})"
        ],
        "total_latency_ms": state["total_latency_ms"] + latency,
    }


def copo_agent_node(state: AgentState) -> AgentState:
    """Handles CO-PO specific routing and context enrichment."""
    start = time.time()
    notes = []

    if state["intent"] in [NBAQueryIntent.CO_PO_MAPPING, NBAQueryIntent.ATTAINMENT_CALCULATION]:
        notes.append("Activating OBE specialist context")
        entities = state.get("entities", {})
        if entities.get("cos"):
            notes.append(f"COs identified: {', '.join(entities['cos'])}")
        if entities.get("pos"):
            notes.append(f"POs identified: {', '.join(entities['pos'])}")

        # Criteria relevance for CO-PO
        nba_criteria = [3]  # Criterion 3: CO and PO Attainment
        if state["intent"] == NBAQueryIntent.ATTAINMENT_CALCULATION:
            nba_criteria.append(2)  # Criterion 2: Curriculum
    else:
        nba_criteria = []
        notes.append("Passing to general handler")

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "nba_criteria_relevant": nba_criteria,
        "nodes_executed": state["nodes_executed"] + ["copo_agent"],
        "agent_notes": state["agent_notes"] + notes,
        "total_latency_ms": state["total_latency_ms"] + latency,
    }


def validation_node(state: AgentState) -> AgentState:
    """Validates query against NBA compliance rules."""
    start = time.time()
    issues = []
    query_lower = state["user_query"].lower()

    # Check for known anti-patterns
    if "hardcode" in query_lower:
        issues.append("Warning: Hardcoding values is not NBA best practice.")
    if "ignore attainment" in query_lower:
        issues.append("Warning: Cannot ignore attainment — core NBA requirement.")
    if "70%" in query_lower and state["intent"] == NBAQueryIntent.ATTAINMENT_CALCULATION:
        issues.append("Note: NBA standard target is 60%, not 70%, unless institution sets higher.")

    # SAR completeness hints
    if state["intent"] == NBAQueryIntent.SAR_GUIDANCE:
        issues.append("Note: Ensure all 9 criteria sections are covered in SAR.")

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "compliance_issues": issues,
        "validation_passed": len(issues) == 0 or all("Note" in i for i in issues),
        "nodes_executed": state["nodes_executed"] + ["validation"],
        "agent_notes": state["agent_notes"] + (issues if issues else ["Validation: PASS"]),
        "total_latency_ms": state["total_latency_ms"] + latency,
    }


def rag_retrieval_node(state: AgentState) -> AgentState:
    """Retrieves relevant document chunks from vector store."""
    start = time.time()
    try:
        from utils.rag_engine import get_rag_engine
        rag = get_rag_engine()
        results = rag.retrieve(state["user_query"], top_k=5)
        context = rag.build_context(results) if results else ""
        citations = rag.format_sources(results) if results else []
        avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0.0
        note = f"RAG: retrieved {len(results)} chunks, avg score={avg_score:.2f}"
    except Exception as e:
        results = []
        context = ""
        citations = []
        avg_score = 0.0
        note = f"RAG failed: {str(e)[:60]}"
        logger.error(f"RAG node error: {e}")

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "retrieved_chunks": results,
        "context_text": context,
        "source_citations": citations,
        "retrieval_score": avg_score,
        "nodes_executed": state["nodes_executed"] + ["rag_retrieval"],
        "agent_notes": state["agent_notes"] + [note],
        "total_latency_ms": state["total_latency_ms"] + latency,
    }


def watsonx_generation_node(state: AgentState) -> AgentState:
    """Generates response using IBM Watsonx Granite."""
    start = time.time()
    from config.constants import NBA_SYSTEM_PROMPT

    context = state.get("context_text", "")
    history = state.get("chat_history", [])
    history_text = ""
    for msg in history[-4:]:
        role = msg.get("role", "user").capitalize()
        history_text += f"\n{role}: {msg.get('content', '')}"

    if context:
        prompt = f"""Based on the following NBA knowledge base context, answer the question.

CONTEXT:
{context}

CHAT HISTORY:{history_text if history_text else ' None'}

COMPLIANCE NOTES: {'; '.join(state.get('compliance_issues', [])) or 'None'}

QUESTION: {state['user_query']}

ANSWER:"""
    else:
        prompt = f"""CHAT HISTORY:{history_text if history_text else ' None'}

QUESTION: {state['user_query']}

ANSWER:"""

    try:
        from utils.watsonx_client import get_watsonx_client
        wc = get_watsonx_client()
        response = wc.generate_response(
            prompt=prompt,
            system_prompt=NBA_SYSTEM_PROMPT,
            max_tokens=1024,
            temperature=0.7,
        )
        tokens = len(response.split())
        note = f"Watsonx: generated {tokens} tokens"
    except Exception as e:
        response = f"AI generation error: {str(e)}"
        tokens = 0
        note = f"Watsonx error: {str(e)[:60]}"
        logger.error(f"Watsonx node error: {e}")

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "raw_response": response,
        "response_tokens": tokens,
        "nodes_executed": state["nodes_executed"] + ["watsonx_generation"],
        "agent_notes": state["agent_notes"] + [note],
        "total_latency_ms": state["total_latency_ms"] + latency,
    }


def response_formatting_node(state: AgentState) -> AgentState:
    """Formats the final response with citations and notes."""
    start = time.time()

    response = state["raw_response"]

    # Append citations if available
    citations = state.get("source_citations", [])
    if citations:
        response += "\n\n**📚 Sources:**\n" + "\n".join(f"- {c}" for c in citations)

    # Append compliance notes
    issues = state.get("compliance_issues", [])
    if issues:
        notes_text = "\n".join(f"- {i}" for i in issues)
        response += f"\n\n**ℹ️ NBA Notes:**\n{notes_text}"

    latency = round((time.time() - start) * 1000)
    return {
        **state,
        "final_response": response,
        "timestamp": datetime.now().isoformat(),
        "nodes_executed": state["nodes_executed"] + ["response_formatting"],
        "agent_notes": state["agent_notes"] + [f"Response formatted: {len(response)} chars"],
        "total_latency_ms": state["total_latency_ms"] + latency,
    }
