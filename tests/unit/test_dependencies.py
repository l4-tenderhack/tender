import asyncio

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import Settings
from app.core.dependencies import (
    get_auth_service,
    get_bearer_token,
    get_current_user,
    get_ollama_service,
    get_parser_service,
)
from app.schemas.auth import UserResponse
from app.services.auth_service import AuthService
from app.services.ollama_service import OllamaService
from app.services.parser_service import ParserService


class _AuthServiceOk:

    async def get_current_user(self, token: str) -> UserResponse:
        return UserResponse(username=f"user:{token}", is_active=True)


class _AuthServiceFail:

    async def get_current_user(self, token: str) -> UserResponse:
        _ = token
        raise NotImplementedError("JWT authentication is not implemented yet.")


def test_get_bearer_token_success() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-123")

    token = get_bearer_token(credentials)

    assert token == "token-123"


def test_get_bearer_token_missing() -> None:
    with pytest.raises(HTTPException) as exc:
        get_bearer_token(None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing bearer token"


def test_di_service_providers() -> None:
    settings = Settings()

    parser = get_parser_service(db_session=object(), settings=settings)
    auth = get_auth_service(db_session=object(), settings=settings)
    ollama = get_ollama_service(settings=settings)

    assert isinstance(parser, ParserService)
    assert isinstance(auth, AuthService)
    assert isinstance(ollama, OllamaService)


def test_get_current_user_success() -> None:
    result = asyncio.run(get_current_user(token="abc", auth_service=_AuthServiceOk()))

    assert result.username == "user:abc"


def test_get_current_user_not_implemented() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(token="abc", auth_service=_AuthServiceFail()))

    assert exc.value.status_code == 501
    assert "not implemented" in str(exc.value.detail).lower()
