"""
Unit tests for Phoenix observability configuration fields.

Validates SC-PT-08 (Pydantic V2 compliance) and REQ-PT-01 (configuration fields).
"""

import pytest
from unittest.mock import patch


class TestPhoenixConfigDefaults:
    """Tests for Phoenix-related Settings defaults."""

    def test_enable_phoenix_tracing_defaults_to_false(self):
        """Settings without ENABLE_PHOENIX_TRACING should default to False (SC-PT-08, REQ-PT-01)."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "test-key",
                "HUGGINGFACE_API_KEY": "test-hf-key",
            },
            clear=True,
        ):
            from app.core.config import Settings

            s = Settings()
            assert s.enable_phoenix_tracing is False

    def test_phoenix_endpoint_defaults_to_localhost(self):
        """Settings without PHOENIX_ENDPOINT should default to local Phoenix URL (SC-PT-08, REQ-PT-01)."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "test-key",
                "HUGGINGFACE_API_KEY": "test-hf-key",
            },
            clear=True,
        ):
            from app.core.config import Settings

            s = Settings()
            assert s.phoenix_endpoint == "http://127.0.0.1:6006/v1/traces"

    def test_enable_phoenix_tracing_from_env_var(self):
        """Settings should read ENABLE_PHOENIX_TRACING from environment (REQ-PT-01)."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "test-key",
                "HUGGINGFACE_API_KEY": "test-hf-key",
                "ENABLE_PHOENIX_TRACING": "true",
            },
            clear=True,
        ):
            from app.core.config import Settings

            s = Settings()
            assert s.enable_phoenix_tracing is True

    def test_phoenix_endpoint_from_env_var(self):
        """Settings should read PHOENIX_ENDPOINT from environment (REQ-PT-01)."""
        custom_endpoint = "http://10.0.0.5:9999/v1/traces"
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "test-key",
                "HUGGINGFACE_API_KEY": "test-hf-key",
                "PHOENIX_ENDPOINT": custom_endpoint,
            },
            clear=True,
        ):
            from app.core.config import Settings

            s = Settings()
            assert s.phoenix_endpoint == custom_endpoint
