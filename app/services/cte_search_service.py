from __future__ import annotations

import json
import logging
import re
import time
from datetime import date

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models.procurement import Contract, ContractItem, CteMain, Organization

logger = logging.getLogger(__name__)
from app.schemas.cte_search import (
    ContractItemOut,
    ContractOut,
    CteMatch,
    CteSearchResponse,
)


_MAX_CONTRACTS = 50

_OVERCOLLECT_THRESHOLD = 0.55
_OVERCOLLECT_FACTOR = 5
_VECTOR_WEIGHT = 0.6
_NUM_IMPORTANCE = 2.0
_STEM_LEN = 4

_NUM_RE = re.compile(r"\d+")
_WORD_RE = re.compile(r"[а-яёa-z]+")
_SPLIT_NUM_ALPHA = re.compile(r"(\d)([а-яёa-z])")
_SPLIT_ALPHA_NUM = re.compile(r"([а-яёa-z])(\d)")

# Color words for characteristic matching
_COLOR_RE = re.compile(
    r"\b(черн\w*|бел\w*|красн\w*|син\w*|зелен\w*|серы\w*|серого|желт\w*|голуб\w*|розов\w*|оранж\w*|фиолет\w*|коричнев\w*)\b",
    re.I,
)


def _tokenize(text: str) -> tuple[set[str], set[str]]:
    t = text.lower()
    t = _SPLIT_NUM_ALPHA.sub(r"\1 \2", t)
    t = _SPLIT_ALPHA_NUM.sub(r"\1 \2", t)
    return set(_NUM_RE.findall(t)), set(_WORD_RE.findall(t))


def _stem(word: str) -> str:
    return word[:_STEM_LEN] if len(word) > _STEM_LEN else word


def _stems_match(a: str, b: str) -> bool:
    sa, sb = _stem(a), _stem(b)
    return sa == sb or sa.startswith(sb) or sb.startswith(sa)


def _keyword_coverage(query: str, candidate: str) -> float:
    """Fraction of query tokens (numbers + word stems) found in candidate."""
    q_nums, q_words = _tokenize(query)
    c_nums, c_words = _tokenize(candidate)

    significant = {w for w in q_words if len(w) >= 3}

    num_matched = len(q_nums & c_nums)
    word_matched = sum(
        1 for qw in significant if any(_stems_match(qw, cw) for cw in c_words)
    )

    total = len(q_nums) * _NUM_IMPORTANCE + len(significant)
    if total == 0:
        return 1.0
    return (num_matched * _NUM_IMPORTANCE + word_matched) / total


def _meta_boost(query: str, match: CteMatch) -> float:
    """Lightweight metadata bonus: check if query words appear in category,
    manufacturer, or characteristics. Returns 0..1."""
    q_lower = query.lower()
    _, q_words = _tokenize(q_lower)
    significant = {w for w in q_words if len(w) >= 3}
    if not significant:
        return 0.0

    bonus = 0.0
    parts = 0

    # Category match
    cat = (match.category or "").lower()
    if cat:
        _, cat_words = _tokenize(cat)
        if cat_words:
            cat_hit = sum(1 for qw in significant if any(_stems_match(qw, cw) for cw in cat_words))
            bonus += cat_hit / len(significant)
            parts += 1

    # Manufacturer match — check if any query token stem-matches manufacturer words
    mfr = (match.manufacturer or "").lower()
    if mfr:
        _, mfr_words = _tokenize(mfr)
        mfr_sig = {w for w in mfr_words if len(w) >= 3}
        if mfr_sig:
            mfr_hit = sum(1 for qw in significant if any(_stems_match(qw, mw) for mw in mfr_sig))
            if mfr_hit > 0:
                bonus += mfr_hit / len(significant)
                parts += 1

    # Color / characteristic match
    q_colors = set(_COLOR_RE.findall(q_lower))
    if q_colors:
        chars_text = json.dumps(match.characteristics, ensure_ascii=False).lower() if match.characteristics else ""
        full_text = f"{match.cte_name.lower()} {(match.description or '').lower()} {chars_text}"
        color_hit = sum(1 for c in q_colors if _stem(c.lower()) in full_text)
        bonus += color_hit / len(q_colors)
        parts += 1

    return bonus / max(parts, 1)


