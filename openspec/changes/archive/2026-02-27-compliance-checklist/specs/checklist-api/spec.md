# Spec: Checklist API Endpoints

## Endpoints

### POST /api/checklist/generate

Genera un checklist de requisitos a partir de los documentos indexados.

**Request**: No body required

**Response 200**:
```json
{
  "items": [
    {
      "id": "a1b2c3d4",
      "requirement_text": "El licitante debera contar con certificacion ISO 27001",
      "category": "certification",
      "severity": "mandatory",
      "status": "pending",
      "source_page": 12,
      "source_document": "pliego_2024.pdf"
    }
  ],
  "summary": {
    "total": 15,
    "by_category": {"legal": 3, "technical": 5, "financial": 2, "administrative": 3, "timeline": 1, "other": 1},
    "by_severity": {"mandatory": 10, "desirable": 5},
    "by_status": {"pending": 15, "compliant": 0, "non_compliant": 0, "not_applicable": 0}
  }
}
```

**Response 409**: No hay documentos indexados

### GET /api/checklist

Obtiene el checklist generado previamente.

**Response 200**: Mismo schema que POST /generate
**Response 404**: Checklist no generado aun

### PATCH /api/checklist/items/{item_id}

Actualiza el estado de un item del checklist.

**Request**:
```json
{
  "status": "compliant"
}
```

**Response 200**: ChecklistItem actualizado
**Response 404**: Item no encontrado
