"""Service that builds search facets from DB and caches them in Redis."""
import json
import logging

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import get_redis
from app.models.procurement import CteCharacteristic, Organization, RegionCoordinate
from app.schemas.search import FacetItem, FacetsResponse, RegionFacet

logger = logging.getLogger(__name__)

_CACHE_KEY = "facets:v1"
_CACHE_TTL = 3600  # 1 hour


class FacetsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_facets(self) -> FacetsResponse:
        redis = get_redis()
        if redis is not None:
            cached = await redis.get(_CACHE_KEY)
            if cached:
                return FacetsResponse.model_validate_json(cached)

        facets = await self._build_facets()

        if redis is not None:
            try:
                await redis.setex(_CACHE_KEY, _CACHE_TTL, facets.model_dump_json())
            except Exception:
                logger.warning("Failed to cache facets in Redis", exc_info=True)

        return facets

    async def _build_facets(self) -> FacetsResponse:
        characteristics, regions = await self._fetch_characteristics(), None
        regions = await self._fetch_regions()
        return FacetsResponse(characteristics=characteristics, regions=regions)

    async def _fetch_characteristics(self) -> dict[str, list[FacetItem]]:
        stmt = (
            select(
                CteCharacteristic.char_name,
                CteCharacteristic.char_value,
                func.count().label("cnt"),
            )
            .group_by(CteCharacteristic.char_name, CteCharacteristic.char_value)
            .order_by(CteCharacteristic.char_name, func.count().desc())
        )
        rows = (await self.db.execute(stmt)).all()

        result: dict[str, list[FacetItem]] = {}
        for char_name, char_value, cnt in rows:
            result.setdefault(char_name, []).append(FacetItem(value=char_value, count=cnt))
        return result

    async def _fetch_regions(self) -> list[RegionFacet]:
        # org counts per region
        org_stmt = (
            select(Organization.region_name, func.count().label("cnt"))
            .where(Organization.region_name.isnot(None))
            .group_by(Organization.region_name)
        )
        org_rows = {row.region_name: row.cnt for row in (await self.db.execute(org_stmt)).all()}

        # coordinates
        coord_stmt = select(RegionCoordinate)
        coords = {
            row.region: row
            for row in (await self.db.execute(coord_stmt)).scalars().all()
            if row.region
        }

        # merge: include all regions that exist in either table
        all_regions = set(org_rows.keys()) | set(coords.keys())
        facets: list[RegionFacet] = []
        for name in sorted(all_regions):
            coord = coords.get(name)
            facets.append(
                RegionFacet(
                    name=name,
                    latitude=coord.latitude_dd if coord else None,
                    longitude=coord.longitude_dd if coord else None,
                    org_count=org_rows.get(name, 0),
                )
            )
        return facets
