"""
NBA Enterprise AI Platform — Custom Exception Hierarchy
Domain-specific exceptions with HTTP status mappings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class NBABaseException(Exception):
    """Root exception for all NBA Platform errors."""

    status_code: int = 500
    default_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
    ) -> None:
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": type(self).__name__,
            "message": self.message,
            "detail": self.detail,
        }


# ----------------------------------------------------------------
# Authentication & Authorisation
# ----------------------------------------------------------------

class AuthenticationError(NBABaseException):
    status_code = 401
    default_message = "Authentication failed"


class TokenExpiredError(AuthenticationError):
    default_message = "Token has expired"


class InvalidTokenError(AuthenticationError):
    default_message = "Invalid token"


class AuthorizationError(NBABaseException):
    status_code = 403
    default_message = "Insufficient permissions"


# ----------------------------------------------------------------
# Resource Errors
# ----------------------------------------------------------------

class NotFoundError(NBABaseException):
    status_code = 404
    default_message = "Resource not found"


class ConflictError(NBABaseException):
    status_code = 409
    default_message = "Resource already exists"


class ValidationError(NBABaseException):
    status_code = 422
    default_message = "Validation failed"


# ----------------------------------------------------------------
# Business Logic Errors
# ----------------------------------------------------------------

class WorkflowError(NBABaseException):
    status_code = 500
    default_message = "Workflow execution failed"


class AgentError(NBABaseException):
    status_code = 500
    default_message = "AI agent execution failed"


class LLMError(NBABaseException):
    status_code = 502
    default_message = "LLM provider returned an error"


class RAGError(NBABaseException):
    status_code = 500
    default_message = "RAG retrieval failed"


class AttainmentCalculationError(NBABaseException):
    status_code = 422
    default_message = "Attainment calculation failed"


class MappingError(NBABaseException):
    status_code = 422
    default_message = "CO-PO mapping error"


class SARGenerationError(NBABaseException):
    status_code = 500
    default_message = "SAR generation failed"


# ----------------------------------------------------------------
# Infrastructure Errors
# ----------------------------------------------------------------

class DatabaseError(NBABaseException):
    status_code = 503
    default_message = "Database operation failed"


class CacheError(NBABaseException):
    status_code = 503
    default_message = "Cache operation failed"


class ExternalServiceError(NBABaseException):
    status_code = 502
    default_message = "External service unavailable"


class RateLimitError(NBABaseException):
    status_code = 429
    default_message = "Rate limit exceeded"
