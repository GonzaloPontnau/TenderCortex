from pydantic import BaseModel, Field

from app.schemas.metadata import AgentMetadata


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    agent_metadata: AgentMetadata = Field(description="Metadata del flujo de agentes para trazabilidad")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "El presupuesto total de la licitacion es de USD 5,000,000.",
                    "sources": ["licitacion_2024.pdf (p.12)", "licitacion_2024.pdf (p.15)"],
                    "agent_metadata": {
                        "domain": "financial",
                        "specialist_used": "FinancialAgent",
                        "documents_retrieved": 10,
                        "documents_filtered": 4,
                        "revision_count": 0,
                        "audit_result": "pass",
                        "quant_analysis": None,
                        "risk_assessment": None,
                    },
                }
            ]
        }
    }


class IngestResponse(BaseModel):
    status: str
    filename: str
    chunks_processed: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "filename": "licitacion_2024.pdf",
                    "chunks_processed": 42,
                }
            ]
        }
    }
