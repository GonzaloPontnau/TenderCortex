"""
Prompts utilizados por los nodos de infraestructura del grafo (grader, refiner).
"""

GRADER_PROMPT_BATCH = """Eres un evaluador de relevancia documental. Tu tarea es determinar si cada documento
contiene información relevante para responder la pregunta del usuario.

REGLAS CRÍTICAS DE RELEVANCIA:
1. SIEMPRE marca como "relevant" documentos que contengan:
   - TABLAS (cronogramas, presupuestos, requisitos tabulados)
   - FECHAS específicas (DD/MM/AAAA, plazos, cronogramas)
   - MONTOS FINANCIEROS (USD, ARS, porcentajes de garantía)
   - PORCENTAJES (% de participación, SLAs, penalidades)
   - LISTAS NUMERADAS de requisitos o especificaciones

2. Estos documentos son relevantes INCLUSO si tienen poco texto narrativo.
   Un documento con solo una tabla de fechas ES RELEVANTE para preguntas de cronograma.

3. Evalúa el CONTENIDO ESTRUCTURADO (tablas, listas) con el mismo peso que el texto.

A continuación se presentan {doc_count} documentos numerados. Evalúa CADA uno.

{documents_block}

Pregunta:
{question}

Responde con una línea por documento, EXACTAMENTE en este formato (sin texto extra):
1:relevant
2:not_relevant
3:relevant
..."""

REFINE_PROMPT = """Eres un experto en licitaciones especializado en el dominio: {domain}.
La respuesta anterior fue insuficiente. Revisa CUIDADOSAMENTE todo el contexto.

Busca específicamente según tu dominio:
- legal: normativas, artículos, obligaciones, sanciones
- technical: tecnologías, arquitectura, integraciones, SLAs técnicos
- financial: montos, porcentajes, garantías, pagos
- timeline: fechas, plazos, cronogramas, hitos
- requirements: requisitos, experiencia, personal, capacidades

Contexto completo:
{context}

Pregunta del usuario:
{question}

Respuesta anterior (insuficiente):
{previous_answer}

Genera una respuesta mejorada basada ÚNICAMENTE en el contexto. Si realmente no hay información, indícalo."""

# ---------------------------------------------------------------------------
# QuanT prompts
# ---------------------------------------------------------------------------

EXTRACTION_AND_STRATEGY_PROMPT = """Eres un extractor de datos numericos y experto en visualizacion, especializado en documentos de licitaciones.

TAREA DOBLE:
1. Identifica y extrae TODOS los datos numericos relevantes del contexto para responder la pregunta
2. Decide la mejor forma de visualizar esos datos

INSTRUCCIONES DE EXTRACCION:
- Busca montos, porcentajes, cantidades, fechas con valores, metricas
- Identifica las categorias o etiquetas asociadas a cada numero
- Detecta si hay series temporales o comparaciones
- Indica si los datos estan completos o hay valores faltantes

REGLAS DE VISUALIZACION:
- Comparar volumenes/cantidades -> "bar" (grafico de barras)
- Evolucion temporal/tendencias -> "line" (grafico de lineas)
- Distribucion/porcentajes de un todo -> "pie" (grafico circular)
- Datos tabulares complejos -> "table" (tabla formateada)
- Valor unico, datos insuficientes o sin datos -> "none" (solo texto)

FORMATO DE RESPUESTA (JSON estricto):
{{
    "data_found": true/false,
    "data_type": "comparison" | "timeline" | "distribution" | "single_value" | "table",
    "categories": ["categoria1", "categoria2", ...],
    "values": [valor1, valor2, ...],
    "unit": "USD" | "ARS" | "%" | "dias" | "unidades" | "otro",
    "data_quality": "clean" | "sanitized" | "incomplete",
    "chart_type": "bar" | "line" | "pie" | "table" | "none",
    "notes": "observaciones sobre los datos"
}}

Si NO hay datos numericos relevantes, responde:
{{
    "data_found": false,
    "data_type": "none",
    "categories": [],
    "values": [],
    "unit": "",
    "data_quality": "incomplete",
    "chart_type": "none",
    "notes": "No se encontraron datos numericos relevantes para la pregunta"
}}

Contexto del documento:
{context}

Pregunta del usuario:
{question}

Responde SOLO con el JSON, sin texto adicional:"""

INSIGHT_PROMPT = """Eres QuanT, un analista cuantitativo experto. Genera un insight claro y conciso
basado en los datos y la visualizacion.

INSTRUCCIONES:
- Comienza con el hallazgo principal (ej: "El presupuesto total es de...")
- Menciona comparaciones o tendencias si existen
- Destaca valores criticos en **negrita**
- Si hay anomalias o datos faltantes, mencionalo
- Se preciso: usa los numeros exactos del contexto

Tipo de grafico generado: {chart_type}
Datos analizados: {data}
Pregunta original: {question}

Genera el insight (2-4 oraciones):"""

# ---------------------------------------------------------------------------
# Risk Sentinel prompts
# ---------------------------------------------------------------------------

UNIFIED_RISK_PROMPT_ENHANCED = """Eres un auditor de compliance y riesgos para licitaciones. Analiza la respuesta generada contra el contexto del documento.

RESPUESTA A AUDITAR:
{answer}

CONTEXTO DEL DOCUMENTO:
{context}

PREGUNTA ORIGINAL:
{question}

TAREA:
1. Verifica si las afirmaciones de la respuesta están respaldadas por el contexto.
2. Identifica riesgos específicos (factores de riesgo) para la viabilidad de la oferta.
3. Evalúa la severidad y probabilidad de cada riesgo.

CRITERIOS DE RIESGO:
- low: Riesgo menor, gestionable.
- medium: Riesgo moderado, requiere mitigación.
- high: Riesgo alto, puede comprometer la oferta.
- critical: Riesgo crítico, "Showstopper" (ej: inhabilitación, incumplimiento legal grave).

RESPONDE SOLO EN JSON:
{{
    "risk_factors": [
        {{
            "description": "Descripción del riesgo detectado",
            "category": "financial|legal|technical|timeline|requirements|reputation",
            "severity": "low|medium|high|critical",
            "probability": 0.1-1.0 (float)
        }}
    ],
    "compliance_status": "approved|pending|rejected",
    "gate_passed": true/false,
    "issues": ["Lista de observaciones textuales (resumen)"]
}}"""
