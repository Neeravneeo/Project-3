from typing import TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class PaginatedResponse[T](BaseModel):
    """Generic paginated list wrapper."""
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    limit: int
    has_next: bool

class ErrorResponse(BaseModel):
    """Standard error envelope."""
    detail: str
    code: str | None = None
