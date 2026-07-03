from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
