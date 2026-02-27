"""Endpoints de gestion documental para el indice vectorial."""

import json
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.routes.chat import invalidate_cache
from app.core.logging import get_logger
from app.schemas import IngestResponse
from app.services import get_rag_service
from app.services.checklist_service import get_checklist_service

logger = get_logger(__name__)
router = APIRouter()


async def _save_upload_to_temp(file: UploadFile) -> Path:
    """Guarda un UploadFile a un archivo temporal y retorna el path."""
    tmp_path = Path(tempfile.mktemp(suffix=".pdf"))
    with open(tmp_path, "wb") as tmp:
        while chunk := await file.read(1024 * 256):
            tmp.write(chunk)
    return tmp_path


def _validate_pdf(file: UploadFile) -> None:
    """Valida que el archivo sea un PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF",
        )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile) -> IngestResponse:
    """Procesa un PDF y lo indexa en el vector store."""
    _validate_pdf(file)

    original_filename = file.filename
    tmp_path: Path | None = None
    try:
        tmp_path = await _save_upload_to_temp(file)
        rag = get_rag_service()
        chunks = await rag.ingest_document(tmp_path, original_filename=original_filename)
        invalidate_cache()
        logger.info(f"Documento '{original_filename}' procesado: {chunks} chunks")
        return IngestResponse(status="success", filename=original_filename, chunks_processed=chunks)
    except Exception as e:
        logger.error(f"Error en ingesta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando documento: {str(e)}",
        )
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


@router.post("/ingest/stream")
async def ingest_document_stream(file: UploadFile) -> StreamingResponse:
    """Procesa un PDF con progreso en tiempo real via Server-Sent Events.

    Emite eventos SSE con formato:
        data: {"phase": "parsing", "message": "Extrayendo texto del PDF..."}
        data: {"phase": "embedding", "message": "...", "batch_current": 1, "batch_total": 3}
        data: {"phase": "done", "message": "...", "chunks": 42, "elapsed_seconds": 8.3}
    """
    _validate_pdf(file)

    original_filename = file.filename
    tmp_path = await _save_upload_to_temp(file)

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            rag = get_rag_service()
            async for event in rag.ingest_document_streaming(
                tmp_path, original_filename=original_filename
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("phase") == "done":
                    invalidate_cache()
        except Exception as e:
            logger.error(f"Error en ingesta streaming: {e}")
            yield f"data: {json.dumps({'phase': 'error', 'message': str(e)})}\n\n"
        finally:
            tmp_path.unlink(missing_ok=True)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/index")
async def clear_index() -> dict:
    """Elimina todos los vectores del vector store."""
    try:
        rag = get_rag_service()
        success = await rag.clear_index()
        if success:
            invalidate_cache()
            get_checklist_service().clear()
            return {"status": "success", "message": "Indice limpiado exitosamente"}
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error limpiando el indice")
    except Exception as e:
        logger.error(f"Error en clear_index: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/index/stats")
async def get_index_stats() -> dict:
    """Obtiene estadisticas del vector store."""
    try:
        rag = get_rag_service()
        return await rag.get_stats()
    except Exception as e:
        logger.error(f"Error en get_stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/documents")
async def get_documents() -> dict:
    """Obtiene lista de documentos indexados para sincronizar con frontend."""
    try:
        rag = get_rag_service()
        documents = await rag.get_indexed_documents()
        return {"status": "success", "documents": documents}
    except Exception as e:
        logger.error(f"Error obteniendo documentos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
