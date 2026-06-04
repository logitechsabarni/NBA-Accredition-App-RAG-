# NBA Enterprise AI Platform

<div align="center">

![NBA Platform](https://img.shields.io/badge/NBA%20Accreditation-AI%20Platform-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)


Intelligent, Explainable Race Strategy 
Powered by
https://skillsbuild.org/
<img width="150" height="28" alt="image" src="https://github.com/user-attachments/assets/95ce5eba-232e-45ed-8fe6-11f3eebbb24b" />
https://www.ibm.com/watsonx
https://langflow.org/


Python React License

Transform racing telemetry into intelligent, explainable strategy decisions in real-time



**Production-grade AI-powered NBA Accreditation Management SaaS Platform**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [API Docs](#api-documentation) • [Deployment](#deployment)

</div>

---

## Overview

The **NBA Enterprise AI Platform** is a full-stack, production-ready SaaS solution designed for engineering colleges seeking National Board of Accreditation (NBA) certification. It automates the complete accreditation lifecycle using a multi-agent AI architecture powered by LangGraph, OpenAI GPT-4, and IBM Granite via watsonx.ai.

The platform supports deployment across hundreds of engineering colleges, with enterprise-grade security, observability, and horizontal scalability.

---

## Features

| Module | Capabilities |
|--------|-------------|
| **CO-PO Mapping** | AI-assisted mapping generation, correlation scoring, validation |
| **CO Attainment** | Direct + indirect attainment calculation per NBA norms |
| **PO Attainment** | Aggregated PO attainment from CO-PO mapping and CO attainment |
| **SAR Generation** | Criterion-wise SAR document generation with PDF export |
| **Continuous Improvement** | CI cycle tracking, action planning, improvement recommendations |
| **Gap Analysis** | Automated gap detection against NBA criteria |
| **Readiness Scoring** | Department and institution-level accreditation readiness scoring |
| **Audit Trail** | Complete immutable audit trail for all platform actions |
| **Accreditation Analytics** | KPI dashboards, department benchmarking, trend analysis |
| **AI Chat Assistant** | Conversational AI for accreditation guidance |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NBA Enterprise AI Platform                    │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite + TailwindCSS + Zustand)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │Dashboard │ │AI Chat   │ │SAR Builder│ │Analytics         │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI + Nginx)                                   │
│  Auth Routes │ Chat Routes │ Workflow Routes │ Analytics Routes  │
├─────────────────────────────────────────────────────────────────┤
│  LangGraph Orchestration Engine                                  │
│  Intent → Route → Agent → Validate → RAG → LLM → Audit         │
├──────────────────────────┬──────────────────────────────────────┤
│  AI Agents               │  RAG System                          │
│  ├── COPOAgent           │  ├── PDF Loader                      │
│  ├── AttainmentAgent     │  ├── Chunking Engine                 │
│  ├── SARAgent            │  ├── SentenceTransformers            │
│  ├── CIAgent             │  ├── FAISS Vector Store              │
│  ├── AnalyticsAgent      │  └── Metadata Retriever              │
│  └── ValidationAgent     │                                      │
├──────────────────────────┴──────────────────────────────────────┤
│  LLM Layer               │  Data Layer                          │
│  ├── OpenAI GPT-4o       │  ├── PostgreSQL (relational)         │
│  └── IBM Granite         │  ├── MongoDB (documents/logs)        │
│      (watsonx.ai)        │  └── Redis (cache/queue)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.11** — Runtime
- **FastAPI** — Async REST API framework
- **LangGraph** — Agentic workflow orchestration
- **SQLAlchemy Async** — ORM with PostgreSQL
- **Alembic** — Database migrations
- **FAISS** — Vector similarity search
- **Sentence Transformers** — Embedding generation
- **OpenAI API** — GPT-4o for complex reasoning
- **IBM Granite via watsonx.ai** — Domain-adapted LLM
- **Prometheus** — Metrics and monitoring

### Frontend
- **React 18** + **Vite** — UI framework
- **TailwindCSS** — Utility-first styling
- **Zustand** — Lightweight state management
- **Axios** — HTTP client with interceptors
- **React Router v6** — Client-side routing
- **Recharts** — Data visualization

