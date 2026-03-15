from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_cte_search_service
from app.schemas.cte_search import CteSearchRequest, CteSearchResponse
from app.services.cte_search_service import CteSearchService

router = APIRouter(prefix="/cte-search")


@router.post(
    "",
    response_model=CteSearchResponse,
    summary="Поиск похожих КТЕ по названию и возврат контрактов",
)
async def search_cte(
    payload: CteSearchRequest,
    service: CteSearchService = Depends(get_cte_search_service),
) -> CteSearchResponse:
    return await service.search(
        query=payload.query,
        n=payload.n,
        date_from=payload.date_from,
        date_to=payload.date_to,
        region=payload.region,
        inn=payload.inn,
        score_threshold=payload.score_threshold,
    )
