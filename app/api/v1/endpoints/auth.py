from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Аутентификация пользователя и выдача токена",
    tags=["auth"],
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await auth_service.login(payload.username, payload.password)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить текущего аутентифицированного пользователя",
    tags=["auth"],
)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