def _aggregate_characteristics(matches: list[CteMatch]) -> dict[str, list[str]]:
    agg: dict[str, set[str]] = {}
    for m in matches:
        for key, val in m.characteristics.items():
            sval = str(val).strip()
            if sval:
                agg.setdefault(key, set()).add(sval)
    return {k: sorted(v) for k, v in sorted(agg.items())}


def _rerank_pass1(query: str, matches: list[CteMatch], n: int) -> list[CteMatch]:
    """First pass: vector + keyword coverage. Cheap, no metadata needed."""
    scored: list[tuple[float, CteMatch]] = []
    for m in matches:
        kw = _keyword_coverage(query, m.cte_name)
        final = _VECTOR_WEIGHT * m.score + (1 - _VECTOR_WEIGHT) * kw
        scored.append((round(final, 6), m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:n]]


def _rerank_pass2(query: str, matches: list[CteMatch], n: int) -> list[CteMatch]:
    """Second pass: boost by metadata (category, manufacturer, chars).
    Applied after enrichment on a small set (2*n → n)."""
    scored: list[tuple[float, CteMatch]] = []
    for m in matches:
        kw = _keyword_coverage(query, m.cte_name)
        mb = _meta_boost(query, m)
        # 50% vector, 25% keyword, 25% metadata
        final = 0.50 * m.score + 0.25 * kw + 0.25 * mb
        scored.append((round(final, 6), m))
    scored.sort(key=lambda x: x[0], reverse=True)
    for final_score, m in scored:
        m.score = final_score
    return [m for _, m in scored[:n]]


