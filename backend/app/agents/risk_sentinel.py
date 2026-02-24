"""
Risk Sentinel - Auditor de Gates y Compliance
Rol: Oficial de cumplimiento. Unico agente con permiso para decir "NO".

Mentalidad:
"Confio, pero verifico. Mi trabajo es encontrar inconsistencias.
No me importa lo bien que suene la propuesta; si no cumple la norma, la bloqueo.
Soy pesimista por diseño."
"""
from typing import Literal

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.core.logging import AgentLogger
from app.services import get_llm
from app.agents.utils import parse_json_response as _parse_json_response
from app.agents.prompts import UNIFIED_RISK_PROMPT_ENHANCED

logger = AgentLogger("risk_sentinel")

RiskLevel = Literal["low", "medium", "high", "critical"]
ComplianceStatus = Literal["approved", "pending", "rejected"]


# [Skill Integration] - Risk Score Calculator
try:
    from skills.risk_score_calculator.impl import RiskScoreCalculator, RiskFactorInput, RiskCategory, Severity as SkillSeverity, Recommendation
    RISK_CALCULATOR_AVAILABLE = True
except ImportError:
    RISK_CALCULATOR_AVAILABLE = False


async def risk_audit(
    answer: str,
    context: list[Document],
    question: str,
    project_state: dict | None = None
) -> tuple[RiskLevel, ComplianceStatus, list[str], bool]:
    """
    Pipeline simplificado de Risk Sentinel (1 sola llamada LLM).
    
    Args:
        answer: Respuesta generada a auditar
        context: Documentos de contexto
        question: Pregunta original
        project_state: Estado del proyecto (opcional, no usado actualmente)
    
    Returns:
        tuple: (risk_level, compliance_status, issues, gate_passed)
    """
    logger.node_enter("risk_audit", {"question": question[:50]})
    
    try:
        # Respuestas cortas o errores: aprobar automáticamente
        if len(answer) < 50 or "error" in answer.lower():
            logger.node_exit("risk_audit", "Short/error answer - auto-approved")
            return "low", "approved", [], True
        
        # Respuesta de "no hay documentos": aprobar sin auditar
        if "no hay documentos" in answer.lower():
            logger.node_exit("risk_audit", "No documents message - auto-approved")
            return "low", "approved", [], True
        
        context_text = "\n\n---\n\n".join(doc.page_content for doc in context[:5])  # Limitar a 5 docs
        
        llm = get_llm(temperature=settings.risk_temperature)
        
        prompt = UNIFIED_RISK_PROMPT_ENHANCED.format(
            answer=answer[: settings.answer_max_chars],
            context=context_text[: settings.context_max_chars],
            question=question
        )
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        result = _parse_json_response(response.content)
        
        if not result:
            logger.node_exit("risk_audit", "Failed to parse JSON - defaulting to medium/approved")
            return "medium", "approved", [], True
        
        # Default/Fallback values
        risk_level: RiskLevel = result.get("risk_level", "medium")  # Will be recalculated if skill active
        compliance: ComplianceStatus = result.get("compliance_status", "approved")
        issues = result.get("issues", [])
        gate_passed = result.get("gate_passed", True)

        # --- SKILL INTEGRATION: Risk Score Calculator ---
        if RISK_CALCULATOR_AVAILABLE and "risk_factors" in result:
            try:
                raw_factors = result.get("risk_factors", [])
                risk_inputs = []
                
                for rf in raw_factors:
                    # Validate and convert to RiskFactorInput
                    try:
                        # Map strings to Enums safely
                        sev_str = rf.get("severity", "medium").upper()
                        cat_str = rf.get("category", "financial").upper()
                        
                        # Handle potential mapping errors dynamically could be cleaner, but hardcoding for safety
                        severity = getattr(SkillSeverity, sev_str, SkillSeverity.MEDIUM)
                        category = getattr(RiskCategory, cat_str, RiskCategory.FINANCIAL)
                        
                        risk_inputs.append(RiskFactorInput(
                            description=rf.get("description", "Unknown risk"),
                            category=category,
                            severity=severity,
                            probability=float(rf.get("probability", 0.5)),
                            source_agent="RiskSentinel"
                        ))
                    except Exception as conv_err:
                        logger.debug("risk_audit", f"Skipping malformed risk factor: {conv_err}")
                
                if risk_inputs:
                    calc = RiskScoreCalculator(allow_empty_risks=True)
                    assessment = calc.calculate(risk_inputs)
                    
                    # Override outcomes based on deterministic calculation
                    logger.debug(
                        "risk_audit",
                        f"Risk Score Calculated: {assessment.total_score} ({assessment.recommendation.value})",
                    )
                    
                    # Map Recommendation to ComplianceStatus
                    if assessment.recommendation == Recommendation.GO:
                        compliance = "approved"
                        risk_level = "low"
                        gate_passed = True
                    elif assessment.recommendation == Recommendation.REVIEW:
                        compliance = "pending"
                        risk_level = "medium" # or high depending on score
                        gate_passed = True # Pending usually doesn't block flow in this graph logic? 
                                          # In graph: 'refine' if revision < 2.
                                          # If gate_passed is False?
                    else: # NO_GO
                        compliance = "rejected"
                        risk_level = "critical"
                        gate_passed = False
                        
                    # If high score but review needed
                    if assessment.total_score < 70:
                        risk_level = "high"
                    if assessment.total_score < 40:
                        risk_level = "critical"

                    # Add calculation insights to issues
                    issues.append(f"[RiskScore] Score: {assessment.total_score}/100. Rec: {assessment.recommendation.value}")
                    if assessment.kill_switch_activated:
                        issues.append(f"[RiskScore] KILL SWITCH ACTIVATED: {assessment.recommendation_reason}")

            except Exception as s_err:
                logger.error("risk_audit", s_err)
        # ------------------------------------------------

        # Validaciones finales
        if risk_level not in ["low", "medium", "high", "critical"]:
            risk_level = "medium"
        if compliance not in ["approved", "pending", "rejected"]:
            compliance = "approved"
        
        # Filtrar issues vacíos
        issues = [i for i in issues if i and not i.startswith("Lista SOLO")]
        
        logger.node_exit(
            "risk_audit",
            f"risk={risk_level}, compliance={compliance}, issues={len(issues)}, gate={gate_passed}"
        )
        
        return risk_level, compliance, issues, gate_passed
        
    except Exception as e:
        logger.error("risk_audit", e)
        return "medium", "approved", [f"Error en auditoría: {str(e)}"], True

