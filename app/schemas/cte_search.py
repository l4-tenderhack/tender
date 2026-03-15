from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CteSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Название КТЕ для поиска")
    n: int | None = Field(default=None, description="Количество похожих КТЕ (если не задано — из настроек бэкенда)")
    date_from: date | None = Field(None, description="Нижняя граница даты подписания контракта")
    date_to: date | None = Field(None, description="Верхняя граница даты подписания контракта")
    region: str | None = Field(None, description="Фильтр по региону покупателя (подстрока)")
    inn: str | None = Field(None, description="Фильтр по ИНН организации")
    score_threshold: float | None = Field(default=None, description="Порог скора для Qdrant (если не задано — из настроек бэкенда)")


class CteMatch(BaseModel):
    cte_id: str
    cte_name: str
    category: str = ""
    manufacturer: str = ""
    description: str = ""
    price: float = 0.0
    region: str = ""
    date: str | None = None
    characteristics: dict = Field(default_factory=dict)
    score: float = 0.0
    category_boost: float = 1.0


class ContractItemOut(BaseModel):
    cte_id: int
    cte_position_name: str | None
    unit_price: Decimal | None
    quantity: Decimal | None
    unit_name: str | None


class ContractOut(BaseModel):
    contract_id: int
    contract_external_id: int
    purchase_name: str
    signed_at: str | None
    buyer_inn: str | None
    buyer_region: str | None
    supplier_inn: str | None
    items: list[ContractItemOut]


class CteSearchResponse(BaseModel):
    query: str
    matched_ctes: list[CteMatch]
    contracts: list[ContractOut]
    total_contracts: int
    available_characteristics: dict[str, list[str]] = Field(default_factory=dict)
    elapsed_ms: float | None = Field(None, description="Время выполнения поиска (мс)")
