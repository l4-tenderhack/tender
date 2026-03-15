from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.models.procurement import Contract, ContractItem, CteMain, Organization
from app.schemas.cte import CteItem, CteOrganizationsRequest, CteOrganizationsResponse
from app.schemas.procurement import OrganizationResponse

router = APIRouter(prefix="/cte")


@router.get(
    "/{cte_id}",
    response_model=CteItem,
    summary="Получить КТЕ по ID",
    tags=["cte"],
)
async def get_cte_by_id(
    cte_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CteItem:
    row = (await db.execute(select(CteMain).where(CteMain.cte_id == cte_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="КТЕ не найдена")
    return CteItem.model_validate(row)


@router.post(
    "/organizations",
    response_model=CteOrganizationsResponse,
    summary="Получить организации по ID КТЕ",
    tags=["cte"],
)
async def get_organizations_by_cte_ids(
    payload: CteOrganizationsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CteOrganizationsResponse:
    """Return unique organizations (buyers and suppliers) linked to the given cte_ids
    via contract_items → contracts → organizations."""
    stmt = (
        select(Organization)
        .join(
            Contract,
            (Contract.buyer_org_id == Organization.id)
            | (Contract.supplier_org_id == Organization.id),
        )
        .join(ContractItem, ContractItem.contract_id == Contract.id)
        .where(ContractItem.cte_id.in_(payload.cte_ids))
        .distinct()
    )
    orgs = (await db.execute(stmt)).scalars().all()
    return CteOrganizationsResponse(
        total=len(orgs),
        organizations=[OrganizationResponse.model_validate(o) for o in orgs],
    )
