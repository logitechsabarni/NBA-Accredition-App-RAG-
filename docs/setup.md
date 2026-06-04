# Setup Guide

## Local Run

```bash
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
docker-compose -f docker/docker-compose.yml up --build

# Notes

- Uses OpenAI GPT-4o-mini
- Granite fallback enabled
- LangGraph orchestration ready
- RAG pipeline integration pending vector DB setup
