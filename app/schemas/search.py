from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Строка поискового запроса")
    category: str | None = Field(None, description="Фильтр по категории")
    manufacturer: str | None = Field(None, description="Фильтр по производителю")
    price_min: float | None = Field(None, ge=0, description="Минимальная цена")
    price_max: float | None = Field(None, ge=0, description="Максимальная цена")
    characteristics: dict[str, str] | None = Field(
        None, description="Фильтры по характеристикам (ключ:значение)"
    )
    limit: int = Field(20, ge=1, le=100, description="Количество результатов")
    offset: int = Field(0, ge=0, description="Смещение для пагинации")
    score_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Минимальный порог схожести (только для гибридного поиска)")


class SearchResult(BaseModel):
    cte_id: str
    category: str
    manufacturer: str
    description: str
    price: float
    characteristics: dict[str, Any]
    score: float
    category_boost: float
    region: str = ""
    date: Optional[str] = None


class SearchResponse(BaseModel):
    total: int
    execution_time_ms: float
    results: list[SearchResult]
    available_characteristics: dict[str, list[str]] = Field(default_factory=dict)


class FacetItem(BaseModel):
    value: str
    count: int


class RegionFacet(BaseModel):
    name: str
    latitude: float | None = None
    longitude: float | None = None
    org_count: int = 0


class FacetsResponse(BaseModel):
    category: list[FacetItem] = Field(default_factory=list)
    manufacturer: list[FacetItem] = Field(default_factory=list)
    characteristics: dict[str, list[FacetItem]] = Field(default_factory=dict)
    regions: list[RegionFacet] = Field(default_factory=list)


class SuggestResponse(BaseModel):
    suggestions: list[str]
