"""Schemas para el Compliance Checklist automatico."""

from enum import Enum

from pydantic import BaseModel, Field


class ChecklistItemStatus(str, Enum):
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class ChecklistCategory(str, Enum):
    LEGAL = "legal"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    TIMELINE = "timeline"
    OTHER = "other"


class ChecklistSeverity(str, Enum):
    MANDATORY = "mandatory"
    DESIRABLE = "desirable"


class ChecklistItem(BaseModel):
    """Un requisito extraido del pliego de licitacion."""

    id: str = Field(description="Identificador unico del item")
    requirement_text: str = Field(description="Texto del requisito extraido")
    category: ChecklistCategory = Field(description="Categoria del requisito")
    severity: ChecklistSeverity = Field(description="Severidad: obligatorio o deseable")
    status: ChecklistItemStatus = Field(
        default=ChecklistItemStatus.PENDING,
        description="Estado de cumplimiento actual",
    )
    source_page: int | None = Field(default=None, description="Pagina fuente en el documento")
    source_document: str | None = Field(default=None, description="Nombre del documento fuente")


class ChecklistSummary(BaseModel):
    """Resumen estadistico del checklist."""

    total: int = Field(description="Total de requisitos")
    by_category: dict[str, int] = Field(default_factory=dict, description="Conteo por categoria")
    by_severity: dict[str, int] = Field(default_factory=dict, description="Conteo por severidad")
    by_status: dict[str, int] = Field(default_factory=dict, description="Conteo por estado")


class ChecklistResponse(BaseModel):
    """Respuesta completa del checklist con items y resumen."""

    items: list[ChecklistItem] = Field(default_factory=list)
    summary: ChecklistSummary = Field(description="Estadisticas agregadas del checklist")

    @classmethod
    def from_items(cls, items: list[ChecklistItem]) -> "ChecklistResponse":
        """Construye respuesta calculando el summary a partir de los items."""
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for item in items:
            by_category[item.category.value] = by_category.get(item.category.value, 0) + 1
            by_severity[item.severity.value] = by_severity.get(item.severity.value, 0) + 1
            by_status[item.status.value] = by_status.get(item.status.value, 0) + 1

        return cls(
            items=items,
            summary=ChecklistSummary(
                total=len(items),
                by_category=by_category,
                by_severity=by_severity,
                by_status=by_status,
            ),
        )


class ChecklistItemUpdate(BaseModel):
    """Payload para actualizar el estado de un item."""

    status: ChecklistItemStatus = Field(description="Nuevo estado del item")
