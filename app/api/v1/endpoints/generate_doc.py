import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.dependencies import get_doc_service, get_nmck_service, get_cte_search_service
from app.schemas.generate_doc import GenerateDocRequest
from app.services.doc_service import DocService
from app.services.nmck_service import NmckService
from app.services.cte_search_service import CteSearchService

router = APIRouter(prefix="/generate_doc")


@router.post(
    "",
    summary="Сгенерировать документ НМЦК",
    tags=["generate_doc"],
    response_class=FileResponse,
)
async def generate_doc(
    payload: GenerateDocRequest,
    background_tasks: BackgroundTasks,
    doc_service: DocService = Depends(get_doc_service),
    nmck_service: NmckService = Depends(get_nmck_service),
    search_service: CteSearchService = Depends(get_cte_search_service),
) -> FileResponse:
    # 1. Fetch real analytics data if sources are not provided
    nmck_data = None
    if not payload.sources:
        try:
            nmck_data = await nmck_service.calculate_by_search(
                cte_id=payload.cte_id,
                date_from=payload.date_from,
                date_to=payload.date_to,
                top_n=payload.top_n,
                score_threshold=payload.score_threshold,
                search_service=search_service,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to fetch data for report: {str(exc)}",
            ) from exc

    # 2. Prepare data for the template
    template_data = payload.model_dump()
    
    if payload.nmck is not None:
        template_data["nmck"] = float(payload.nmck)
    elif nmck_data:
        template_data["nmck"] = float(nmck_data.nmck_per_unit)
    else:
        # Fallback if no nmck provided and no auto-fetch (sources exists)
        template_data["nmck"] = sum(s.price for s in payload.sources) / len(payload.sources) if payload.sources else 0
    
    # Map real contracts to DocumentSource format
    real_sources = []
    
    if nmck_data:
        for contract in nmck_data.contracts:
            for item in contract.items:
                source = {
                    "supplier": contract.supplier_inn or "Не указан",
                    "date": contract.signed_at or "Не указана",
                    "name": item.cte_position_name,
                    "price": float(item.unit_price)
                }
                real_sources.append(source)

    
    # Use real sources if found, otherwise fallback to payload sources if any
    if not real_sources and payload.sources:
        template_data["sources"] = [s.model_dump() for s in payload.sources]
    else:
        template_data["sources"] = real_sources

    # 3. Generate the document
    try:
        output_path = doc_service.generate_docx(template_data)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    background_tasks.add_task(os.remove, output_path)

    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"nmck_report_{payload.cte_id}.docx",
    )
