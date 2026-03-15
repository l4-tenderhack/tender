from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db_session
from app.schemas.auth import UserResponse
from app.services.auth_service import AuthService
from app.services.cte_search_service import CteSearchService
from app.services.doc_service import DocService
from app.services.facets_service import FacetsService
from app.services.nmck_service import NmckService
from app.services.parser_service import ParserService
from app.services.search_service import SearchService

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_dependency() -> Settings:
    return get_settings()


def get_parser_service(
    db_session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> ParserService:
    return ParserService(db_session=db_session, settings=settings)


def get_auth_service(
    db_session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> AuthService:
    return AuthService(db_session=db_session, settings=settings)


def get_doc_service() -> DocService:
    return DocService()


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service


def get_nmck_service(
    db_session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> NmckService:
    return NmckService(db_session=db_session, settings=settings)


def get_facets_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> FacetsService:
    return FacetsService(db=db_session)


def get_cte_search_service(
    db_session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> CteSearchService:
    return CteSearchService(db_session=db_session, settings=settings)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует bearer-токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_bearer_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        return await auth_service.get_current_user(token)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
