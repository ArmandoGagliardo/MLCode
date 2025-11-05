"""
AST Duplicate Manager
=====================

Duplicate manager using AST-based hashing.
Migrated from module/utils/duplicate_manager.py
"""

import hashlib
import json
import ast
import logging
from pathlib import Path
from typing import List, Optional

from domain.interfaces.duplicate_manager import IDuplicateManager

logger = logging.getLogger(__name__)


class ASTDuplicateManager(IDuplicateManager):
    """
    AST-based duplicate detection for code.

    Uses Abstract Syntax Tree parsing to detect duplicates
    while ignoring superficial differences:
    - Whitespace and formatting
    - Comments
    - Variable naming (optional)

    Example:
        >>> manager = ASTDuplicateManager()
        >>> code1 = "def f(x): return x+1"
        >>> code2 = "def f(x):\\n    # Add one\\n    return x + 1"
        >>> manager.add_item(code1, 'python')
        >>> assert manager.is_duplicate(code2, 'python')  # Same AST!
    """

    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize AST duplicate manager.

        Args:
            cache_path: Path to cache file (None = no caching)

        Example:
            >>> manager = ASTDuplicateManager(cache_path='data/duplicates.json')
        """
        self._hashes = set()
        self._duplicate_count = 0
        self._cache_path = Path(cache_path) if cache_path else None

        if self._cache_path and self._cache_path.exists():
            self.load_cache(str(self._cache_path))

        logger.debug(f"ASTDuplicateManager initialized (cache={bool(cache_path)})")

    def is_duplicate(self, code: str, language: Optional[str] = None) -> bool:
        """
        Check if code is a duplicate using AST hashing.

        Args:
            code: Source code to check
            language: Programming language (used for AST parsing)

        Returns:
            True if duplicate found

        Example:
            >>> manager = ASTDuplicateManager()
            >>> assert not manager.is_duplicate("def f(): pass", 'python')
        """
        code_hash = self._generate_ast_hash(code, language)
        is_dup = code_hash in self._hashes

        if is_dup:
            self._duplicate_count += 1

        return is_dup

    def add_item(self, code: str, language: Optional[str] = None) -> None:
        """
        Add code to duplicate tracking.

        Args:
            code: Source code
            language: Programming language

        Example:
            >>> manager = ASTDuplicateManager()
            >>> manager.add_item("def f(): return 42", 'python')
        """
        code_hash = self._generate_ast_hash(code, language)
        self._hashes.add(code_hash)

    def add_batch(self, codes: List[str], language: Optional[str] = None) -> int:
        """
        Add multiple codes, returning count of unique items added.

        Args:
            codes: List of source codes
            language: Programming language

        Returns:
            Number of unique items added

        Example:
            >>> manager = ASTDuplicateManager()
            >>> added = manager.add_batch(["def f(): pass", "def g(): pass"], 'python')
            >>> assert added == 2
        """
        count = 0
        for code in codes:
            if not self.is_duplicate(code, language):
                self.add_item(code, language)
                count += 1
        return count

    def clear(self) -> None:
        """Clear all tracked duplicates."""
        self._hashes.clear()
        self._duplicate_count = 0

    def get_count(self) -> int:
        """Get count of unique items tracked."""
        return len(self._hashes)

    def get_duplicate_count(self) -> int:
        """Get count of duplicates found."""
        return self._duplicate_count

    def load_cache(self, cache_path: str) -> bool:
        """
        Load duplicate cache from file.

        Args:
            cache_path: Path to cache file

        Returns:
            True if successful

        Example:
            >>> manager = ASTDuplicateManager()
            >>> manager.load_cache('data/duplicates.json')
        """
        try:
            path = Path(cache_path)
            if not path.exists():
                return False

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._hashes = set(data.get('hashes', []))
                self._duplicate_count = data.get('duplicate_count', 0)

            logger.info(f"Loaded {len(self._hashes)} hashes from cache")
            return True

        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return False

    def save_cache(self, cache_path: str) -> bool:
        """
        Save duplicate cache to file.

        Args:
            cache_path: Path to cache file

        Returns:
            True if successful

        Example:
            >>> manager = ASTDuplicateManager()
            >>> manager.save_cache('data/duplicates.json')
        """
        try:
            path = Path(cache_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'hashes': list(self._hashes),
                'duplicate_count': self._duplicate_count,
            }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self._hashes)} hashes to cache")
            return True

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False

    # Private methods

    def _generate_ast_hash(self, code: str, language: Optional[str]) -> str:
        """Generate AST-based hash for code."""
        # Only Python supported for AST parsing currently
        if language != 'python':
            return self._generate_simple_hash(code)

        try:
            # Parse to AST
            tree = ast.parse(code)

            # Unparse to normalized form (removes formatting)
            normalized = ast.unparse(tree)

            # Further normalization
            normalized = normalized.replace(' ', '').replace('\n', '').lower()

            # Generate hash
            return hashlib.md5(normalized.encode('utf-8')).hexdigest()

        except (SyntaxError, Exception) as e:
            # Fallback to simple hash
            logger.debug(f"AST parsing failed, using simple hash: {e}")
            return self._generate_simple_hash(code)

    def _generate_simple_hash(self, code: str) -> str:
        """Generate simple hash for non-Python or unparseable code."""
        normalized = code.strip().replace(' ', '').replace('\n', '').lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
