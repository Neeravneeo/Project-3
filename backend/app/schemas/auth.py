from pydantic import BaseModel, EmailStr, ConfigDict

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
