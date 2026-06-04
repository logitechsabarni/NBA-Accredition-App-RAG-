"""
NBA Enterprise AI Platform — FastAPI Application Factory
Builds and configures the FastAPI application with all middleware,
exception handlers, routers, and lifecycle hooks.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError

from config.settings import settings
from config.logging_config import configure_logging, get_logger
from db.postgres import init_db, close_db
from db.mongodb import MongoDBClient
from db.redis_client import init_redis, close_redis
from utils.exceptions import NBABaseException, RateLimitError
from utils.response import error_response

logger = get_logger(__name__)


# ----------------------------------------------------------------
# Application Lifespan
# ----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle management."""
    configure_logging(
        log_level=settings.LOG_LEVEL,
        is_development=settings.is_development,
    )
    logger.info(
        "Starting NBA Enterprise AI Platform",
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # Startup
    await init_redis()
    await MongoDBClient.connect()

    if settings.is_development:
        await init_db()

    # Initialise Prometheus metrics if enabled
    if settings.METRICS_ENABLED:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    logger.info("All services connected — NBA Platform ready")
    yield

    # Shutdown
    logger.info("Shutting down NBA Platform...")
    await close_db()
    await MongoDBClient.disconnect()
    await close_redis()
    logger.info("NBA Platform shutdown complete")


# ----------------------------------------------------------------
# Application Factory
# ----------------------------------------------------------------

def create_application() -> FastAPI:
    app = FastAPI(
        title="NBA Enterprise AI Platform",
        description=(
            "AI-powered NBA Accreditation Management Platform for engineering colleges. "
            "Automates CO-PO mapping, attainment calculation, SAR generation, "
            "continuous improvement tracking, and accreditation analytics."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    _register_middleware(app)
    _register_exception_handlers(app)
    _register_routers(app)

    return app


def _register_middleware(app: FastAPI) -> None:
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
        max_age=settings.CORS_MAX_AGE,
    )

    # GZip compression for responses > 1 KB
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        from uuid import uuid4
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        import structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        if request.url.path in {"/health", "/metrics", "/"}:
            return await call_next(request)
        from db.redis_client import rate_limit_check
        client_ip = request.client.host if request.client else "unknown"
        allowed = await rate_limit_check(
            identifier=f"ip:{client_ip}",
            limit=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        )
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"success": False, "message": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NBABaseException)
    async def nba_exception_handler(request: Request, exc: NBABaseException):
        logger.warning("Domain exception", error=exc.message, type=type(exc).__name__)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "Invalid or expired token"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False, "message": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error. Please try again or contact support.",
            },
        )


def _register_routers(app: FastAPI) -> None:
    from api.auth_routes import router as auth_router
    from api.chat_routes import router as chat_router
    from api.workflow_routes import router as workflow_router
    from api.analytics_routes import router as analytics_router

    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(chat_router, prefix="/chat", tags=["AI Chat"])
    app.include_router(workflow_router, prefix="/workflow", tags=["Workflows"])
    app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

    @app.get("/health", tags=["System"])
    async def health_check():
        from db.redis_client import get_redis
        checks = {"api": "ok", "redis": "unknown", "postgres": "unknown", "mongodb": "unknown"}
        try:
            await get_redis().ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"
        try:
            from db.postgres import engine
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception:
            checks["postgres"] = "error"
        try:
            from db.mongodb import MongoDBClient
            await MongoDBClient.get_db().command("ping")
            checks["mongodb"] = "ok"
        except Exception:
            checks["mongodb"] = "error"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "healthy" if all_ok else "degraded",
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
                "services": checks,
            },
        )

    @app.get("/", tags=["System"])
    async def root():
        return {
            "platform": "NBA Enterprise AI Platform",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }
