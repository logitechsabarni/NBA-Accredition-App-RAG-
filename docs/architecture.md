# NBA Enterprise AI Platform Architecture

## Layers
- API Layer (FastAPI)
- Core Orchestrator (LangGraph)
- LLM Layer (OpenAI + Granite)
- RAG Layer (Embeddings + Vector DB)
- Services Layer (Business logic)

## Flow
User → API → Orchestrator → RAG → LLM Router → Response
