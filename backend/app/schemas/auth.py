from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class AuthUserResponse(BaseModel):
    user_id: str
    email: str


class AuthResponse(BaseModel):
    authenticated: bool = True
    user: AuthUserResponse


class MeResponse(BaseModel):
    user_id: str
    email: str
    is_active: bool = True
