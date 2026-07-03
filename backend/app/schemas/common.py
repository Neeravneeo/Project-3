from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
