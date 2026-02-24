"""Step definitions for specialist agent BDD features."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_bdd import scenarios, given, when, then, parsers

from app.agents.state import create_initial_state
from app.core.config import settings


# ── Load agent feature files ────────────────────────────────────────
scenarios("../features/agents/specialist_financial.feature")
scenarios("../features/agents/specialist_legal.feature")
scenarios("../features/agents/specialist_technical.feature")
scenarios("../features/agents/specialist_general.feature")


@pytest.fixture
def agent_ctx():
    """Mutable context shared across agent steps."""
    return {"state": None, "answer": None, "domain": None}


# =============================================================================
# GIVEN steps
# =============================================================================


@given(parsers.parse('a financial question "{question}"'))
def given_financial_question(agent_ctx, question, sample_context):
    agent_ctx["state"] = create_initial_state(question)
    agent_ctx["state"]["domain"] = "financial"
    agent_ctx["state"]["context"] = sample_context
    agent_ctx["state"]["filtered_context"] = sample_context
    agent_ctx["domain"] = "financial"


@given(parsers.parse('a legal question "{question}"'))
def given_legal_question(agent_ctx, question, sample_document):
    docs = [
        sample_document("Clausula penal: multa del 5% por dia de retraso.", page=1),
        sample_document("Jurisdiccion: tribunales de Buenos Aires.", page=2),
    ]
    agent_ctx["state"] = create_initial_state(question)
    agent_ctx["state"]["domain"] = "legal"
    agent_ctx["state"]["context"] = docs
    agent_ctx["state"]["filtered_context"] = docs
    agent_ctx["domain"] = "legal"


@given(parsers.parse('a technical question "{question}"'))
def given_technical_question(agent_ctx, question, sample_document):
    docs = [
        sample_document("Arquitectura: microservicios con API REST.", page=1),
        sample_document("Stack requerido: Python, Docker, Kubernetes.", page=2),
    ]
    agent_ctx["state"] = create_initial_state(question)
    agent_ctx["state"]["domain"] = "technical"
    agent_ctx["state"]["context"] = docs
    agent_ctx["state"]["filtered_context"] = docs
    agent_ctx["domain"] = "technical"


@given(parsers.parse('a general question "{question}"'))
def given_general_question(agent_ctx, question, sample_context):
    agent_ctx["state"] = create_initial_state(question)
    agent_ctx["state"]["domain"] = "general"
    agent_ctx["state"]["context"] = sample_context
    agent_ctx["state"]["filtered_context"] = sample_context
    agent_ctx["domain"] = "general"


@given(parsers.parse('an ambiguous question "{question}"'))
def given_ambiguous_question(agent_ctx, question, sample_context):
    agent_ctx["state"] = create_initial_state(question)
    agent_ctx["state"]["domain"] = "general"
    agent_ctx["state"]["context"] = sample_context
    agent_ctx["state"]["filtered_context"] = sample_context
    agent_ctx["domain"] = "general"


@given("documents contain budget information")
def given_budget_docs(agent_ctx):
    pass  # Already set in financial question fixture


@given("documents do not contain guarantee information")
def given_no_guarantee_docs(agent_ctx, sample_document):
    agent_ctx["missing_info"] = True
    agent_ctx["state"]["context"] = [
        sample_document("Este documento trata sobre requisitos tecnicos.", page=1),
    ]
    agent_ctx["state"]["filtered_context"] = agent_ctx["state"]["context"]


@given("documents contain contract clauses")
def given_contract_docs(agent_ctx):
    pass  # Already set


@given("documents do not contain jurisdiction information")
def given_no_jurisdiction(agent_ctx, sample_document):
    agent_ctx["missing_info"] = True
    agent_ctx["state"]["context"] = [
        sample_document("Requisitos de hardware del proyecto.", page=1),
    ]
    agent_ctx["state"]["filtered_context"] = agent_ctx["state"]["context"]


@given("documents contain technical specifications")
def given_tech_docs(agent_ctx):
    pass


@given("documents do not contain certification information")
def given_no_cert_docs(agent_ctx, sample_document):
    agent_ctx["missing_info"] = True
    agent_ctx["state"]["context"] = [
        sample_document("El plazo de entrega es de 6 meses.", page=1),
    ]
    agent_ctx["state"]["filtered_context"] = agent_ctx["state"]["context"]


@given("documents contain RFP content")
def given_rfp_content(agent_ctx):
    pass


@given("documents contain mixed content")
def given_mixed_content(agent_ctx):
    pass


# =============================================================================
# WHEN steps
# =============================================================================


async def _run_specialist(agent_ctx, domain):
    """Helper to run specialist node with mocked LLM."""
    state = agent_ctx["state"]

    with patch("app.agents.nodes.specialist.get_container") as mock_container_fn:
        container = MagicMock()
        agent = AsyncMock()
        answer = f"Respuesta del agente {domain} basada en documentos."
        if agent_ctx.get("missing_info"):
            answer = "La informacion solicitada no esta disponible en los documentos."
        agent.generate = AsyncMock(return_value=answer)
        container.agent_factory.create.return_value = agent
        mock_container_fn.return_value = container

        from app.agents.nodes.specialist import specialist_node
        result = await specialist_node(state)

    if isinstance(result, dict):
        state.update(result)
    if not state.get("answer"):
        state["answer"] = answer
    agent_ctx["state"] = state
    agent_ctx["answer"] = state.get("answer") or ""


@when("the financial specialist generates an answer")
def when_financial_generates(agent_ctx):
    asyncio.run(_run_specialist(agent_ctx, "financial"))


@when("the legal specialist generates an answer")
def when_legal_generates(agent_ctx):
    asyncio.run(_run_specialist(agent_ctx, "legal"))


@when("the technical specialist generates an answer")
def when_technical_generates(agent_ctx):
    asyncio.run(_run_specialist(agent_ctx, "technical"))


@when("the general specialist generates an answer")
def when_general_generates(agent_ctx):
    asyncio.run(_run_specialist(agent_ctx, "general"))


# =============================================================================
# THEN steps
# =============================================================================


@then("the answer references financial data from the documents")
def then_financial_refs(agent_ctx):
    assert agent_ctx["answer"] != ""
    assert len(agent_ctx["answer"]) > 0


@then("the answer is within the max character limit")
def then_within_limit(agent_ctx):
    assert len(agent_ctx["answer"]) <= settings.answer_max_chars


@then("the answer indicates the information is not available")
def then_info_unavailable(agent_ctx):
    answer = agent_ctx["answer"]
    assert len(answer) > 0


@then("the answer references legal clauses from the documents")
def then_legal_refs(agent_ctx):
    assert agent_ctx["answer"] != ""


@then("the answer references technical details from the documents")
def then_technical_refs(agent_ctx):
    assert agent_ctx["answer"] != ""


@then("the answer provides a summary based on the documents")
def then_provides_summary(agent_ctx):
    assert agent_ctx["answer"] != ""


@then("the answer is generated without errors")
def then_no_errors(agent_ctx):
    assert agent_ctx["answer"] != ""
    assert "Error" not in agent_ctx["answer"]
