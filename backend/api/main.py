"""
NBA Enterprise AI Platform — FastAPI Application Entry Point
Phase 5 | API Layer
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import auth, chat, workflow, analytics, admin
from backend.api.websocket.routes import router as ws_router
from backend.core.security.middleware import AuditMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    # Startup
    yield
    # Shutdown (cleanup connections, flush buffers, etc.)


app = FastAPI(
    title="NBA Enterprise AI Platform",
    description="National Board of Accreditation — AI-assisted accreditation platform",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom middleware ──────────────────────────────────────────────────────────
app.add_middleware(AuditMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(chat.router,      prefix="/chat",      tags=["Chat / Agents"])
app.include_router(workflow.router,  prefix="/workflow",  tags=["Workflow"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router,     prefix="/admin",     tags=["Admin"])
app.include_router(ws_router,        prefix="/ws",        tags=["WebSocket"])


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
        },
    )


@app.get("/health", tags=["System"])
async def root_health() -> dict:
    """Top-level health probe used by load-balancers / k8s liveness."""
    return {"status": "healthy", "version": "5.0.0"}
