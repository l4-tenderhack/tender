from __future__ import annotations

import math
import statistics
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.procurement import Contract, ContractItem, CteCatalog, CteMain, Organization
from app.schemas.nmck import DbContractPrice, ManualContractInput, ManualNmckResponse, SearchNmckResponse

if TYPE_CHECKING:
    from app.services.cte_search_service import CteSearchService

MIN_SAMPLE_SIZE = 3
CV_HOMOGENEITY_THRESHOLD = Decimal("33")
IQR_MULTIPLIER = 1.5
T_95_LOOKUP = {
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    15: 2.131,
    20: 2.086,
    30: 2.042,
}


def _t_value_95(n: int) -> float:
    if n <= 2:
        return 4.303
    for threshold in sorted(T_95_LOOKUP.keys(), reverse=True):
        if n >= threshold:
            return T_95_LOOKUP[threshold]
    return T_95_LOOKUP[3]


def _quantile(sorted_data: list[float], q: float) -> float:
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    idx = q * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_data[-1]
    frac = idx - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


def _to_decimal(value: float, places: int = 5) -> Decimal:
    quantize_str = Decimal(10) ** -places
    return Decimal(str(value)).quantize(quantize_str, rounding=ROUND_HALF_UP)


class NmckInsufficientDataError(Exception):
    pass