### Infrastructure
- **Docker** + **Docker Compose** — Containerization
- **Kubernetes** — Production orchestration
- **Nginx** — Reverse proxy + SSL termination
- **Render** — Backend hosting
- **Vercel** — Frontend hosting

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2+
- Python 3.11+
- Node.js 20+
- OpenAI API key
- IBM watsonx.ai credentials (optional)

### 1. Clone the repository
```bash
git clone https://github.com/your-org/NBA_Enterprise_AI_Platform.git
cd NBA_Enterprise_AI_Platform
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your actual API keys and credentials
```

### 3. Start with Docker Compose
```bash
docker-compose up -d
```

### 4. Run database migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 5. Ingest NBA knowledge base
```bash
docker-compose exec backend python -m rag.nba_knowledge_base --ingest
```

### 6. Access the platform
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## API Documentation

Interactive Swagger UI available at: `http://localhost:8000/docs`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Authenticate user |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/chat` | AI chat with accreditation assistant |
| POST | `/workflow/copo` | Trigger CO-PO mapping workflow |
| POST | `/workflow/attainment` | Run attainment calculation |
| POST | `/workflow/sar` | Generate SAR document |
| POST | `/workflow/ci` | Run continuous improvement analysis |
| GET | `/analytics/readiness` | Get readiness score |
| GET | `/analytics/dashboard` | Get dashboard analytics |
| GET | `/health` | Health check |

---

## Project Structure

```
NBA_Enterprise_AI_Platform/
├── .env.example              # Environment template
├── .gitignore
├── docker-compose.yml        # Multi-service orchestration
├── nginx.conf                # Reverse proxy configuration
├── kubernetes.yaml           # K8s manifests
├── render.yaml               # Render deployment config
├── vercel.json               # Vercel deployment config
│
├── backend/
│   ├── api/                  # FastAPI route handlers
│   ├── agents/               # LangGraph AI agents
│   ├── core/                 # Orchestration engine
│   ├── rag/                  # RAG pipeline
│   ├── llm/                  # LLM clients and routing
│   ├── models/               # SQLAlchemy + Pydantic models
│   ├── services/             # Business logic layer
│   ├── db/                   # Database connections + migrations
│   ├── config/               # Settings and configuration
│   ├── utils/                # Shared utilities
│   └── prompts/              # LLM prompt templates
│
├── frontend/
│   └── src/
│       ├── pages/            # React page components
│       ├── components/       # Reusable UI components
│       ├── charts/           # Recharts visualizations
│       ├── services/         # Axios API services
│       ├── store/            # Zustand state stores
│       └── utils/            # Frontend utilities
│
├── deployment/               # CI/CD and infra configs
├── docs/                     # Architecture and API docs
├── data/                     # NBA knowledge base PDFs
├── vector_db/                # FAISS index persistence
├── logs/                     # Application logs
└── tests/                    # Unit and integration tests
```

---

## Environment Variables

See [`.env.example`](.env.example) for the complete list of required environment variables.

Key variables:
- `DATABASE_URL` — PostgreSQL async connection string
- `MONGO_URI` — MongoDB connection URI
- `REDIS_URL` — Redis connection URL
- `OPENAI_API_KEY` — OpenAI API key
- `WATSONX_API_KEY` — IBM watsonx.ai API key
- `JWT_SECRET_KEY` — JWT signing secret (min 32 chars)

---

## Deployment

### Docker Compose (Recommended for staging)
```bash
docker-compose -f docker-compose.yml up -d --build
```

### Kubernetes (Production)
```bash
# Update secrets in kubernetes.yaml first
kubectl apply -f kubernetes.yaml
kubectl get pods -n nba-platform
```

### Render + Vercel (Cloud)
```bash
# Backend auto-deploys from render.yaml on push to main
# Frontend auto-deploys from vercel.json on push to main
```

See [deployment guide](docs/deployment_guide.md) for detailed instructions.

---

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=. --cov-report=html

# Frontend tests
cd frontend
npm run test
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built for engineering colleges pursuing NBA accreditation. Powered by OpenAI GPT-4, IBM Granite (watsonx.ai), LangGraph, and FAISS.
