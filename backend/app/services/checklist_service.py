"""Servicio de generacion de checklist de requisitos desde documentos indexados."""

import asyncio
import json
import re
from functools import lru_cache
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.checklist import (
    ChecklistCategory,
    ChecklistItem,
    ChecklistItemStatus,
    ChecklistResponse,
    ChecklistSeverity,
)
from app.services.llm_factory import get_llm
from app.services.vector_store import COLLECTION_NAME, get_rag_service

logger = get_logger(__name__)

EXTRACTION_PROMPT = """Eres un experto en analisis de pliegos de licitaciones publicas. Tu tarea es extraer TODOS los requisitos, exigencias, condiciones y obligaciones del texto proporcionado.

## REGLAS:

1. Extrae cada requisito como un item independiente y concreto.
2. Clasifica cada requisito en una categoria:
   - "legal": Contratos, clausulas, jurisdiccion, normativa, legislacion
   - "technical": Arquitectura, tecnologia, integraciones, equipamiento, infraestructura
   - "financial": Presupuesto, pagos, garantias, seguros, facturacion
   - "administrative": Documentacion, formularios, inscripciones, registros
   - "timeline": Fechas, plazos, cronogramas, hitos, entregas
   - "other": Cualquier requisito que no encaje en las anteriores

3. Detecta la severidad:
   - "mandatory": Usa palabras como DEBE, DEBERA, obligatorio, excluyente, indispensable, requisito, requerido
   - "desirable": Usa palabras como se valorara, deseable, preferible, opcional, plus, ventaja

4. Incluye la pagina fuente si esta disponible en los metadatos.

5. El texto del requisito debe ser conciso pero completo (1-2 oraciones).

## FORMATO DE RESPUESTA (JSON array estricto):

```json
[
  {
    "requirement_text": "El licitante debera presentar certificacion ISO 27001 vigente",
    "category": "technical",
    "severity": "mandatory",
    "source_page": 12
  }
]
```

RESPONDE UNICAMENTE CON EL JSON ARRAY. Sin texto adicional."""

MAX_BATCH_CHARS = 4000


class ChecklistService:
    """Extrae requisitos de documentos indexados y gestiona un checklist en memoria."""

    def __init__(self):
        self._items: dict[str, ChecklistItem] | None = None

    async def generate(self) -> ChecklistResponse:
        """Extrae requisitos de todos los documentos indexados y genera el checklist."""
        rag = get_rag_service()

        if rag._client is None:
            await rag._initialize()

        records, _ = await asyncio.to_thread(
            rag._client.scroll,
            collection_name=COLLECTION_NAME,
            limit=2000,
            with_payload=True,
        )

        if not records:
            self._items = {}
            return ChecklistResponse.from_items([])

        batches = self._build_batches(records)
        logger.info(f"Generando checklist: {len(records)} chunks en {len(batches)} batches")

        all_items: list[ChecklistItem] = []
        llm = get_llm(temperature=0.0)

        for idx, batch in enumerate(batches, 1):
            try:
                items = await self._extract_from_batch(llm, batch["text"], batch["source"], batch["pages"])
                all_items.extend(items)
                logger.info(f"Batch {idx}/{len(batches)}: {len(items)} requisitos extraidos")
            except Exception as e:
                logger.error(f"Error en batch {idx}: {e}")

        all_items = self._deduplicate(all_items)
        self._items = {item.id: item for item in all_items}
        logger.info(f"Checklist generado: {len(all_items)} requisitos unicos")

        return ChecklistResponse.from_items(all_items)

    def get_checklist(self) -> ChecklistResponse | None:
        """Retorna el checklist actual o None si no fue generado."""
        if self._items is None:
            return None
        return ChecklistResponse.from_items(list(self._items.values()))

    def update_item(self, item_id: str, status: ChecklistItemStatus) -> ChecklistItem:
        """Actualiza el estado de un item. Raises KeyError si no existe."""
        if self._items is None:
            raise RuntimeError("Checklist no generado")
        if item_id not in self._items:
            raise KeyError(f"Item {item_id} no encontrado")
        self._items[item_id].status = status
        return self._items[item_id]

    def clear(self) -> None:
        """Limpia el checklist (llamar cuando se borran documentos)."""
        self._items = None

    def _build_batches(self, records) -> list[dict]:
        """Agrupa records en batches respetando MAX_BATCH_CHARS."""
        batches: list[dict] = []
        current_text = ""
        current_source = ""
        current_pages: list[int] = []

        for record in records:
            if not record.payload:
                continue
            content = record.payload.get("page_content", "")
            metadata = record.payload.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page", 0)

            if len(current_text) + len(content) > MAX_BATCH_CHARS and current_text:
                batches.append({"text": current_text, "source": current_source, "pages": current_pages})
                current_text = ""
                current_pages = []

            current_text += f"\n\n[Pagina {page + 1}, Fuente: {source}]\n{content}"
            current_source = source
            if page not in current_pages:
                current_pages.append(page)

        if current_text:
            batches.append({"text": current_text, "source": current_source, "pages": current_pages})

        return batches

    async def _extract_from_batch(
        self, llm, text: str, source: str, pages: list[int]
    ) -> list[ChecklistItem]:
        """Extrae requisitos de un batch de texto usando el LLM."""
        messages = [
            SystemMessage(content=EXTRACTION_PROMPT),
            HumanMessage(content=f"Analiza el siguiente texto y extrae los requisitos:\n\n{text}"),
        ]

        response = await llm.ainvoke(messages)
        return self._parse_extraction(response.content, source)

    def _parse_extraction(self, response_text: str, source: str) -> list[ChecklistItem]:
        """Parsea la respuesta JSON del LLM en ChecklistItems."""
        try:
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if not json_match:
                logger.warning(f"No se encontro JSON array en respuesta LLM")
                return []

            raw_items = json.loads(json_match.group())
            items: list[ChecklistItem] = []

            for raw in raw_items:
                if not isinstance(raw, dict) or "requirement_text" not in raw:
                    continue

                category = self._parse_category(raw.get("category", "other"))
                severity = self._parse_severity(raw.get("severity", "mandatory"))
                page = raw.get("source_page")

                items.append(
                    ChecklistItem(
                        id=uuid4().hex[:8],
                        requirement_text=raw["requirement_text"].strip(),
                        category=category,
                        severity=severity,
                        source_page=page if isinstance(page, int) else None,
                        source_document=source,
                    )
                )

            return items
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parseando extraccion: {e}")
            return []

    @staticmethod
    def _parse_category(value: str) -> ChecklistCategory:
        try:
            return ChecklistCategory(value.lower())
        except ValueError:
            return ChecklistCategory.OTHER

    @staticmethod
    def _parse_severity(value: str) -> ChecklistSeverity:
        try:
            return ChecklistSeverity(value.lower())
        except ValueError:
            return ChecklistSeverity.MANDATORY

    @staticmethod
    def _deduplicate(items: list[ChecklistItem]) -> list[ChecklistItem]:
        """Elimina requisitos duplicados por texto similar."""
        seen: set[str] = set()
        unique: list[ChecklistItem] = []

        for item in items:
            normalized = item.requirement_text.lower().strip()
            # Clave simplificada: primeros 60 chars normalizados
            key = normalized[:60]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique


@lru_cache
def get_checklist_service() -> ChecklistService:
    """Retorna instancia singleton del ChecklistService."""
    return ChecklistService()