class NmckService:

    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings

    # ------------------------------------------------------------------
    # Search-based НМЦК (existing)
    # ------------------------------------------------------------------

    async def calculate_by_search(
        self,
        cte_id: int,
        top_n: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        region: str | None = None,
        inn: str | None = None,
        score_threshold: float | None = None,
        *,
        search_service: CteSearchService,
    ) -> SearchNmckResponse:
        cte_name = await self._get_cte_name(cte_id)
        if cte_name is None:
            raise NmckInsufficientDataError(f"КТЕ {cte_id} не найдена в каталоге")

        query_lower = cte_name.lower()
        n_val = top_n if top_n is not None else 5
        search_result = await search_service.search(
            query=query_lower,
            n=n_val,
            date_from=date_from,
            date_to=date_to,
            region=region,
            inn=inn,
            score_threshold=score_threshold,
        )

        matched_cte_ids: list[int] = []
        matched_cte_names: list[str] = []
        for m in search_result.matched_ctes:
            try:
                mid = int(m.cte_id)
                matched_cte_ids.append(mid)
                matched_cte_names.append(m.cte_name)
            except (ValueError, TypeError):
                continue

        if cte_id not in matched_cte_ids:
            matched_cte_ids.insert(0, cte_id)
            matched_cte_names.insert(0, cte_name)

        prices_by_cte_raw = await self._collect_prices_by_cte(
            matched_cte_ids, date_from=date_from, date_to=date_to,
        )
        prices_all: list[float] = []
        for v in prices_by_cte_raw.values():
            prices_all.extend(v)

        prices_by_cte_serializable = {str(k): v for k, v in prices_by_cte_raw.items()}

        stats = self._compute_nmck(prices_all, warnings=[])

        return SearchNmckResponse(
            cte_id=cte_id,
            cte_name=cte_name,
            search_query=query_lower,
            matched_cte_ids=matched_cte_ids,
            matched_cte_names=matched_cte_names,
            prices_by_cte=prices_by_cte_serializable,
            contracts=search_result.contracts,
            total_contracts=search_result.total_contracts,
            **stats,
        )

    # ------------------------------------------------------------------
    # Manual НМЦК (new)
    # ------------------------------------------------------------------

    async def calculate_manual(
        self,
        cte_id: int,
        manual_contracts: list[ManualContractInput],
    ) -> SearchNmckResponse:
        """Fetch existing DB contracts for cte_id, merge with user-provided,
        then compute НМЦК on the combined set."""
        cte_name = await self._get_cte_name(cte_id)

        db_contracts = await self._fetch_db_contracts(cte_id)
        db_prices = [c.unit_price for c in db_contracts]
        manual_prices = [mc.unit_price for mc in manual_contracts]
        combined = db_prices + manual_prices

        warnings: list[str] = []
        if len(db_prices) > 0:
            warnings.append(
                f"Найдено {len(db_prices)} существующих контрактов в БД для cte_id={cte_id}."
            )

        stats = self._compute_nmck(combined, warnings=warnings)

        # Map db_contracts and manual_contracts to ContractOut
        from app.schemas.cte_search import ContractItemOut, ContractOut

        final_contracts: list[ContractOut] = []

        # 1. Add DB contracts
        for dbc in db_contracts:
            final_contracts.append(
                ContractOut(
                    contract_id=dbc.contract_id or 0,
                    contract_external_id=dbc.contract_id or 0,
                    purchase_name=cte_name or "Контракт из БД",
                    signed_at=dbc.signed_at.isoformat() if dbc.signed_at else None,
                    buyer_inn=None,
                    buyer_region=None,
                    supplier_inn=dbc.supplier_inn,
                    items=[
                        ContractItemOut(
                            cte_id=cte_id,
                            cte_position_name=cte_name,
                            unit_price=Decimal(str(dbc.unit_price)),
                            quantity=Decimal("1"),
                            unit_name="шт",
                        )
                    ],
                )
            )

        # 2. Add manual contracts
        for i, mc in enumerate(manual_contracts):
            final_contracts.append(
                ContractOut(
                    contract_id=-(i + 1),  # Negative IDs for manual
                    contract_external_id=-(i + 1),
                    purchase_name=cte_name or "Ручной ввод",
                    signed_at=mc.signed_at.isoformat() if mc.signed_at else None,
                    buyer_inn=None,
                    buyer_region=None,
                    supplier_inn=mc.supplier_inn,
                    items=[
                        ContractItemOut(
                            cte_id=cte_id,
                            cte_position_name=cte_name,
                            unit_price=Decimal(str(mc.unit_price)),
                            quantity=Decimal("1"),
                            unit_name="шт",
                        )
                    ],
                )
            )

        return SearchNmckResponse(
            cte_id=cte_id,
            cte_name=cte_name,
            search_query="manual",
            matched_cte_ids=[cte_id],
            matched_cte_names=[cte_name] if cte_name else [],
            prices_by_cte={str(cte_id): combined},
            contracts=final_contracts,
            total_contracts=len(final_contracts),
            **stats,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_db_contracts(self, cte_id: int) -> list[DbContractPrice]:
        stmt = (
            select(
                ContractItem.contract_id,
                ContractItem.unit_price,
                Contract.signed_at,
                Organization.inn.label("supplier_inn"),
            )
            .join(Contract, ContractItem.contract_id == Contract.id)
            .outerjoin(Organization, Contract.supplier_org_id == Organization.id)
            .where(ContractItem.cte_id == cte_id)
            .where(ContractItem.unit_price.isnot(None))
            .where(ContractItem.unit_price > 0)
        )
        result = await self.db_session.execute(stmt)
        return [
            DbContractPrice(
                contract_id=row.contract_id,
                unit_price=float(row.unit_price),
                signed_at=row.signed_at.date() if row.signed_at else None,
                supplier_inn=row.supplier_inn,
            )
            for row in result.all()
        ]

    async def _get_cte_name(self, cte_id: int) -> str | None:
        result = await self.db_session.execute(
            select(CteMain.description).where(CteMain.cte_id == str(cte_id))
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        result = await self.db_session.execute(
            select(CteCatalog.cte_name).where(CteCatalog.cte_id == cte_id)
        )
        return result.scalar_one_or_none()

    async def _collect_prices_by_cte(
        self,
        cte_ids: list[int],
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[int, list[float]]:
        stmt = (
            select(ContractItem.cte_id, ContractItem.unit_price)
            .where(ContractItem.cte_id.in_(cte_ids))
            .where(ContractItem.unit_price.isnot(None))
            .where(ContractItem.unit_price > 0)
        )
        if date_from is not None or date_to is not None:
            stmt = stmt.join(Contract, ContractItem.contract_id == Contract.id)
            if date_from is not None:
                stmt = stmt.where(Contract.signed_at >= date_from)
            if date_to is not None:
                stmt = stmt.where(Contract.signed_at <= date_to)

        result = await self.db_session.execute(stmt)
        rows = result.all()
        prices: dict[int, list[float]] = {cid: [] for cid in cte_ids}
        for row_cte_id, unit_price in rows:
            prices[int(row_cte_id)].append(float(unit_price))
        return prices

    def _filter_outliers_iqr(
        self, prices: list[float]
    ) -> tuple[list[float], int]:
        if len(prices) < 4:
            return prices, 0

        sorted_p = sorted(prices)
        q1 = _quantile(sorted_p, 0.25)
        q3 = _quantile(sorted_p, 0.75)
        iqr = q3 - q1

        lower = q1 - IQR_MULTIPLIER * iqr
        upper = q3 + IQR_MULTIPLIER * iqr

        filtered = [p for p in sorted_p if lower <= p <= upper]
        removed = len(prices) - len(filtered)
        return filtered, removed

    def _compute_nmck(
        self,
        prices_raw: list[float],
        warnings: list[str],
    ) -> dict[str, Any]:
        if not prices_raw:
            raise NmckInsufficientDataError("Не найдены данные о ценах для указанных КТЕ")

        sample_size_total = len(prices_raw)

        filtered, outliers_removed = self._filter_outliers_iqr(prices_raw)
        if len(filtered) < MIN_SAMPLE_SIZE:
            warnings.append(
                f"После фильтрации IQR осталось только {len(filtered)} цен; "
                "используется нефильтрованная выборка."
            )
            filtered = prices_raw
            outliers_removed = 0

        sample_size_filtered = len(filtered)

        if sample_size_filtered < MIN_SAMPLE_SIZE:
            raise NmckInsufficientDataError(
                f"Недостаточно данных о ценах: найдено {sample_size_filtered}, "
                f"минимально необходимо {MIN_SAMPLE_SIZE}."
            )

        mean_val = statistics.mean(filtered)
        std_dev_val = statistics.pstdev(filtered) if len(filtered) > 1 else 0.0
        cv_val = (std_dev_val / mean_val * 100) if mean_val else 0.0
        is_homogeneous = Decimal(str(cv_val)) <= CV_HOMOGENEITY_THRESHOLD
        if not is_homogeneous:
            warnings.append(
                f"Выборка неоднородна (КВ={cv_val:.1f}% > 33%). "
                "Рекомендуется сузить критерии поиска."
            )

        median_val = statistics.median(filtered)
        price_min = min(filtered)
        price_max = max(filtered)

        t = _t_value_95(sample_size_filtered)
        margin = (
            t * std_dev_val / math.sqrt(sample_size_filtered)
            if sample_size_filtered > 1
            else 0.0
        )
        ci_low = median_val - margin
        ci_high = median_val + margin

        return {
            "nmck_per_unit": _to_decimal(median_val),
            "price_min": _to_decimal(price_min),
            "price_max": _to_decimal(price_max),
            "mean_price": _to_decimal(mean_val),
            "median_price": _to_decimal(median_val),
            "std_dev": _to_decimal(std_dev_val),
            "coefficient_of_variation": _to_decimal(cv_val, places=2),
            "is_homogeneous": bool(is_homogeneous),
            "confidence_interval_low": _to_decimal(ci_low),
            "confidence_interval_high": _to_decimal(ci_high),
            "sample_size_total": sample_size_total,
            "sample_size_filtered": sample_size_filtered,
            "outliers_removed": outliers_removed,
            "warnings": warnings,
            "method": "comparable_market_prices",
        }
