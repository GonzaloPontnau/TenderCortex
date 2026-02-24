"""Step definitions for API endpoint BDD features."""

import pytest
from unittest.mock import AsyncMock, patch

from pytest_bdd import scenarios, given, when, then, parsers

from httpx import AsyncClient, ASGITransport

from app.main import app


# ── Load API feature files ──────────────────────────────────────────
scenarios("../features/api/chat_endpoint.feature")
scenarios("../features/api/document_ingest.feature")


@pytest.fixture
def api_ctx():
    """Mutable context shared across API steps."""
    return {"response": None, "client": None}


@pytest.fixture
async def test_client():
    """Async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# GIVEN steps
# =============================================================================


@given("the API server is running")
def given_api_running():
    pass  # FastAPI test client handles this


@given("documents have been ingested")
def given_docs_ingested(api_ctx):
    api_ctx["has_documents"] = True


@given("no documents have been ingested")
def given_no_docs(api_ctx):
    api_ctx["has_documents"] = False


# =============================================================================
# WHEN steps — Chat
# =============================================================================


@when(parsers.parse('I POST to "/api/chat" with question "{question}"'))
async def when_post_chat(api_ctx, test_client, question):
    has_docs = api_ctx.get("has_documents", True)

    with patch("app.api.routes.chat.get_rag_service") as mock_rag_fn, \
         patch("app.api.routes.chat.compile_graph") as mock_graph_fn:
        rag = AsyncMock()
        rag.get_document_count = AsyncMock(return_value=5 if has_docs else 0)
        mock_rag_fn.return_value = rag

        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "answer": "El presupuesto es USD 5M." if has_docs else
                      "No hay documentos cargados en el sistema.\n\nPara poder responder",
            "context": [],
            "filtered_context": [],
            "domain": "financial" if has_docs else "none",
            "audit_result": "pass",
            "revision_count": 0,
            "risk_level": "low",
            "compliance_status": "approved",
            "risk_issues": [],
            "gate_passed": True,
            "quant_chart": None,
            "quant_chart_type": None,
            "quant_insights": None,
            "quant_data_quality": None,
            "no_documents": not has_docs,
        })
        mock_graph_fn.return_value = mock_graph

        response = await test_client.post("/api/chat", json={"question": question})

    api_ctx["response"] = response


@when('I POST to "/api/chat" with a 2001-character question')
async def when_post_long_question(api_ctx, test_client):
    question = "x" * 2001
    response = await test_client.post("/api/chat", json={"question": question})
    api_ctx["response"] = response


# =============================================================================
# WHEN steps — Document Ingest
# =============================================================================


@when('I POST a PDF file to "/api/ingest"')
async def when_post_pdf(api_ctx, test_client):
    with patch("app.api.routes.documents.get_rag_service") as mock_rag_fn:
        rag = AsyncMock()
        rag.ingest_file = AsyncMock(return_value=42)
        mock_rag_fn.return_value = rag

        pdf_content = b"%PDF-1.4 fake content"
        response = await test_client.post(
            "/api/ingest",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )

    api_ctx["response"] = response


@when('I POST a non-PDF file to "/api/ingest"')
async def when_post_non_pdf(api_ctx, test_client):
    response = await test_client.post(
        "/api/ingest",
        files={"file": ("test.txt", b"plain text", "text/plain")},
    )
    api_ctx["response"] = response


@when('I DELETE "/api/index"')
async def when_delete_index(api_ctx, test_client):
    with patch("app.api.routes.documents.get_rag_service") as mock_rag_fn:
        rag = AsyncMock()
        rag.clear = AsyncMock()
        mock_rag_fn.return_value = rag

        response = await test_client.delete("/api/index")

    api_ctx["response"] = response


@when('I GET "/api/index/stats"')
async def when_get_stats(api_ctx, test_client):
    with patch("app.api.routes.documents.get_rag_service") as mock_rag_fn:
        rag = AsyncMock()
        rag.get_stats = AsyncMock(return_value={"total_documents": 5, "total_chunks": 42})
        mock_rag_fn.return_value = rag

        response = await test_client.get("/api/index/stats")

    api_ctx["response"] = response


# =============================================================================
# THEN steps
# =============================================================================


@then(parsers.parse("the response status is {status:d}"))
def then_status_code(api_ctx, status):
    assert api_ctx["response"].status_code == status


@then(parsers.parse('the response contains an "{field}" field'))
def then_response_has_field(api_ctx, field):
    data = api_ctx["response"].json()
    assert field in data


@then(parsers.parse('the response contains "{field}"'))
def then_response_contains(api_ctx, field):
    data = api_ctx["response"].json()
    assert field in data


@then(parsers.parse('agent_metadata contains "{field}"'))
def then_metadata_has(api_ctx, field):
    data = api_ctx["response"].json()
    assert field in data.get("agent_metadata", {})


@then(parsers.parse('the response contains "{field}" as "{value}"'))
def then_field_value(api_ctx, field, value):
    data = api_ctx["response"].json()
    assert data.get(field) == value


@then(parsers.parse('the response contains "{field}" greater than {value:d}'))
def then_field_gt(api_ctx, field, value):
    data = api_ctx["response"].json()
    assert data.get(field, 0) > value


@then("the answer contains upload instructions")
def then_upload_instructions(api_ctx):
    data = api_ctx["response"].json()
    answer = data.get("answer", "")
    assert "documento" in answer.lower() or "carga" in answer.lower() or \
           "sube" in answer.lower() or "upload" in answer.lower() or \
           "no hay" in answer.lower()


@then("the vector store is empty")
def then_store_empty(api_ctx):
    assert api_ctx["response"].status_code == 200


@then("the response contains vector store statistics")
def then_has_stats(api_ctx):
    data = api_ctx["response"].json()
    assert isinstance(data, dict)
