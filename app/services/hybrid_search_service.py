"""
Hybrid search service using Ollama embeddings + Qdrant REST API via httpx.
Drop-in replacement for SearchService. No qdrant_client dependency.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import asyncpg
import httpx

from app.core.config import Settings
from app.services.search_service import SearchRequest, SearchResult

logger = logging.getLogger(__name__)


class HybridSearchService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._qdrant: Optional[httpx.AsyncClient] = None
        self._ollama: Optional[httpx.AsyncClient] = None
        self._pool: Optional[asyncpg.Pool] = None
        self._dim: Optional[int] = None
        self._connect_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        headers = {"api-key": self.settings.qdrant_api_key} if self.settings.qdrant_api_key else {}
        self._qdrant = httpx.AsyncClient(base_url=self.settings.qdrant_url, headers=headers, timeout=30.0)
        self._ollama = httpx.AsyncClient(timeout=120.0)

        async with self._connect_lock:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    host=self.settings.pg_host,
                    port=self.settings.pg_port,
                    database=self.settings.pg_database,
                    user=self.settings.pg_user,
                    password=self.settings.pg_password,
                    min_size=self.settings.pool_min_size,
                    max_size=self.settings.pool_max_size,
                    timeout=self.settings.pool_timeout,
                )

        # Detect dim
        probe = await self._embed(["probe"])
        self._dim = len(probe[0])
        logger.info(
            "HybridSearchService ready (qdrant=%s collection=%s ollama=%s model=%s dim=%d)",
            self.settings.qdrant_url,
            self.settings.qdrant_collection,
            self.settings.ollama_url,
            self.settings.ollama_model,
            self._dim,
        )

    async def disconnect(self):
        if self._ollama:
            await self._ollama.aclose()
        if self._qdrant:
            await self._qdrant.aclose()
        if self._pool:
            await self._pool.close()
            self._pool = None

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    async def _embed(self, texts: List[str]) -> List[List[float]]:
        resp = await self._ollama.post(
            f"{self.settings.ollama_url}/api/embed",
            json={"model": self.settings.ollama_model, "input": texts},
        )
        if not resp.is_success:
            logger.error("Ollama /api/embed error %d: %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json()["embeddings"]

    async def _embed_one(self, text: str) -> List[float]:
        vecs = await self._embed([text])
        return vecs[0]

    # ------------------------------------------------------------------
    # Qdrant helpers
    # ------------------------------------------------------------------

    def _build_filter(self, request: SearchRequest) -> Optional[Dict]:
        must = []
        if request.category:
            must.append({"key": "category", "match": {"value": request.category}})
        if request.manufacturer:
            must.append({"key": "manufacturer", "match": {"value": request.manufacturer}})
        if request.price_min is not None or request.price_max is not None:
            rng: Dict[str, Any] = {}
            if request.price_min is not None:
                rng["gte"] = request.price_min
            if request.price_max is not None:
                rng["lte"] = request.price_max
            must.append({"key": "price", "range": rng})
        return {"must": must} if must else None

    async def _qdrant_post(self, path: str, body: Dict) -> Any:
        resp = await self._qdrant.post(path, json=body)
        resp.raise_for_status()
        return resp.json()

    async def _qdrant_get(self, path: str) -> Any:
        resp = await self._qdrant.get(path)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Postgres enrichment
    # ------------------------------------------------------------------

    async def _enrich(self, cte_ids: List[str]) -> Dict[str, Any]:
        """Fetch full CTE data from cte_main for the given ids."""
        if not cte_ids or not self._pool:
            return {}
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT cte_id, category, manufacturer, description,
                       COALESCE(price_normalized, 0.0) AS price,
                       COALESCE(region, '') AS region,
                       date, characteristics
                FROM cte_main
                WHERE cte_id = ANY($1::text[])
                """,
                cte_ids,
            )
        return {row["cte_id"]: row for row in rows}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        vec = await self._embed_one(f"query: {request.query}")
        body: Dict[str, Any] = {
            "vector": vec,
            "limit": request.limit,
            "offset": request.offset,
            "with_payload": True,
        }
        f = self._build_filter(request)
        if f:
            body["filter"] = f

        data = await self._qdrant_post(
            f"/collections/{self.settings.qdrant_collection}/points/search",
            body,
        )

        # Filter by score threshold first, collect cte_ids
        hits = []
        for point in data.get("result", []):
            score = float(point.get("score") or 0)
            if score < request.score_threshold:
                continue
            p = point.get("payload") or {}
            cte_id = str(p.get("cte_id", ""))
            hits.append((cte_id, score))

        # Enrich from Postgres
        enriched = await self._enrich([cte_id for cte_id, _ in hits])

        out = []
        for cte_id, score in hits:
            row = enriched.get(cte_id)
            if row:
                try:
                    chars = (
                        json.loads(row["characteristics"])
                        if isinstance(row["characteristics"], str)
                        else dict(row["characteristics"] or {})
                    )
                except Exception:
                    chars = {}
                out.append(SearchResult(
                    cte_id=cte_id,
                    category=str(row["category"] or ""),
                    manufacturer=str(row["manufacturer"] or ""),
                    description=str(row["description"] or ""),
                    price=float(row["price"] or 0),
                    region=str(row["region"] or ""),
                    date=str(row["date"]) if row["date"] else None,
                    characteristics=chars,
                    score=score,
                    category_boost=1.0,
                ))
            else:
                # cte not in cte_main — return minimal result
                out.append(SearchResult(
                    cte_id=cte_id,
                    category="", manufacturer="", description="",
                    price=0.0, region="", date=None,
                    characteristics={}, score=score, category_boost=1.0,
                ))
        return out

    async def get_facets(self, request: SearchRequest, limit: int = 20) -> Dict[str, Any]:
        cat_counts: Dict[str, int] = {}
        mfr_counts: Dict[str, int] = {}
        offset = None

        while True:
            body: Dict[str, Any] = {"limit": 1000, "with_payload": ["category", "manufacturer"]}
            if offset:
                body["offset"] = offset
            data = await self._qdrant_post(
                f"/collections/{self.settings.qdrant_collection}/points/scroll",
                body,
            )
            result = data.get("result", {})
            for point in result.get("points", []):
                p = point.get("payload") or {}
                cat = p.get("category", "")
                mfr = p.get("manufacturer", "")
                if cat:
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1
                if mfr:
                    mfr_counts[mfr] = mfr_counts.get(mfr, 0) + 1
            offset = result.get("next_page_offset")
            if not offset:
                break

        top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:limit]
        top_mfrs = sorted(mfr_counts.items(), key=lambda x: -x[1])[:limit]
        return {
            "category": [{"value": k, "count": v} for k, v in top_cats],
            "manufacturer": [{"value": k, "count": v} for k, v in top_mfrs],
            "characteristics": {},
        }

    async def get_statistics(self) -> Dict[str, Any]:
        data = await self._qdrant_get(f"/collections/{self.settings.qdrant_collection}")
        result = data.get("result", {})
        return {
            "total_documents": result.get("vectors_count"),
            "unique_categories": None,
            "unique_manufacturers": None,
            "table_size": None,
            "top_characteristics": [],
        }

    async def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        data = await self._qdrant_post(
            f"/collections/{self.settings.qdrant_collection}/points/scroll",
            {"limit": 500, "with_payload": ["category", "manufacturer"]},
        )
        pl = prefix.lower()
        suggestions = []
        seen: set = set()
        for point in data.get("result", {}).get("points", []):
            p = point.get("payload") or {}
            for field in ("category", "manufacturer"):
                val = p.get(field, "")
                if val and val.lower().startswith(pl) and val not in seen:
                    suggestions.append(val)
                    seen.add(val)
                    if len(suggestions) >= limit:
                        return suggestions
        return suggestions
