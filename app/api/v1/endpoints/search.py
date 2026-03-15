import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.dependencies import get_facets_service, get_search_service
from app.schemas.search import (
    FacetsResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SuggestResponse,
)
from app.services.facets_service import FacetsService
from app.services.search_service import SearchRequest as SvcSearchRequest, SearchService


def _aggregate_characteristics(results: list[Any]) -> dict[str, list[str]]:
    agg: dict[str, set[str]] = {}
    for r in results:
        chars = r.characteristics if isinstance(r.characteristics, dict) else {}
        for key, val in chars.items():
            sval = str(val).strip()
            if sval:
                agg.setdefault(key, set()).add(sval)
    return {k: sorted(v) for k, v in sorted(agg.items())}

router = APIRouter(prefix="/search")


@router.post("", response_model=SearchResponse, summary="Полнотекстовый поиск", tags=["search"])
async def search(
    payload: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    start = time.time()
    try:
        results = await service.search(
            SvcSearchRequest(
                query=payload.query,
                category=payload.category,
                manufacturer=payload.manufacturer,
                price_min=payload.price_min,
                price_max=payload.price_max,
                characteristics=payload.characteristics,
                limit=payload.limit,
                offset=payload.offset,
                score_threshold=payload.score_threshold,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    search_results = [
        SearchResult(
            cte_id=r.cte_id,
            category=r.category,
            manufacturer=r.manufacturer,
            description=r.description,
            price=r.price,
            characteristics=r.characteristics,
            score=r.score,
            category_boost=r.category_boost,
            region=r.region,
            date=r.date,
        )
        for r in results
    ]

    return SearchResponse(
        total=len(search_results),
        execution_time_ms=round((time.time() - start) * 1000, 2),
        results=search_results,
        available_characteristics=_aggregate_characteristics(results),
    )


@router.get("", response_model=SearchResponse, summary="Полнотекстовый поиск (GET)", tags=["search"])
async def search_get(
    q: str = Query(..., description="Поисковый запрос"),
    category: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return await search(
        SearchRequest(
            query=q, category=category, manufacturer=manufacturer, limit=limit, offset=offset
        ),
        service,
    )


@router.get("/facets", response_model=FacetsResponse, summary="Получить фасеты", tags=["search"])
async def get_facets(
    facets_service: FacetsService = Depends(get_facets_service),
) -> FacetsResponse:
    try:
        return await facets_service.get_facets()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/suggest", response_model=SuggestResponse, summary="Поисковые подсказки", tags=["search"]
)
async def suggest(
    prefix: str = Query(..., description="Префикс запроса"),
    limit: int = Query(10, ge=1, le=20),
    service: SearchService = Depends(get_search_service),
) -> SuggestResponse:
    try:
        suggestions = await service.suggest(prefix, limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return SuggestResponse(suggestions=suggestions)


@router.post(
    "/hybrid",
    response_model=SearchResponse,
    summary="Гибридный семантический поиск (Qdrant + Ollama)",
    tags=["search"],
)
async def hybrid_search(
    payload: SearchRequest,
    request: Request,
) -> SearchResponse:
    from app.services.hybrid_search_service import HybridSearchService

    svc = request.app.state.search_service
    if not isinstance(svc, HybridSearchService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Гибридный поиск не включён. Укажите QDRANT_URL в переменных окружения.",
        )

    start = time.time()
    try:
        results = await svc.search(
            SvcSearchRequest(
                query=payload.query,
                category=payload.category,
                manufacturer=payload.manufacturer,
                price_min=payload.price_min,
                price_max=payload.price_max,
                characteristics=payload.characteristics,
                limit=payload.limit,
                offset=payload.offset,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    search_results = [
        SearchResult(
            cte_id=r.cte_id,
            category=r.category,
            manufacturer=r.manufacturer,
            description=r.description,
            price=r.price,
            characteristics=r.characteristics,
            score=r.score,
            category_boost=r.category_boost,
            region=r.region,
            date=r.date,
        )
        for r in results
    ]

    return SearchResponse(
        total=len(search_results),
        execution_time_ms=round((time.time() - start) * 1000, 2),
        results=search_results,
        available_characteristics=_aggregate_characteristics(results),
    )


@router.get("/stats", summary="Статистика поискового индекса", tags=["search"])
async def get_stats(service: SearchService = Depends(get_search_service)) -> dict:
    try:
        return await service.get_statistics()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
