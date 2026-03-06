"""
Unit tests for Phoenix tracing integration in the FastAPI lifespan.

Tests that the lifespan function correctly handles the enable_phoenix_tracing
setting and gracefully catches exceptions from setup_phoenix_tracing().

Validates SC-PT-03, SC-PT-04, SC-PT-06.
"""

import os
import sys

import pytest
from unittest.mock import MagicMock, patch

# Dummy env vars so Settings() can be instantiated without a real .env file
_DUMMY_ENV = {
    "GROQ_API_KEY": "test-key-groq",
    "HUGGINGFACE_API_KEY": "test-key-hf",
}


@pytest.fixture(autouse=True)
def _env_and_fresh_import():
    """Set dummy env vars and ensure app.main is freshly imported each test."""
    with patch.dict(os.environ, _DUMMY_ENV):
        yield
    # Clean up app.main from sys.modules so next test starts fresh
    for mod in [k for k in sys.modules if k.startswith("app.main")]:
        del sys.modules[mod]


def _get_lifespan():
    """Import lifespan from app.main (may use cached module)."""
    from app.main import lifespan
    return lifespan


class TestLifespanTracingDisabled:
    """Tests that tracing is skipped when disabled (SC-PT-03, SC-PT-04)."""

    @pytest.mark.asyncio
    async def test_lifespan_does_not_call_setup_when_tracing_disabled(self):
        """When enable_phoenix_tracing is False, setup_phoenix_tracing
        should NOT be called (SC-PT-03, SC-PT-04)."""
        lifespan = _get_lifespan()

        mock_settings = MagicMock()
        mock_settings.enable_phoenix_tracing = False
        mock_settings.app_env = "development"

        mock_setup = MagicMock()
        mock_phoenix_mod = MagicMock()
        mock_phoenix_mod.setup_phoenix_tracing = mock_setup

        with patch("app.main.settings", mock_settings), \
             patch.dict(sys.modules, {"app.core.phoenix_tracing": mock_phoenix_mod}), \
             patch("app.main.get_rag_service"), \
             patch("app.main.asyncio.create_task"):
            async with lifespan(MagicMock()):
                pass

        mock_setup.assert_not_called()

    @pytest.mark.asyncio
    async def test_lifespan_skips_tracing_import_when_disabled(self):
        """When enable_phoenix_tracing is False, the phoenix_tracing module
        should not be imported at all (SC-PT-03)."""
        lifespan = _get_lifespan()

        mock_settings = MagicMock()
        mock_settings.enable_phoenix_tracing = False
        mock_settings.app_env = "development"

        phoenix_imported = False
        original_import = __import__

        def tracking_import(name, *args, **kwargs):
            nonlocal phoenix_imported
            if "phoenix_tracing" in str(name):
                phoenix_imported = True
            return original_import(name, *args, **kwargs)

        with patch("app.main.settings", mock_settings), \
             patch("app.main.get_rag_service"), \
             patch("app.main.asyncio.create_task"), \
             patch("builtins.__import__", side_effect=tracking_import):
            async with lifespan(MagicMock()):
                pass

        assert phoenix_imported is False, (
            "phoenix_tracing should NOT be imported when enable_phoenix_tracing is False"
        )


class TestLifespanTracingExceptionHandling:
    """Tests that lifespan catches exceptions from setup_phoenix_tracing (SC-PT-06)."""

    @pytest.mark.asyncio
    async def test_lifespan_catches_exception_from_setup_and_logs_warning(self):
        """When setup_phoenix_tracing() raises any exception, the lifespan
        should catch it, log a warning, and continue without crashing (SC-PT-06)."""
        lifespan = _get_lifespan()

        mock_settings = MagicMock()
        mock_settings.enable_phoenix_tracing = True
        mock_settings.phoenix_endpoint = "http://127.0.0.1:6006/v1/traces"
        mock_settings.app_env = "development"

        mock_setup = MagicMock(side_effect=RuntimeError("Unexpected tracing failure"))
        mock_phoenix_mod = MagicMock()
        mock_phoenix_mod.setup_phoenix_tracing = mock_setup

        mock_logger = MagicMock()

        with patch("app.main.settings", mock_settings), \
             patch.dict(sys.modules, {"app.core.phoenix_tracing": mock_phoenix_mod}), \
             patch("app.main.get_rag_service"), \
             patch("app.main.asyncio.create_task"), \
             patch("app.main.logger", mock_logger):
            async with lifespan(MagicMock()):
                pass

        mock_logger.warning.assert_called()
        warning_msg = str(mock_logger.warning.call_args)
        assert "tracing" in warning_msg.lower() or "Phoenix" in warning_msg

    @pytest.mark.asyncio
    async def test_lifespan_catches_import_error_from_setup(self):
        """When importing setup_phoenix_tracing raises ImportError,
        the lifespan should catch it and continue (SC-PT-06)."""
        lifespan = _get_lifespan()

        mock_settings = MagicMock()
        mock_settings.enable_phoenix_tracing = True
        mock_settings.phoenix_endpoint = "http://127.0.0.1:6006/v1/traces"
        mock_settings.app_env = "development"

        # Module whose attribute access raises ImportError
        class FailingModule:
            def __getattr__(self, name):
                raise ImportError("No module named 'app.core.phoenix_tracing'")

        mock_logger = MagicMock()

        # Remove real module from cache so the failing one is used
        sys.modules.pop("app.core.phoenix_tracing", None)

        with patch("app.main.settings", mock_settings), \
             patch.dict(sys.modules, {"app.core.phoenix_tracing": FailingModule()}), \
             patch("app.main.get_rag_service"), \
             patch("app.main.asyncio.create_task"), \
             patch("app.main.logger", mock_logger):
            async with lifespan(MagicMock()):
                pass

        mock_logger.warning.assert_called()
