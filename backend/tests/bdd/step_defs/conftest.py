"""BDD-specific fixtures for pytest-bdd step definitions.

Extends the shared conftest.py fixtures with BDD-oriented helpers
for pipeline state management, mock orchestration, and assertions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.documents import Document

from app.agents.state import AgentState, create_initial_state, NO_DOCUMENTS_MESSAGE
from app.core.config import settings


# =============================================================================
# PIPELINE STATE FIXTURES
# =============================================================================


@pytest.fixture
def initial_state() -> dict:
    """Create a fresh AgentState for pipeline testing."""
    return create_initial_state("Test question")


@pytest.fixture
def state_with_context(sample_context) -> dict:
    """AgentState pre-populated with retrieved documents."""
    state = create_initial_state("Cual es el presupuesto total?")
    state["context"] = sample_context
    return state


@pytest.fixture
def state_with_answer(state_with_context) -> dict:
    """AgentState with a specialist answer ready for audit."""
    state = state_with_context
    state["domain"] = "financial"
    state["filtered_context"] = state["context"]
    state["answer"] = "El presupuesto total es de USD 5,000,000."
    return state


@pytest.fixture
def state_after_failed_audit(state_with_answer) -> dict:
    """AgentState after an audit rejection."""
    state = state_with_answer
    state["audit_result"] = "fail"
    state["compliance_status"] = "rejected"
    state["gate_passed"] = False
    state["risk_level"] = "high"
    state["risk_issues"] = ["La respuesta no cita fuentes del documento"]
    return state


@pytest.fixture
def state_at_max_revisions(state_after_failed_audit) -> dict:
    """AgentState that has reached the maximum revision limit."""
    state = state_after_failed_audit
    state["revision_count"] = settings.max_audit_revisions
    return state


# =============================================================================
# MOCK SERVICE FIXTURES
# =============================================================================


@pytest.fixture
def mock_rag_with_docs(sample_context):
    """RAG service mock that returns sample documents."""
    rag = AsyncMock()
    rag.similarity_search = AsyncMock(return_value=sample_context)
    rag.warmup = AsyncMock()
    rag.health_check = AsyncMock(return_value=True)
    return rag


@pytest.fixture
def mock_rag_empty():
    """RAG service mock that returns no documents (empty store)."""
    rag = AsyncMock()
    rag.similarity_search = AsyncMock(return_value=[])
    rag.warmup = AsyncMock()
    rag.health_check = AsyncMock(return_value=True)
    return rag


@pytest.fixture
def mock_rag_error():
    """RAG service mock that raises an exception."""
    rag = AsyncMock()
    rag.similarity_search = AsyncMock(side_effect=Exception("Vector store unavailable"))
    return rag


@pytest.fixture
def mock_router():
    """Mock for the domain router function."""
    with patch("app.agents.router.route_question") as mock:
        mock.return_value = "financial"
        yield mock


@pytest.fixture
def mock_risk_audit_pass():
    """Mock risk_audit that returns a passing result."""
    with patch("app.agents.risk_sentinel.risk_audit") as mock:
        mock.return_value = ("low", "approved", [], True)
        yield mock


@pytest.fixture
def mock_risk_audit_fail():
    """Mock risk_audit that returns a failing result."""
    with patch("app.agents.risk_sentinel.risk_audit") as mock:
        mock.return_value = ("high", "rejected", ["Issues found"], False)
        yield mock


# =============================================================================
# ASSERTION HELPERS
# =============================================================================


@pytest.fixture
def no_documents_message():
    """The expected no-documents message constant."""
    return NO_DOCUMENTS_MESSAGE


@pytest.fixture
def max_audit_revisions():
    """The configured max audit revisions from settings."""
    return settings.max_audit_revisions
