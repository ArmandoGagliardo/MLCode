"""
Unit tests for Configuration
"""

import pytest


class TestConfiguration:
    """Test configuration loading and values."""

    @pytest.mark.unit
    def test_config_imports(self):
        """Test that config module imports without errors."""
        from config import (
            STORAGE_TYPE,
            SUPPORTED_LANGUAGES,
            DEFAULT_MODEL,
            MAX_SEQUENCE_LENGTH,
            USE_GPU
        )

        # Verify imports succeeded
        assert STORAGE_TYPE is not None
        assert SUPPORTED_LANGUAGES is not None
        assert DEFAULT_MODEL is not None
        assert MAX_SEQUENCE_LENGTH is not None
        assert USE_GPU is not None

    @pytest.mark.unit
    def test_supported_languages(self):
        """Test that supported languages are properly configured."""
        from config import SUPPORTED_LANGUAGES

        assert isinstance(SUPPORTED_LANGUAGES, (list, tuple, set))
        assert len(SUPPORTED_LANGUAGES) > 0
        assert "python" in SUPPORTED_LANGUAGES

    @pytest.mark.unit
    def test_default_model(self):
        """Test that default model is a valid string."""
        from config import DEFAULT_MODEL

        assert isinstance(DEFAULT_MODEL, str)
        assert len(DEFAULT_MODEL) > 0
        # Should be a HuggingFace model name
        assert "/" in DEFAULT_MODEL or DEFAULT_MODEL.startswith("gpt")

    @pytest.mark.unit
    def test_max_sequence_length(self):
        """Test that max sequence length is reasonable."""
        from config import MAX_SEQUENCE_LENGTH

        assert isinstance(MAX_SEQUENCE_LENGTH, int)
        assert MAX_SEQUENCE_LENGTH > 0
        assert MAX_SEQUENCE_LENGTH <= 8192  # Reasonable upper bound

    @pytest.mark.unit
    def test_storage_type(self):
        """Test that storage type is valid."""
        from config import STORAGE_TYPE

        valid_types = ["local", "s3", "spaces", "b2", "wasabi", "r2"]
        assert STORAGE_TYPE.lower() in valid_types

    @pytest.mark.unit
    def test_gpu_setting(self):
        """Test that GPU setting is boolean."""
        from config import USE_GPU

        assert isinstance(USE_GPU, bool)