class CteSearchService:

    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db = db_session
        self.settings = settings

    async def search(
        self,
        query: str,
        n: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        region: str | None = None,
        inn: str | None = None,
        score_threshold: float | None = None,
    ) -> CteSearchResponse:
        t0 = time.perf_counter()
        query = query.lower()
        n_val = n if n is not None else 10
        qdrant_threshold = (
            score_threshold
            if score_threshold is not None
            else self.settings.cte_search_score_threshold
        )

        t_embed = time.perf_counter()
        embedding = await self._embed(query)
        logger.info("embed: %.0f ms", (time.perf_counter() - t_embed) * 1000)

        # 1. Overcollect from Qdrant
        overcollect_limit = n_val * _OVERCOLLECT_FACTOR
        t_qdrant = time.perf_counter()
        raw_matches = await self._search_qdrant(
            embedding,
            limit=overcollect_limit,
            score_threshold=qdrant_threshold,
        )
        logger.info("qdrant: %.0f ms", (time.perf_counter() - t_qdrant) * 1000)

        # 2. First-pass rerank (cheap: vector + keyword on cte_name) → 2*n
        shortlist = _rerank_pass1(query, raw_matches, n_val * 2)

        # 3. Enrich only shortlist from PG (single query, ~20 items)
        t_enrich = time.perf_counter()
        shortlist = await self._enrich_matches(shortlist)
        logger.info("enrich: %.0f ms", (time.perf_counter() - t_enrich) * 1000)

        # 4. Second-pass rerank with metadata boost → n
        matches = _rerank_pass2(query, shortlist, n_val)

        cte_ids = [int(m.cte_id) for m in matches]

        if not cte_ids:
            return CteSearchResponse(
                query=query, matched_ctes=matches, contracts=[], total_contracts=0,
                elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
            )

        has_filters = any(v is not None for v in (date_from, date_to, region, inn))

        t_contracts = time.perf_counter()
        contracts = await self._get_contracts(
            cte_ids,
            date_from=date_from,
            date_to=date_to,
            region=region,
            inn=inn,
        )
        logger.info("contracts: %.0f ms (%d rows)", (time.perf_counter() - t_contracts) * 1000, len(contracts))

        if has_filters:
            cte_ids_with_contracts: set[str] = set()
            for c in contracts:
                for item in c.items:
                    cte_ids_with_contracts.add(str(item.cte_id))
            matches = [m for m in matches if m.cte_id in cte_ids_with_contracts]

        return CteSearchResponse(
            query=query,
            matched_ctes=matches,
            contracts=contracts,
            total_contracts=len(contracts),
            available_characteristics=_aggregate_characteristics(matches),
            elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
        )

    # ------------------------------------------------------------------
    # PostgreSQL enrichment
    # ------------------------------------------------------------------

    async def _enrich_matches(self, matches: list[CteMatch]) -> list[CteMatch]:
        cte_ids = [m.cte_id for m in matches]
        if not cte_ids:
            return matches

        stmt = select(CteMain).where(CteMain.cte_id.in_(cte_ids))
        result = await self.db.execute(stmt)
        rows = {row.cte_id: row for row in result.scalars().all()}

        for m in matches:
            row = rows.get(m.cte_id)
            if not row:
                continue
            chars = row.characteristics
            if isinstance(chars, str):
                try:
                    chars = json.loads(chars)
                except Exception:
                    chars = {}
            m.category = str(row.category or "")
            m.manufacturer = str(row.manufacturer or "")
            m.description = str(row.description or "")
            m.price = float(row.price_normalized or 0)
            m.region = str(row.region or "")
            m.characteristics = dict(chars) if chars else {}
            m.category_boost = 1.0

        return matches

    # ------------------------------------------------------------------
    # Embedding & Qdrant
    # ------------------------------------------------------------------

    async def _embed(self, text: str) -> list[float]:
        url = f"{self.settings.ollama_base_url}/api/embed"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                json={"model": self.settings.ollama_model, "input": [text]},
            )
            resp.raise_for_status()
            return resp.json()["embeddings"][0]

    async def _search_qdrant(
        self,
        vector: list[float],
        limit: int,
        score_threshold: float | None = None,
    ) -> list[CteMatch]:
        threshold = score_threshold if score_threshold is not None else self.settings.cte_search_score_threshold
        url = (
            f"{self.settings.qdrant_url}"
            f"/collections/{self.settings.qdrant_collection}/points/query"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                json={
                    "query": vector,
                    "limit": limit,
                    "with_payload": True,
                    "score_threshold": threshold,
                },
            )
            resp.raise_for_status()

        points = resp.json().get("result", {}).get("points", [])
        results: list[CteMatch] = []
        for pt in points:
            payload = pt.get("payload", {})
            results.append(
                CteMatch(
                    cte_id=str(payload.get("cte_id", "")),
                    cte_name=payload.get("name", ""),
                    score=pt.get("score", 0.0),
                )
            )
        return results

    # ------------------------------------------------------------------
    # Contracts
    # ------------------------------------------------------------------

    async def _get_contracts(
        self,
        cte_ids: list[int],
        date_from: date | None = None,
        date_to: date | None = None,
        region: str | None = None,
        inn: str | None = None,
    ) -> list[ContractOut]:
        stmt = (
            select(Contract)
            .join(ContractItem, Contract.id == ContractItem.contract_id)
            .where(ContractItem.cte_id.in_(cte_ids))
            .options(
                selectinload(Contract.items),
                selectinload(Contract.buyer_organization),
                selectinload(Contract.supplier_organization),
            )
        )

        if date_from is not None:
            stmt = stmt.where(Contract.signed_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Contract.signed_at <= date_to)

        if region is not None:
            regions = [r.strip() for r in region.split(",") if r.strip()]
            stmt = stmt.join(
                Organization, Contract.buyer_org_id == Organization.id
            ).where(or_(*[Organization.region_name.ilike(f"%{r}%") for r in regions]))

        if inn is not None:
            buyer_org = Organization.__table__.alias("buyer_org_inn")
            supplier_org = Organization.__table__.alias("supplier_org_inn")
            stmt = stmt.outerjoin(
                buyer_org, Contract.buyer_org_id == buyer_org.c.id
            ).outerjoin(
                supplier_org, Contract.supplier_org_id == supplier_org.c.id
            ).where(
                (buyer_org.c.inn == inn) | (supplier_org.c.inn == inn)
            )

        result = await self.db.execute(stmt.limit(_MAX_CONTRACTS).distinct())
        contracts = result.scalars().unique().all()

        cte_id_set = set(cte_ids)
        out: list[ContractOut] = []
        for c in contracts:
            relevant_items = [
                ContractItemOut(
                    cte_id=item.cte_id,
                    cte_position_name=item.cte_position_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    unit_name=item.unit_name,
                )
                for item in c.items
                if item.cte_id in cte_id_set
            ]
            buyer = c.buyer_organization
            supplier = c.supplier_organization
            out.append(
                ContractOut(
                    contract_id=c.id,
                    contract_external_id=c.contract_external_id,
                    purchase_name=c.purchase_name,
                    signed_at=c.signed_at.isoformat() if c.signed_at else None,
                    buyer_inn=buyer.inn if buyer else None,
                    buyer_region=buyer.region_name if buyer else None,
                    supplier_inn=supplier.inn if supplier else None,
                    items=relevant_items,
                )
            )
        return out
