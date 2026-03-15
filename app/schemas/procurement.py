from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class OrganizationResponse(BaseModel):
    id: int
    inn: str
    region_name: str | None
    org_type: str

    model_config = {"from_attributes": True}


class ContractItemResponse(BaseModel):
    id: int
    cte_id: int
    cte_position_name: str | None
    quantity: Decimal | None
    unit_name: str | None
    unit_price: Decimal | None

    model_config = {"from_attributes": True}


class ContractResponse(BaseModel):
    id: int
    contract_external_id: int
    purchase_name: str
    procurement_method: str | None
    initial_price: Decimal | None
    final_price: Decimal | None
    discount_percent: Decimal | None
    vat_rate_text: str | None
    signed_at: datetime | None
    buyer_org_id: int | None
    supplier_org_id: int | None

    model_config = {"from_attributes": True}


class ContractDetailResponse(ContractResponse):
    buyer_organization: OrganizationResponse | None = None
    supplier_organization: OrganizationResponse | None = None
    items: list[ContractItemResponse] = Field(default_factory=list)


class ContractListResponse(BaseModel):
    total: int
    items: list[ContractResponse]


class ContractFilterRequest(BaseModel):
    purchase_name: str | None = Field(None, description="Фильтр по названию закупки (частичное совпадение)")
    procurement_method: str | None = Field(None, description="Фильтр по способу закупки")
    buyer_inn: str | None = Field(None, description="Фильтр по ИНН покупателя")
    supplier_inn: str | None = Field(None, description="Фильтр по ИНН поставщика")
    signed_after: datetime | None = Field(None, description="Фильтр: контракты подписанные после этой даты")
    signed_before: datetime | None = Field(None, description="Фильтр: контракты подписанные до этой даты")
    price_min: Decimal | None = Field(None, ge=0, description="Минимальная итоговая цена")
    price_max: Decimal | None = Field(None, ge=0, description="Максимальная итоговая цена")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
