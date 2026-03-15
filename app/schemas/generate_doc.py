from datetime import date
from pydantic import BaseModel


class DocumentSource(BaseModel):
    name: str
    supplier: str
    price: float
    date: str


class GenerateDocRequest(BaseModel):
    cte_id: int
    customer: str = "Организация-Заказчик"
    subject: str | None = None
    quantity: int = 1
    unit: str = "шт"
    date_from: date | None = None
    date_to: date | None = None
    sources: list[DocumentSource] | None = None
    nmck: float | None = None
    top_n: int | None = None
    score_threshold: float | None = None


class GenerateDocResponse(BaseModel):
    filename: str
