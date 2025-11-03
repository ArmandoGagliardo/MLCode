"""
Integration tests for parser improvements
"""

import pytest
from module.preprocessing.universal_parser_enhanced import UniversalParserEnhanced, create_parser
from module.preprocessing.parser_improvements import InputValidator, CodeHasher


class TestEnhancedParser:
    """Test enhanced parser functionality."""

    @pytest.mark.integration
    def test_parser_with_metrics(self, sample_python_code):
        """Test parser with metrics enabled."""
        parser = UniversalParserEnhanced(enable_metrics=True, enable_caching=True)

        # Parse code multiple times
        for _ in range(3):
            result = parser.parse(sample_python_code, "python")
            assert isinstance(result, list)
            assert len(result) > 0

        # Check metrics
        metrics = parser.get_metrics()
        assert metrics is not None
        assert metrics.total_parses == 3
        assert metrics.successful_parses == 3
        assert metrics.functions_extracted > 0

    @pytest.mark.integration
    def test_parser_caching(self):
        """Test parser instance caching."""
        parser = UniversalParserEnhanced(enable_metrics=True, enable_caching=True)

        # Parse different languages
        parser.parse("def test(): pass", "python")
        parser.parse("function test() {}", "javascript")

        # Check cache stats
        cache_stats = parser.get_cache_stats()
        assert cache_stats is not None
        assert cache_stats['size'] == 2  # Two languages cached
        assert 'python' in cache_stats['languages']
        assert 'javascript' in cache_stats['languages']

    @pytest.mark.integration
    def test_input_validation(self):
        """Test input validation."""
        parser = UniversalParserEnhanced()

        # Valid input
        result = parser.parse("def test(): pass", "python")
        assert len(result) >= 0

        # Empty input
        result = parser.parse("", "python")
        assert len(result) == 0

        # Invalid language
        result = parser.parse("def test(): pass", "invalid_lang")
        assert len(result) == 0

        # Check metrics recorded failures
        metrics = parser.get_metrics()
        assert metrics.failed_parses >= 2  # Empty code + invalid language

    @pytest.mark.integration
    def test_batch_parsing(self, sample_python_code, sample_javascript_code):
        """Test batch parsing functionality."""
        parser = UniversalParserEnhanced()

        codes = [
            (sample_python_code, "python"),
            (sample_javascript_code, "javascript"),
            ("def another(): return 42", "python")
        ]

        results = parser.parse_batch(codes)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
        assert len(results[0]) > 0  # Python code should have functions
        assert len(results[1]) > 0  # JavaScript code should have functions

    @pytest.mark.integration
    def test_code_hashing(self, sample_python_code):
        """Test code hashing functionality."""
        parser = UniversalParserEnhanced()

        results1, hash1 = parser.parse_with_hash(sample_python_code, "python")
        results2, hash2 = parser.parse_with_hash(sample_python_code, "python")

        # Same code should have same hash
        assert hash1 == hash2

        # Different code should have different hash
        results3, hash3 = parser.parse_with_hash("def other(): pass", "python")
        assert hash1 != hash3

    @pytest.mark.integration
    def test_metrics_summary(self, sample_python_code, sample_javascript_code):
        """Test metrics summary generation."""
        parser = UniversalParserEnhanced(enable_metrics=True)

        # Parse multiple times
        parser.parse(sample_python_code, "python")
        parser.parse(sample_javascript_code, "javascript")
        parser.parse("def test(): pass", "python")

        # Get summary
        summary = parser.get_metrics().get_summary()

        assert summary['total_parses'] == 3
        assert 'languages' in summary
        assert 'python' in summary['languages']
        assert 'javascript' in summary['languages']
        assert summary['languages']['python']['parses'] == 2

    @pytest.mark.integration
    def test_parser_factory(self):
        """Test parser factory function."""
        # Enhanced parser
        parser1 = create_parser(enhanced=True, enable_metrics=True)
        assert isinstance(parser1, UniversalParserEnhanced)
        assert parser1.enable_metrics is True

        # Base parser
        from module.preprocessing.universal_parser_new import UniversalParser
        parser2 = create_parser(enhanced=False)
        assert isinstance(parser2, UniversalParser)
        assert not isinstance(parser2, UniversalParserEnhanced)


class TestInputValidator:
    """Test input validator functionality."""

    @pytest.mark.integration
    def test_validate_code(self):
        """Test code validation."""
        validator = InputValidator()

        # Valid code
        is_valid, error = validator.validate_code("def test(): pass")
        assert is_valid is True
        assert error is None

        # Empty code
        is_valid, error = validator.validate_code("")
        assert is_valid is False
        assert "empty" in error.lower()

        # Invalid type
        is_valid, error = validator.validate_code(123)
        assert is_valid is False
        assert "string" in error.lower()

    @pytest.mark.integration
    def test_validate_language(self):
        """Test language validation."""
        validator = InputValidator()
        supported = ["python", "javascript", "java"]

        # Valid language
        is_valid, error = validator.validate_language("python", supported)
        assert is_valid is True
        assert error is None

        # Invalid language
        is_valid, error = validator.validate_language("cobol", supported)
        assert is_valid is False
        assert "not supported" in error.lower()

        # Empty language
        is_valid, error = validator.validate_language("", supported)
        assert is_valid is False

    @pytest.mark.integration
    def test_sanitize_code(self):
        """Test code sanitization."""
        validator = InputValidator()

        # Code with different line endings
        code = "def test():\r\n    return 42\r"
        sanitized = validator.sanitize_code(code)

        assert "\r\n" not in sanitized
        assert "\r" not in sanitized
        assert "\n" in sanitized


class TestCodeHasher:
    """Test code hashing functionality."""

    @pytest.mark.integration
    def test_compute_hash(self):
        """Test hash computation."""
        code = "def test(): pass"

        hash1 = CodeHasher.compute_hash(code, 'sha256')
        hash2 = CodeHasher.compute_hash(code, 'sha256')

        # Same code should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 is 64 hex characters

        # Different algorithms
        hash_md5 = CodeHasher.compute_hash(code, 'md5')
        assert len(hash_md5) == 32  # MD5 is 32 hex characters
        assert hash1 != hash_md5

    @pytest.mark.integration
    def test_normalized_hash(self):
        """Test normalized hashing (whitespace insensitive)."""
        code1 = "def test(): pass"
        code2 = "def test():pass"
        code3 = "def test():\n    pass"

        # These should all have the same normalized hash
        hash1 = CodeHasher.compute_normalized_hash(code1)
        hash2 = CodeHasher.compute_normalized_hash(code2)
        hash3 = CodeHasher.compute_normalized_hash(code3)

        assert hash1 == hash2 == hash3

        # Different code should have different hash
        code4 = "def other(): pass"
        hash4 = CodeHasher.compute_normalized_hash(code4)
        assert hash1 != hash4
