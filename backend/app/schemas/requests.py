from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"question": "Cuales son los requisitos tecnicos del pliego?"},
                {"question": "Cual es el presupuesto total de la licitacion?"},
            ]
        }
    }
