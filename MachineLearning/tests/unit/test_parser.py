"""
Unit tests for UniversalParser
"""

import pytest
from module.preprocessing.universal_parser_new import UniversalParser


class TestUniversalParser:
    """Test the universal code parser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return UniversalParser()

    @pytest.mark.unit
    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert hasattr(parser, 'parse_code')

    @pytest.mark.unit
    def test_parse_python_functions(self, parser, sample_python_code):
        """Test parsing Python functions."""
        result = parser.parse_code(sample_python_code, "python")

        assert result is not None
        assert 'functions' in result
        assert len(result['functions']) >= 1

        # Check first function structure
        func = result['functions'][0]
        assert 'name' in func
        assert 'code' in func
        assert func['name'] == 'calculate_sum'

    @pytest.mark.unit
    def test_parse_python_classes(self, parser, sample_python_code):
        """Test parsing Python classes."""
        result = parser.parse_code(sample_python_code, "python")

        assert result is not None
        assert 'classes' in result
        assert len(result['classes']) >= 1

        # Check class structure
        cls = result['classes'][0]
        assert 'name' in cls
        assert cls['name'] == 'Calculator'

    @pytest.mark.unit
    def test_parse_javascript(self, parser, sample_javascript_code):
        """Test parsing JavaScript code."""
        result = parser.parse_code(sample_javascript_code, "javascript")

        assert result is not None
        assert 'functions' in result
        assert len(result['functions']) >= 1

    @pytest.mark.unit
    def test_parse_empty_code(self, parser):
        """Test parsing empty code."""
        result = parser.parse_code("", "python")

        assert result is not None
        assert 'functions' in result
        assert len(result['functions']) == 0

    @pytest.mark.unit
    def test_parse_invalid_language(self, parser):
        """Test parsing with invalid language."""
        # Should handle gracefully or raise appropriate error
        try:
            result = parser.parse_code("def test(): pass", "invalid_lang")
            # If it doesn't raise, should return empty or None
            assert result is None or len(result.get('functions', [])) == 0
        except (ValueError, KeyError):
            # Expected behavior
            pass

    @pytest.mark.unit
    def test_parse_malformed_code(self, parser):
        """Test parsing syntactically incorrect code."""
        malformed = "def broken(:\n    pass"

        # Should handle gracefully
        try:
            result = parser.parse_code(malformed, "python")
            # If parsing succeeds despite syntax errors, that's OK
            # Tree-sitter is error-tolerant
            assert result is not None
        except Exception:
            # Also acceptable to raise an error
            pass
