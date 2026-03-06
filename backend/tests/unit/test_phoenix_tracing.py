"""
Unit tests for the Phoenix tracing setup module.

Tests that setup_phoenix_tracing() correctly configures OTel tracing
and handles missing packages gracefully.
All OTel/Phoenix classes are mocked — no real packages required.

Validates SC-PT-01, SC-PT-05, SC-PT-07.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import importlib


@pytest.fixture(autouse=True)
def reset_tracing_initialized():
    """Reset the idempotency guard before each test."""
    import app.core.phoenix_tracing as mod
    mod._TRACING_INITIALIZED = False
    yield
    mod._TRACING_INITIALIZED = False


class TestSetupPhoenixTracingHappyPath:
    """Tests for successful tracing setup (SC-PT-01)."""

    def test_setup_calls_tracer_provider_and_exporter_and_instrumentor(self):
        """setup_phoenix_tracing() should configure TracerProvider, OTLPSpanExporter,
        and LangChainInstrumentor().instrument() with correct arguments (SC-PT-01)."""
        mock_trace = MagicMock()
        mock_resource_cls = MagicMock()
        mock_resource = MagicMock()
        mock_resource_cls.create.return_value = mock_resource

        mock_exporter_cls = MagicMock()
        mock_exporter = MagicMock()
        mock_exporter_cls.return_value = mock_exporter

        mock_provider_cls = MagicMock()
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        mock_processor_cls = MagicMock()
        mock_processor = MagicMock()
        mock_processor_cls.return_value = mock_processor

        mock_instrumentor_cls = MagicMock()
        mock_instrumentor = MagicMock()
        mock_instrumentor_cls.return_value = mock_instrumentor

        # Build the opentelemetry parent module with trace as an attribute
        # so that `from opentelemetry import trace` resolves correctly.
        mock_otel_parent = MagicMock()
        mock_otel_parent.trace = mock_trace

        mock_sdk_trace_module = MagicMock(TracerProvider=mock_provider_cls)

        modules = {
            "opentelemetry": mock_otel_parent,
            "opentelemetry.trace": mock_trace,
            "opentelemetry.exporter": MagicMock(),
            "opentelemetry.exporter.otlp": MagicMock(),
            "opentelemetry.exporter.otlp.proto": MagicMock(),
            "opentelemetry.exporter.otlp.proto.http": MagicMock(),
            "opentelemetry.exporter.otlp.proto.http.trace_exporter": MagicMock(
                OTLPSpanExporter=mock_exporter_cls
            ),
            "opentelemetry.sdk": MagicMock(),
            "opentelemetry.sdk.resources": MagicMock(Resource=mock_resource_cls),
            "opentelemetry.sdk.trace": mock_sdk_trace_module,
            "opentelemetry.sdk.trace.export": MagicMock(
                SimpleSpanProcessor=mock_processor_cls
            ),
            "openinference": MagicMock(),
            "openinference.instrumentation": MagicMock(),
            "openinference.instrumentation.langchain": MagicMock(
                LangChainInstrumentor=mock_instrumentor_cls
            ),
        }

        endpoint = "http://127.0.0.1:6006/v1/traces"

        with patch.dict("sys.modules", modules):
            # Re-import to pick up mocked modules
            import app.core.phoenix_tracing as mod
            mod._TRACING_INITIALIZED = False
            mod.setup_phoenix_tracing(endpoint)

        # Verify Resource was created with service name
        mock_resource_cls.create.assert_called_once_with(
            {"service.name": "tendercortex-backend"}
        )

        # Verify exporter was created with the endpoint
        mock_exporter_cls.assert_called_once_with(endpoint=endpoint)

        # Verify TracerProvider was created with the resource
        mock_provider_cls.assert_called_once_with(resource=mock_resource)

        # Verify span processor was added
        mock_provider.add_span_processor.assert_called_once_with(mock_processor)

        # Verify tracer provider was set globally
        mock_trace.set_tracer_provider.assert_called_once_with(mock_provider)

        # Verify LangChainInstrumentor was instantiated and instrument() called
        mock_instrumentor_cls.assert_called_once()
        mock_instrumentor.instrument.assert_called_once()


class TestSetupPhoenixTracingImportError:
    """Tests for graceful degradation when packages are missing (SC-PT-05)."""

    def test_catches_import_error_and_logs_warning(self):
        """setup_phoenix_tracing() should catch ImportError, log WARNING,
        and not raise when packages are missing (SC-PT-05)."""
        import app.core.phoenix_tracing as mod

        with patch.object(mod, "logger") as mock_logger:
            # Patch builtins.__import__ to raise ImportError for OTel packages
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

            def side_effect(name, *args, **kwargs):
                if name.startswith(("opentelemetry", "openinference")):
                    raise ImportError(f"No module named '{name}'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=side_effect):
                # Should NOT raise
                mod.setup_phoenix_tracing("http://127.0.0.1:6006/v1/traces")

            # Should have logged a warning about missing packages
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "tracing" in warning_msg.lower() or "instalados" in warning_msg.lower()


class TestSetupPhoenixTracingCustomEndpoint:
    """Tests for custom endpoint support (SC-PT-07)."""

    def test_uses_custom_endpoint_passed_as_argument(self):
        """setup_phoenix_tracing() should pass the custom endpoint to
        OTLPSpanExporter (SC-PT-07)."""
        mock_exporter_cls = MagicMock()

        modules = {
            "opentelemetry": MagicMock(),
            "opentelemetry.trace": MagicMock(),
            "opentelemetry.exporter.otlp.proto.http.trace_exporter": MagicMock(
                OTLPSpanExporter=mock_exporter_cls
            ),
            "opentelemetry.sdk.resources": MagicMock(),
            "opentelemetry.sdk.trace": MagicMock(),
            "opentelemetry.sdk.trace.export": MagicMock(),
            "openinference": MagicMock(),
            "openinference.instrumentation": MagicMock(),
            "openinference.instrumentation.langchain": MagicMock(),
        }

        custom_endpoint = "http://10.0.0.5:9999/v1/traces"

        with patch.dict("sys.modules", modules):
            import app.core.phoenix_tracing as mod
            mod._TRACING_INITIALIZED = False
            mod.setup_phoenix_tracing(custom_endpoint)

        mock_exporter_cls.assert_called_once_with(endpoint=custom_endpoint)


class TestSetupPhoenixTracingIdempotency:
    """Tests for idempotency guard (INV-PT-02)."""

    def test_second_call_is_noop(self):
        """Calling setup_phoenix_tracing() twice should not reconfigure (INV-PT-02)."""
        import app.core.phoenix_tracing as mod

        modules = {
            "opentelemetry": MagicMock(),
            "opentelemetry.trace": MagicMock(),
            "opentelemetry.exporter.otlp.proto.http.trace_exporter": MagicMock(),
            "opentelemetry.sdk.resources": MagicMock(),
            "opentelemetry.sdk.trace": MagicMock(),
            "opentelemetry.sdk.trace.export": MagicMock(),
            "openinference": MagicMock(),
            "openinference.instrumentation": MagicMock(),
            "openinference.instrumentation.langchain": MagicMock(),
        }

        with patch.dict("sys.modules", modules):
            mod._TRACING_INITIALIZED = False
            mod.setup_phoenix_tracing("http://127.0.0.1:6006/v1/traces")

            # Now set flag should be True
            assert mod._TRACING_INITIALIZED is True

            with patch.object(mod, "logger") as mock_logger:
                mod.setup_phoenix_tracing("http://127.0.0.1:6006/v1/traces")
                # Second call should log info about skipping, not reconfigure
                mock_logger.info.assert_called()
