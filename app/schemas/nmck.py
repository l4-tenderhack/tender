from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.cte_search import ContractOut


class SearchNmckResponse(BaseModel):
    cte_id: int
    cte_name: str | None
    search_query: str
    matched_cte_ids: list[int]
    matched_cte_names: list[str]
    prices_by_cte: dict[str, list[float]]
    contracts: list[ContractOut]
    total_contracts: int

    nmck_per_unit: Decimal

    price_min: Decimal
    price_max: Decimal
    mean_price: Decimal
    median_price: Decimal

    std_dev: Decimal
    coefficient_of_variation: Decimal
    is_homogeneous: bool

    confidence_interval_low: Decimal
    confidence_interval_high: Decimal

    sample_size_total: int
    sample_size_filtered: int
    outliers_removed: int

    warnings: list[str]
    method: str = "comparable_market_prices"


# --- Manual НМЦК ---

class ManualContractInput(BaseModel):
    unit_price: float = Field(..., gt=0, description="Цена за единицу")
    signed_at: date | None = Field(None, description="Дата контракта")
    supplier_inn: str | None = Field(None, description="ИНН поставщика")


class ManualNmckRequest(BaseModel):
    cte_id: int
    contracts: list[ManualContractInput] = Field(
        ..., min_length=1, description="Контракты, введённые пользователем"
    )


class DbContractPrice(BaseModel):
    contract_id: int | None = None
    unit_price: float
    signed_at: date | None = None
    supplier_inn: str | None = None
    is_outlier: bool = False


class ManualNmckResponse(BaseModel):
    cte_id: int
    cte_name: str | None
    db_contracts: list[DbContractPrice] = Field(default_factory=list, description="Контракты из БД для данного cte_id")
    manual_contracts: list[ManualContractInput] = Field(default_factory=list, description="Контракты, введённые пользователем")
    total_prices: int = Field(description="Общее количество цен (БД + пользовательские)")

    nmck_per_unit: Decimal

    price_min: Decimal
    price_max: Decimal
    mean_price: Decimal
    median_price: Decimal

    std_dev: Decimal
    coefficient_of_variation: Decimal
    is_homogeneous: bool

    confidence_interval_low: Decimal
    confidence_interval_high: Decimal

    sample_size_total: int
    sample_size_filtered: int
    outliers_removed: int

    warnings: list[str]
    method: str = "comparable_market_prices"
