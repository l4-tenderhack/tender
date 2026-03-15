from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_parser_service
from app.schemas.parsing import ParseJobRequest, ParseJobResponse
from app.services.parser_service import ParserService

router = APIRouter(prefix="/parsing")


@router.post(
    "/jobs",
    response_model=ParseJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать задачу парсинга",
    tags=["parsing"],
)
async def create_parse_job(
    payload: ParseJobRequest,
    parser_service: ParserService = Depends(get_parser_service),
) -> ParseJobResponse:
    try:
        job_id = await parser_service.create_parse_job(payload.source)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc

    return ParseJobResponse(job_id=job_id, status="queued")
