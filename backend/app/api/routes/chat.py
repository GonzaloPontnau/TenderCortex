"""Endpoints de consulta al pipeline de agentes."""

import asyncio
import hashlib
import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.agents import rfp_app
from app.agents.state import create_initial_state
from app.api.response_builder import build_query_response
from app.core.cache import TTLCache
from app.core.config import settings
from app.core.logging import AgentLogger, get_logger
from app.schemas import QueryRequest, QueryResponse

logger = get_logger(__name__)
agent_logger = AgentLogger("pipeline")
router = APIRouter()

_response_cache = TTLCache[QueryResponse](
    ttl_seconds=settings.cache_ttl_seconds,
    max_size=settings.cache_max_size,
)

THINKING_MESSAGES = [
    "Leyendo los fragmentos mas relevantes...",
    "Filtrando evidencia util para tu pregunta...",
    "Contrastando requisitos y criterios clave...",
    "Validando consistencia antes de responder...",
    "Redactando una respuesta clara y accionable...",
]


def invalidate_cache() -> None:
    """Invalida respuestas cacheadas."""
    _response_cache.clear()


def _cache_key(question: str) -> str:
    """Genera clave estable para cache por pregunta normalizada."""
    normalized = question.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _sse_event(event_type: str, data: dict) -> str:
    """Formatea payload como evento SSE."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest) -> QueryResponse:
    """Procesa una pregunta usando el grafo multi-agente."""
    cached = _response_cache.get(_cache_key(request.question))
    if cached is not None:
        logger.info(f"[CHAT] Cache HIT for question: {request.question[:60]}...")
        return cached

    try:
        initial_state = create_initial_state(request.question)
        agent_logger.pipeline_start(request.question, initial_state.get("trace_id"))
        result = await rfp_app.ainvoke(initial_state)
        agent_logger.pipeline_end(result)
        response = build_query_response(result)
        _response_cache.set(_cache_key(request.question), response)
        return response
    except Exception as e:
        logger.error(f"[CHAT] Error procesando consulta: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando pregunta: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(request: QueryRequest) -> StreamingResponse:
    """Procesa una pregunta usando SSE para feedback en tiempo real."""

    async def _event_stream():
        run_task: asyncio.Task | None = None
        try:
            cached = _response_cache.get(_cache_key(request.question))
            if cached is not None:
                yield _sse_event("status", {"step": "cache_hit", "message": "Recuperando respuesta desde cache..."})
                yield _sse_event("result", json.loads(cached.model_dump_json()))
                return

            initial_state = create_initial_state(request.question)
            agent_logger.pipeline_start(request.question, initial_state.get("trace_id"))

            run_task = asyncio.create_task(rfp_app.ainvoke(initial_state))
            heartbeat_seconds = 1.4
            idx = 0

            yield _sse_event("status", {"step": "retrieve", "message": THINKING_MESSAGES[idx]})
            idx += 1

            while not run_task.done():
                await asyncio.sleep(heartbeat_seconds)
                if run_task.done():
                    break
                yield _sse_event(
                    "status",
                    {
                        "step": f"thinking_{idx}",
                        "message": THINKING_MESSAGES[idx % len(THINKING_MESSAGES)],
                    },
                )
                idx += 1

            result = await run_task
            agent_logger.pipeline_end(result)
            response = build_query_response(result)
            _response_cache.set(_cache_key(request.question), response)
            yield _sse_event("result", json.loads(response.model_dump_json()))
        except Exception as e:
            logger.error(f"[STREAM] Error: {e}", exc_info=True)
            yield _sse_event("error", {"detail": str(e)})
        finally:
            if run_task is not None and not run_task.done():
                run_task.cancel()

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
