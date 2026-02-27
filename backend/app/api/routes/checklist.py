"""Endpoints para el Compliance Checklist automatico."""

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.schemas.checklist import ChecklistItemUpdate, ChecklistResponse
from app.services.checklist_service import get_checklist_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/checklist/generate", response_model=ChecklistResponse)
async def generate_checklist() -> ChecklistResponse:
    """Genera un checklist de requisitos a partir de los documentos indexados."""
    try:
        service = get_checklist_service()
        result = await service.generate()
        logger.info(f"Checklist generado: {result.summary.total} requisitos")
        return result
    except Exception as e:
        logger.error(f"Error generando checklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando checklist: {str(e)}",
        )


@router.get("/checklist", response_model=ChecklistResponse)
async def get_checklist() -> ChecklistResponse:
    """Obtiene el checklist generado previamente."""
    service = get_checklist_service()
    checklist = service.get_checklist()
    if checklist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist no generado. Usa POST /api/checklist/generate primero.",
        )
    return checklist


@router.patch("/checklist/items/{item_id}")
async def update_checklist_item(item_id: str, update: ChecklistItemUpdate) -> dict:
    """Actualiza el estado de cumplimiento de un item del checklist."""
    service = get_checklist_service()

    if service.get_checklist() is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Checklist no generado aun.",
        )

    try:
        item = service.update_item(item_id, update.status)
        return item.model_dump()
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_id}' no encontrado.",
        )
