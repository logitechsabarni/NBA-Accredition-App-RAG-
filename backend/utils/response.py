"""
NBA Enterprise AI Platform — Standardised API Response Helpers
All API responses follow a consistent envelope structure.
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    request_id: str = Field(default_factory=lambda: str(uuid4()))


def success_response(
    data: Any = None,
    message: str = "Request completed successfully",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=APIResponse(
            success=True,
            message=message,
            data=data,
        ).model_dump(),
    )


def error_response(
    message: str,
    errors: Optional[List[str]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=APIResponse(
            success=False,
            message=message,
            errors=errors or [],
        ).model_dump(),
    )


def created_response(data: Any, message: str = "Resource created") -> JSONResponse:
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def not_found_response(resource: str = "Resource") -> JSONResponse:
    return error_response(
        message=f"{resource} not found",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def unauthorised_response(message: str = "Authentication required") -> JSONResponse:
    return error_response(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message: str = "Insufficient permissions") -> JSONResponse:
    return error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)


def paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "OK",
) -> JSONResponse:
    import math
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=PaginatedResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            message=message,
        ).model_dump(),
    )
