"""
PostgreSQL search engine with full-text search.
Uses tsvector/tsquery, GIN indexes, asyncpg.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import asyncpg

from app.core.config import Settings
from app.services.normalizer import TextNormalizer

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    query: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    characteristics: Optional[Dict[str, str]] = None
    limit: int = 20
    offset: int = 0
    score_threshold: float = 0.6


@dataclass
class SearchResult:
    cte_id: str
    category: str
    manufacturer: str
    description: str
    price: float
    region: str
    date: Optional[str]
    characteristics: Dict
    score: float
    category_boost: float


class SearchService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.normalizer = TextNormalizer()
        self.pool: Optional[asyncpg.Pool] = None
        self._connect_lock = asyncio.Lock()

    async def connect(self):
        if self.pool is not None:
            return
        async with self._connect_lock:
            if self.pool is None:
                logger.info(
                    "Connecting to PostgreSQL: host=%s port=%s database=%s user=%s pool_min=%s pool_max=%s timeout=%s",
                    self.settings.pg_host,
                    self.settings.pg_port,
                    self.settings.pg_database,
                    self.settings.pg_user,
                    self.settings.pool_min_size,
                    self.settings.pool_max_size,
                    self.settings.pool_timeout,
                )
                try:
                    self.pool = await asyncpg.create_pool(
                        host=self.settings.pg_host,
                        port=self.settings.pg_port,
                        database=self.settings.pg_database,
                        user=self.settings.pg_user,
                        password=self.settings.pg_password,
                        min_size=self.settings.pool_min_size,
                        max_size=self.settings.pool_max_size,
                        timeout=self.settings.pool_timeout,
                    )
                    logger.info("Successfully connected to PostgreSQL")
                except Exception as e:
                    logger.error(
                        "Failed to connect to PostgreSQL at %s:%s/%s — %s: %s",
                        self.settings.pg_host,
                        self.settings.pg_port,
                        self.settings.pg_database,
                        type(e).__name__,
                        e,
                    )
                    raise

    def _get_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError(
                "SearchService not connected. Call connect() during application startup."
            )
        return self.pool

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    def _build_tsquery(self, query: str) -> str:
        query = query.lower().strip()
        terms = query.split()
        if not terms:
            return "''"
        processed = []
        for term in terms:
            term = term.replace("'", "''")
            processed.append(f"{term}:*" if len(term) >= 3 else term)
        return f"'{' | '.join(processed)}'"

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        tsquery = self._build_tsquery(request.query)

        sql = f"""
            SELECT
                cte_id, category, manufacturer, description,
                COALESCE(price_normalized, 0.0) as price,
                COALESCE(region, '') as region,
                date, characteristics,
                ts_rank_cd(search_vector, query, 32) * (1.0 + category_boost / 10) as score,
                category_boost
            FROM cte_main, to_tsquery('russian', {tsquery}) query
            WHERE search_vector @@ query
        """

        params: list = []
        where: list = []

        if request.category:
            where.append("category = $%d" % (len(params) + 1))
            params.append(request.category)
        if request.manufacturer:
            where.append("manufacturer = $%d" % (len(params) + 1))
            params.append(request.manufacturer)
        if request.price_min is not None:
            where.append("price_normalized >= $%d" % (len(params) + 1))
            params.append(request.price_min)
        if request.price_max is not None:
            where.append("price_normalized <= $%d" % (len(params) + 1))
            params.append(request.price_max)
        if request.characteristics:
            for char_name, char_value in request.characteristics.items():
                where.append(
                    """
                    EXISTS (
                        SELECT 1 FROM cte_characteristics c
                        WHERE c.cte_id = cte_main.cte_id
                        AND c.char_name = $%d AND c.char_value ILIKE $%d
                    )
                """
                    % (len(params) + 1, len(params) + 2)
                )
                params.extend([char_name, f"%{char_value}%"])

        if where:
            sql += " AND " + " AND ".join(where)

        sql += f" ORDER BY score DESC, category_boost DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([request.limit, request.offset])

        async with self._get_pool().acquire() as conn:
            rows = await conn.fetch(sql, *params)

        results = []
        for row in rows:
            characteristics: Dict[str, Any] = {}
            if row["characteristics"]:
                try:
                    characteristics = (
                        json.loads(row["characteristics"])
                        if isinstance(row["characteristics"], str)
                        else dict(row["characteristics"])
                    )
                except Exception:
                    pass
            results.append(
                SearchResult(
                    cte_id=row["cte_id"],
                    category=row["category"],
                    manufacturer=row["manufacturer"],
                    description=row["description"],
                    price=float(row["price"] or 0),
                    region=row["region"] or "",
                    date=str(row["date"]) if row["date"] else None,
                    characteristics=characteristics,
                    score=float(row["score"] or 0),
                    category_boost=float(row["category_boost"] or 1.0),
                )
            )
        return results

    async def get_facets(self, request: SearchRequest, limit: int = 20) -> Dict[str, Any]:
        async with self._get_pool().acquire() as conn:
            cat_rows = await conn.fetch(
                "SELECT category, COUNT(*) as cnt FROM cte_main GROUP BY category ORDER BY cnt DESC LIMIT $1",
                limit,
            )
            mfr_rows = await conn.fetch(
                "SELECT manufacturer, COUNT(*) as cnt FROM cte_main GROUP BY manufacturer ORDER BY cnt DESC LIMIT $1",
                limit,
            )
            char_rows = await conn.fetch(
                """
                SELECT char_name, char_value, count FROM mv_characteristics_stats
                WHERE char_name = ANY($1) ORDER BY char_name, count DESC LIMIT $2
            """,
                ["материал", "цвет", "назначение", "тип", "размер", "вид товаров"],
                limit * 5,
            )

        char_facets: Dict[str, list] = {}
        for row in char_rows:
            char_facets.setdefault(row[0], []).append({"value": row[1], "count": row[2]})

        return {
            "category": [{"value": r[0], "count": r[1]} for r in cat_rows],
            "manufacturer": [{"value": r[0], "count": r[1]} for r in mfr_rows],
            "characteristics": char_facets,
        }

    async def get_statistics(self) -> Dict[str, Any]:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM v_search_stats")
            top_chars = await conn.fetch("""
                SELECT char_name, SUM(count) as cnt FROM mv_characteristics_stats
                GROUP BY char_name ORDER BY cnt DESC LIMIT 20
            """)
        return {
            "total_documents": row["total_documents"],
            "unique_categories": row["unique_categories"],
            "unique_manufacturers": row["unique_manufacturers"],
            "table_size": row["table_size"],
            "top_characteristics": [{"name": r[0], "count": r[1]} for r in top_chars],
        }

    async def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        async with self._get_pool().acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM cte_main WHERE category ILIKE $1 || '%' ORDER BY category LIMIT $2",
                prefix,
                limit,
            )
            suggestions = [r[0] for r in rows]
            if len(suggestions) < limit:
                rows = await conn.fetch(
                    "SELECT DISTINCT manufacturer FROM cte_main WHERE manufacturer ILIKE $1 || '%' ORDER BY manufacturer LIMIT $2",
                    prefix,
                    limit - len(suggestions),
                )
                suggestions.extend(r[0] for r in rows)
        return suggestions

    async def get_total_count(self) -> int:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) FROM cte_main")
            return row[0]
