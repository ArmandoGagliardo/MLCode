"""
Heuristic Quality Filter
=========================

Quality filter implementation using simple heuristics.
Migrated from module/preprocessing/code_quality_filter.py
"""

import re
import ast
import logging
from typing import Dict

from domain.interfaces.quality_filter import IQualityFilter

logger = logging.getLogger(__name__)


class HeuristicQualityFilter(IQualityFilter):
    """
    Heuristic-based quality filter for code.

    Uses simple, fast heuristics to assess code quality:
    - Length checks
    - Line count checks
    - Bad pattern detection (TODO, FIXME, etc.)
    - Complexity checks
    - Boilerplate detection
    - Syntax validation (Python only)

    Example:
        >>> filter = HeuristicQualityFilter(min_score=60.0)
        >>> code = "def add(a, b):\\n    return a + b"
        >>> score = filter.calculate_score(code, 'python')
        >>> assert score >= 60.0
    """

    def __init__(
        self,
        min_score: float = 60.0,
        min_length: int = 10,
        max_length: int = 10000,
        min_lines: int = 2,
        max_lines: int = 500
    ):
        """
        Initialize heuristic quality filter.

        Args:
            min_score: Minimum acceptable quality score (0-100)
            min_length: Minimum character length
            max_length: Maximum character length
            min_lines: Minimum number of lines
            max_lines: Maximum number of lines

        Example:
            >>> filter = HeuristicQualityFilter(min_score=70.0, min_lines=3)
        """
        self._min_score = min_score
        self._min_length = min_length
        self._max_length = max_length
        self._min_lines = min_lines
        self._max_lines = max_lines

        # Bad patterns (low quality indicators)
        self._bad_patterns = [
            r'TODO',
            r'FIXME',
            r'XXX',
            r'HACK',
            r'print\s*\(',  # Debug prints
            r'console\.log\(',  # Debug logs
            r'^\s*pass\s*$',  # Empty pass statements
            r'^\s*\.\.\.\s*$',  # Ellipsis placeholders
        ]

        # Compile regex patterns
        self._bad_regex = [re.compile(p, re.IGNORECASE) for p in self._bad_patterns]

        logger.debug(f"HeuristicQualityFilter initialized (min_score={min_score})")

    def calculate_score(self, code: str, language: str) -> float:
        """
        Calculate quality score using heuristics.

        Scoring breakdown (max 100 points):
        - Length valid: 20 points
        - Line count valid: 10 points
        - No bad patterns: 20 points
        - Has complexity: 20 points
        - Not boilerplate: 10 points
        - Meaningful content: 10 points
        - Valid syntax: 10 points

        Args:
            code: Source code to score
            language: Programming language

        Returns:
            Quality score from 0.0 to 100.0

        Example:
            >>> filter = HeuristicQualityFilter()
            >>> score = filter.calculate_score("def f(): return 42", 'python')
            >>> assert 0 <= score <= 100
        """
        if not code or not code.strip():
            return 0.0

        score = 0.0

        # Length (20 points)
        if self._is_valid_length(code):
            score += 20.0

        # Line count (10 points)
        if self._is_valid_line_count(code):
            score += 10.0

        # No bad patterns (20 points)
        if not self._has_bad_patterns(code):
            score += 20.0

        # Complexity (20 points)
        if self._has_sufficient_complexity(code, language):
            score += 20.0

        # Not boilerplate (10 points)
        if self._is_not_boilerplate(code):
            score += 10.0

        # Meaningful content (10 points)
        if self._has_meaningful_content(code):
            score += 10.0

        # Valid syntax (10 points - Python only)
        if language == 'python' and self._is_valid_python_syntax(code):
            score += 10.0
        elif language != 'python':
            # Give points for other languages (no syntax check)
            score += 10.0

        return score

    def is_acceptable(self, code: str, language: str, min_score: float = None) -> bool:
        """
        Check if code meets quality threshold.

        Args:
            code: Source code to check
            language: Programming language
            min_score: Minimum score (uses default if None)

        Returns:
            True if code passes quality check

        Example:
            >>> filter = HeuristicQualityFilter(min_score=60.0)
            >>> assert filter.is_acceptable("def f(): return 1", 'python')
        """
        threshold = min_score if min_score is not None else self._min_score
        score = self.calculate_score(code, language)
        return score >= threshold

    def get_min_score(self) -> float:
        """Get minimum quality score threshold."""
        return self._min_score

    def set_min_score(self, score: float) -> None:
        """Set minimum quality score threshold."""
        if score < 0 or score > 100:
            raise ValueError("Score must be between 0 and 100")
        self._min_score = score

    def get_metrics(self, code: str, language: str) -> Dict:
        """
        Get detailed quality metrics.

        Returns:
            Dictionary with individual metric scores

        Example:
            >>> filter = HeuristicQualityFilter()
            >>> metrics = filter.get_metrics("def f(): pass", 'python')
            >>> assert 'overall_score' in metrics
            >>> assert 'checks_passed' in metrics
        """
        checks = {
            'valid_length': self._is_valid_length(code),
            'valid_line_count': self._is_valid_line_count(code),
            'no_bad_patterns': not self._has_bad_patterns(code),
            'has_complexity': self._has_sufficient_complexity(code, language),
            'not_boilerplate': self._is_not_boilerplate(code),
            'meaningful_content': self._has_meaningful_content(code),
            'valid_syntax': self._is_valid_python_syntax(code) if language == 'python' else True,
        }

        checks_passed = sum(1 for v in checks.values() if v)

        return {
            'overall_score': self.calculate_score(code, language),
            'checks_passed': checks_passed,
            'total_checks': len(checks),
            'checks': checks,
            'language': language,
            'code_length': len(code),
            'code_lines': len([l for l in code.split('\n') if l.strip()]),
        }

    # Private helper methods (migrated from original)

    def _is_valid_length(self, code: str) -> bool:
        """Check if code length is within acceptable range."""
        length = len(code.strip())
        return self._min_length <= length <= self._max_length

    def _is_valid_line_count(self, code: str) -> bool:
        """Check if number of lines is within acceptable range."""
        lines = [line for line in code.split('\n') if line.strip()]
        num_lines = len(lines)
        return self._min_lines <= num_lines <= self._max_lines

    def _has_bad_patterns(self, code: str) -> bool:
        """Check if code contains bad patterns (TODO, FIXME, etc.)."""
        for pattern in self._bad_regex:
            if pattern.search(code):
                return True
        return False

    def _is_valid_python_syntax(self, code: str) -> bool:
        """Check if Python code has valid syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception as e:
            logger.debug(f"Error parsing Python code: {e}")
            return False

    def _has_sufficient_complexity(self, code: str, language: str) -> bool:
        """Check if code has sufficient complexity (not trivial)."""
        # Count unique tokens
        tokens = set(re.findall(r'\b\w+\b', code.lower()))

        if len(tokens) < 3:
            return False

        # Language-specific structure keywords
        structure_keywords_map = {
            'python': ['def', 'class', 'if', 'for', 'while', 'try', 'with', 'return', 'yield', 'async'],
            'javascript': ['function', 'class', 'if', 'for', 'while', 'try', 'return', 'async', '=>'],
            'java': ['class', 'if', 'for', 'while', 'try', 'return', 'new', 'void'],
            'cpp': ['class', 'if', 'for', 'while', 'try', 'return', 'new', 'void'],
            'go': ['func', 'if', 'for', 'switch', 'return', 'defer'],
            'rust': ['fn', 'impl', 'if', 'for', 'while', 'match', 'return'],
            'ruby': ['def', 'class', 'if', 'for', 'while', 'return', 'yield'],
        }

        keywords = structure_keywords_map.get(language.lower(), structure_keywords_map['python'])
        has_structure = any(keyword in code.lower() for keyword in keywords)

        return has_structure

    def _is_not_boilerplate(self, code: str) -> bool:
        """Check if code is not just boilerplate."""
        boilerplate_patterns = [
            r'if\s+__name__\s*==\s*["\']__main__["\']',
            r'^\s*import\s+\w+\s*$',
            r'^\s*from\s+\w+\s+import\s+\w+\s*$',
            r'^\s*#.*$',  # Just comments
        ]

        non_boilerplate_lines = []
        for line in code.split('\n'):
            line = line.strip()
            if not line:
                continue

            is_boilerplate = False
            for pattern in boilerplate_patterns:
                if re.match(pattern, line):
                    is_boilerplate = True
                    break

            if not is_boilerplate:
                non_boilerplate_lines.append(line)

        # Should have at least 2 non-boilerplate lines
        return len(non_boilerplate_lines) >= 2

    def _has_meaningful_content(self, code: str) -> bool:
        """Check if code has meaningful content."""
        lines = []
        in_docstring = False
        docstring_char = None

        for line in code.split('\n'):
            stripped = line.strip()

            # Check for docstring start/end
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in stripped else "'''"
                elif docstring_char in stripped:
                    in_docstring = False
                continue

            # Skip if in docstring or is comment
            if in_docstring or stripped.startswith('#'):
                continue

            # Skip empty lines
            if not stripped:
                continue

            lines.append(stripped)

        # Should have at least 1 meaningful line
        return len(lines) >= 1
