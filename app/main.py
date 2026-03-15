from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middlewares
from app.core.redis import close_redis, init_redis
from app.services.search_service import SearchService
from app.services.hybrid_search_service import HybridSearchService


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_redis()
    settings = get_settings()
    if settings.qdrant_url:
        search_service = HybridSearchService(settings=settings)
    else:
        search_service = SearchService(settings=settings)
    await search_service.connect()
    application.state.search_service = search_service
    yield
    await search_service.disconnect()
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging(level=settings.log_level, app_env=settings.app_env)

    application = FastAPI(
        title=settings.app_name,
        description="Бэкенд для расчёта НМЦК с векторным поиском КТЕ.",
        version="0.1.0",
        debug=settings.debug,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    register_middlewares(application, settings)
    register_exception_handlers(application)

    @application.get("/health", tags=["system"], summary="Application healthcheck")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
