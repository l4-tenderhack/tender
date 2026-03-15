from pydantic import BaseModel, Field


class ParseJobRequest(BaseModel):
    source: str = Field(..., description="Идентификатор источника данных или URL для парсинга")


class ParseJobResponse(BaseModel):
    job_id: str
    status: str = Field(default="queued")
