"""
Duplicate Manager Interface
============================

Defines the contract for duplicate detection implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set


class IDuplicateManager(ABC):
    """
    Interface for duplicate detection managers.

    Duplicate managers track code samples to prevent duplicates in datasets.
    They can use various strategies (hash-based, AST-based, similarity-based).

    Example:
        >>> dedup = ASTDuplicateManager()
        >>> if not dedup.is_duplicate(code):
        ...     dedup.add_item(code)
        ...     dataset.append(code)
    """

    @abstractmethod
    def is_duplicate(self, code: str, language: Optional[str] = None) -> bool:
        """
        Check if code is a duplicate of previously seen code.

        Args:
            code: Source code to check
            language: Programming language (used for AST-based deduplication)

        Returns:
            True if code is duplicate, False if it's unique

        Example:
            >>> dedup.is_duplicate("def foo(): pass")
            False
            >>> dedup.add_item("def foo(): pass")
            >>> dedup.is_duplicate("def foo(): pass")
            True
        """
        pass

    @abstractmethod
    def add_item(self, code: str, language: Optional[str] = None) -> None:
        """
        Add code to the duplicate tracking system.

        Args:
            code: Source code to track
            language: Programming language

        Example:
            >>> dedup.add_item("def foo(): pass", "python")
        """
        pass

    @abstractmethod
    def add_batch(self, codes: List[str], language: Optional[str] = None) -> None:
        """
        Add multiple code samples in batch (more efficient).

        Args:
            codes: List of source code strings
            language: Programming language

        Example:
            >>> dedup.add_batch(["def foo(): pass", "def bar(): return 1"], "python")
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all tracked items.

        Example:
            >>> dedup.clear()
            >>> dedup.get_count()
            0
        """
        pass

    @abstractmethod
    def get_count(self) -> int:
        """
        Get number of unique items tracked.

        Returns:
            Count of unique code samples

        Example:
            >>> dedup.get_count()
            1523
        """
        pass

    @abstractmethod
    def save_cache(self, path: str) -> None:
        """
        Save duplicate tracking state to file.

        Args:
            path: Path to cache file

        Example:
            >>> dedup.save_cache('cache/duplicates.json')
        """
        pass

    @abstractmethod
    def load_cache(self, path: str) -> int:
        """
        Load duplicate tracking state from file.

        Args:
            path: Path to cache file

        Returns:
            Number of items loaded

        Example:
            >>> count = dedup.load_cache('cache/duplicates.json')
            >>> print(f"Loaded {count} items from cache")
        """
        pass

    @abstractmethod
    def get_duplicate_count(self) -> int:
        """
        Get number of duplicates detected.

        Returns:
            Total number of duplicates found

        Example:
            >>> dedup.get_duplicate_count()
            45
        """
        pass
