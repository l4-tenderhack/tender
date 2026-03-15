import hashlib
import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings
from app.core.redis import get_redis

logger = logging.getLogger("app.request")


class CacheMiddleware(BaseHTTPMiddleware):
    CACHE_PATHS = {"/api/v1/cte-search"}

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in self.CACHE_PATHS:
            return await call_next(request)

        redis = get_redis()
        if redis is None:
            return await call_next(request)

        session_id = request.cookies.get("user_session_id") or str(uuid.uuid4())
        body = await request.body()
        cache_key = "cte:" + hashlib.sha256(f"{session_id}:{body}".encode()).hexdigest()

        cached = await redis.get(cache_key)
        if cached:
            resp = Response(content=cached, media_type="application/json")
            resp.headers["X-Cache"] = "HIT"
            return resp

        request._body = body
        response = await call_next(request)

        body_chunks = [chunk async for chunk in response.body_iterator]
        response_body = b"".join(body_chunks)

        if response.status_code == 200:
            settings = get_settings()
            await redis.setex(cache_key, settings.cache_ttl_seconds, response_body.decode())

        new_resp = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
        new_resp.headers["X-Cache"] = "MISS"
        if "user_session_id" not in request.cookies:
            new_resp.set_cookie("user_session_id", session_id, max_age=86400 * 30, httponly=True)
        return new_resp


def register_middlewares(app: FastAPI, settings: Settings) -> None:

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(CacheMiddleware)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        started_at = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            request_id = getattr(request.state, "request_id", "-")
            status_code = response.status_code if response is not None else 500
            logger.info(
                "%s %s -> %s (%.2f ms) request_id=%s",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
            )
