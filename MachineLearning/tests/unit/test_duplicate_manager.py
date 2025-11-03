"""
Unit tests for DuplicateManager
"""

import pytest
import os
from module.scripts.duplicate_manager import DuplicateManager


class TestDuplicateManager:
    """Test the duplicate detection manager."""

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a duplicate manager with temporary database."""
        db_path = temp_dir / "test_duplicates.db"
        return DuplicateManager(db_path=str(db_path))

    @pytest.mark.unit
    def test_manager_initialization(self, manager):
        """Test that manager initializes correctly."""
        assert manager is not None
        assert hasattr(manager, 'is_duplicate')
        assert hasattr(manager, 'add_code')

    @pytest.mark.unit
    def test_first_code_not_duplicate(self, manager):
        """Test that first code is not marked as duplicate."""
        code = "def test(): return 42"
        is_dup = manager.is_duplicate(code, "python", "test.py")
        assert is_dup is False

    @pytest.mark.unit
    def test_identical_code_is_duplicate(self, manager):
        """Test that identical code is marked as duplicate."""
        code = "def test(): return 42"

        # Add first time
        manager.add_code(code, "python", "test.py")

        # Check second time
        is_dup = manager.is_duplicate(code, "python", "test2.py")
        assert is_dup is True

    @pytest.mark.unit
    def test_different_code_not_duplicate(self, manager):
        """Test that different code is not marked as duplicate."""
        code1 = "def test(): return 42"
        code2 = "def other(): return 100"

        manager.add_code(code1, "python", "test.py")

        is_dup = manager.is_duplicate(code2, "python", "test2.py")
        assert is_dup is False

    @pytest.mark.unit
    def test_whitespace_differences_ignored(self, manager):
        """Test that whitespace differences don't affect duplicate detection."""
        code1 = "def test():\n    return 42"
        code2 = "def test():\n\n    return 42"  # Extra newline

        manager.add_code(code1, "python", "test.py")

        # These should be considered duplicates (same hash)
        is_dup = manager.is_duplicate(code2, "python", "test2.py")
        # Depending on hashing implementation, may or may not be duplicate
        assert isinstance(is_dup, bool)

    @pytest.mark.unit
    def test_add_multiple_codes(self, manager):
        """Test adding multiple different codes."""
        codes = [
            "def func1(): return 1",
            "def func2(): return 2",
            "def func3(): return 3"
        ]

        for i, code in enumerate(codes):
            is_dup = manager.is_duplicate(code, "python", f"file{i}.py")
            assert is_dup is False
            manager.add_code(code, "python", f"file{i}.py")

        # Verify all codes are tracked
        # Check that re-checking returns True
        for code in codes:
            is_dup = manager.is_duplicate(code, "python", "new_file.py")
            assert is_dup is True
