"""
Quality Filter Interface
========================

Defines the contract for code quality filtering implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class IQualityFilter(ABC):
    """
    Interface for code quality filters.

    Quality filters analyze code and assign quality scores based on various metrics
    (complexity, documentation, structure, etc.).

    Example:
        >>> filter = RadonQualityFilter(min_score=60)
        >>> score = filter.calculate_score(code, 'python')
        >>> if filter.is_acceptable(code, 'python'):
        ...     print("Code meets quality threshold")
    """

    @abstractmethod
    def calculate_score(self, code: str, language: str) -> float:
        """
        Calculate quality score for given code.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Quality score from 0.0 (worst) to 100.0 (best)

        Example:
            >>> filter.calculate_score("def foo(): pass", "python")
            45.0  # Low score due to no docstring, simple code
        """
        pass

    @abstractmethod
    def is_acceptable(self, code: str, language: str, min_score: Optional[float] = None) -> bool:
        """
        Check if code meets minimum quality threshold.

        Args:
            code: Source code to check
            language: Programming language
            min_score: Minimum acceptable score (uses filter's default if None)

        Returns:
            True if code meets threshold, False otherwise

        Example:
            >>> filter.is_acceptable("def foo(): '''Doc'''\\n    pass", "python")
            True
        """
        pass

    @abstractmethod
    def get_metrics(self, code: str, language: str) -> Dict[str, float]:
        """
        Get detailed quality metrics for code.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Dictionary with metric names and values:
            - 'complexity': Cyclomatic complexity
            - 'maintainability': Maintainability index
            - 'documentation': Documentation coverage
            - 'structure': Code structure quality
            - 'overall': Overall quality score

        Example:
            >>> metrics = filter.get_metrics(code, 'python')
            >>> metrics['complexity']
            3.5
            >>> metrics['maintainability']
            75.0
        """
        pass

    @abstractmethod
    def get_min_score(self) -> float:
        """
        Get the minimum acceptable quality score for this filter.

        Returns:
            Minimum score threshold

        Example:
            >>> filter.get_min_score()
            60.0
        """
        pass

    @abstractmethod
    def set_min_score(self, score: float) -> None:
        """
        Set the minimum acceptable quality score.

        Args:
            score: New minimum score (0-100)

        Raises:
            ValueError: If score is not in valid range

        Example:
            >>> filter.set_min_score(70.0)
        """
        pass
