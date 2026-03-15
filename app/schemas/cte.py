from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.procurement import OrganizationResponse


class CteItem(BaseModel):
    cte_id: str
    category: str
    manufacturer: str
    description: str
    price: Decimal | None
    price_normalized: Decimal | None
    region: str | None
    characteristics: dict[str, Any] | None

    model_config = {"from_attributes": True}


class CteOrganizationsRequest(BaseModel):
    cte_ids: list[int] = Field(..., min_length=1, description="Список ID КТЕ для поиска")


class CteOrganizationsResponse(BaseModel):
    total: int
    organizations: list[OrganizationResponse]
