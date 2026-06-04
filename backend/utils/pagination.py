"""
NBA Enterprise AI Platform — Pagination Utilities
"""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    page: int = Field(default=DEFAULT_PAGE, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def paginate_query(page: int = DEFAULT_PAGE, page_size: int = DEFAULT_PAGE_SIZE):
    """FastAPI dependency for pagination query params."""
    return PaginationParams(page=page, page_size=page_size)
