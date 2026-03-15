from pydantic import BaseModel, Field


class LoginRequest(BaseModel):

    username: str = Field(min_length=1, examples=["demo"])
    password: str = Field(min_length=1, examples=["demo-password"])


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):

    username: str
    is_active: bool = True
