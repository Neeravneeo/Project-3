from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional

class StrategyUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class StrategyResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    is_enabled: bool
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
