from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_cte_search_service, get_nmck_service
from app.schemas.nmck import ManualNmckRequest, ManualNmckResponse, SearchNmckResponse
from app.services.cte_search_service import CteSearchService
from app.services.nmck_service import NmckInsufficientDataError, NmckService

router = APIRouter(prefix="/nmck")


@router.get(
    "/{cte_id}",
    response_model=SearchNmckResponse,
    summary="Расчёт НМЦК через векторный поиск + контракты",
    tags=["nmck"],
)
async def calculate_nmck_by_search(
    cte_id: int,
    top_n: int | None = Query(default=None, description="Количество похожих КТЕ из Qdrant (если не задано — 5)"),
    date_from: date | None = Query(default=None, description="Нижняя граница даты подписания контракта"),
    date_to: date | None = Query(default=None, description="Верхняя граница даты подписания контракта"),
    region: str | None = Query(default=None, description="Фильтр по региону покупателя (подстрока)"),
    inn: str | None = Query(default=None, description="Фильтр по ИНН организации"),
    score_threshold: float | None = Query(default=None, description="Порог скора для Qdrant (если не задано — из настроек бэкенда)"),
    nmck_service: NmckService = Depends(get_nmck_service),
    search_service: CteSearchService = Depends(get_cte_search_service),
) -> SearchNmckResponse:
    try:
        return await nmck_service.calculate_by_search(
            cte_id=cte_id,
            top_n=top_n,
            date_from=date_from,
            date_to=date_to,
            region=region,
            inn=inn,
            score_threshold=score_threshold,
            search_service=search_service,
        )
    except NmckInsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/manual",
    response_model=SearchNmckResponse,
    summary="Расчёт НМЦК из контрактов пользователя + БД",
    tags=["nmck"],
)
async def calculate_nmck_manual(
    payload: ManualNmckRequest,
    nmck_service: NmckService = Depends(get_nmck_service),
) -> ManualNmckResponse:
    """Пользователь добавляет свои контракты к существующим из БД для данного cte_id.
    НМЦК рассчитывается по объединённому набору цен."""
    try:
        return await nmck_service.calculate_manual(
            cte_id=payload.cte_id,
            manual_contracts=payload.contracts,
        )
    except NmckInsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
