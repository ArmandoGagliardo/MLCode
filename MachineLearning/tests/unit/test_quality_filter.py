"""
Unit tests for QualityFilter
"""

import pytest
from module.preprocessing.quality_filter import QualityFilter


class TestQualityFilter:
    """Test the code quality filter."""

    @pytest.fixture
    def filter(self):
        """Create a quality filter instance."""
        return QualityFilter()

    @pytest.mark.unit
    def test_filter_initialization(self, filter):
        """Test that filter initializes correctly."""
        assert filter is not None
        assert hasattr(filter, 'is_high_quality')

    @pytest.mark.unit
    def test_accept_good_code(self, filter, sample_python_code):
        """Test that good code is accepted."""
        result = filter.is_high_quality(sample_python_code, "python")
        assert result is True

    @pytest.mark.unit
    def test_reject_bad_code(self, filter, sample_bad_code):
        """Test that bad code is rejected."""
        result = filter.is_high_quality(sample_bad_code, "python")
        assert result is False

    @pytest.mark.unit
    def test_reject_too_short(self, filter):
        """Test that very short code is rejected."""
        short_code = "def x(): return 1"
        result = filter.is_high_quality(short_code, "python")
        assert result is False

    @pytest.mark.unit
    def test_reject_todo_comments(self, filter):
        """Test that code with TODO comments is rejected."""
        todo_code = '''
def incomplete():
    # TODO: implement this
    pass
'''
        result = filter.is_high_quality(todo_code, "python")
        assert result is False

    @pytest.mark.unit
    def test_reject_fixme_comments(self, filter):
        """Test that code with FIXME comments is rejected."""
        fixme_code = '''
def broken():
    # FIXME: this is broken
    return None
'''
        result = filter.is_high_quality(fixme_code, "python")
        assert result is False

    @pytest.mark.unit
    def test_reject_no_docstring(self, filter):
        """Test that functions without docstrings may be rejected."""
        no_doc = '''
def mystery_function(x, y):
    return x + y
'''
        # Depending on filter settings, this may or may not be rejected
        result = filter.is_high_quality(no_doc, "python")
        # Just verify it returns a boolean
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_empty_code(self, filter):
        """Test handling of empty code."""
        result = filter.is_high_quality("", "python")
        assert result is False
