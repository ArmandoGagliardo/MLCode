"""
Code Quality Filter

Filters code snippets based on quality metrics to ensure only good
training data is used. Checks for syntax, completeness, length, etc.

Version 1.2.0 - Added integration with AdvancedQualityFilter
"""

import re
import ast
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityFilter:
    """
    Filters code based on quality metrics.
    
    Can use either simple heuristics (fast) or advanced metrics (accurate).
    Set use_advanced=True to enable radon-based quality scoring.
    """

    def __init__(self,
                 min_length: int = 10,
                 max_length: int = 10000,
                 min_lines: int = 2,
                 max_lines: int = 500,
                 use_advanced: bool = False,
                 min_quality_score: int = 60):
        """
        Initialize quality filter.

        Args:
            min_length: Minimum character length
            max_length: Maximum character length
            min_lines: Minimum number of lines
            max_lines: Maximum number of lines
            use_advanced: Enable advanced quality metrics (requires radon)
            min_quality_score: Minimum score for advanced filter (0-100)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.use_advanced = use_advanced
        
        # Try to load advanced filter if requested
        self.advanced_filter = None
        if use_advanced:
            try:
                from module.preprocessing.advanced_quality_filter import AdvancedQualityFilter
                self.advanced_filter = AdvancedQualityFilter(min_score=min_quality_score)
                logger.info("✅ Advanced quality filter enabled (radon-based)")
            except ImportError:
                logger.warning("⚠️  Advanced filter requires 'radon'. Install: pip install radon")
                logger.warning("⚠️  Falling back to simple quality filter")
                self.use_advanced = False

        # Patterns to avoid (low quality indicators)
        self.bad_patterns = [
            r'TODO',
            r'FIXME',
            r'XXX',
            r'HACK',
            r'print\s*\(',  # Debug prints
            r'console\.log\(',  # Debug logs
            r'^\s*pass\s*$',  # Empty pass statements
            r'^\s*\.\.\.\s*$',  # Ellipsis placeholders
        ]

        # Compile patterns
        self.bad_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.bad_patterns]

    def is_valid_length(self, code: str) -> bool:
        """
        Check if code length is within acceptable range.

        Args:
            code: Code string to check

        Returns:
            True if valid length
        """
        length = len(code.strip())
        return self.min_length <= length <= self.max_length

    def is_valid_line_count(self, code: str) -> bool:
        """
        Check if number of lines is within acceptable range.

        Args:
            code: Code string to check

        Returns:
            True if valid line count
        """
        lines = [line for line in code.split('\n') if line.strip()]
        num_lines = len(lines)
        return self.min_lines <= num_lines <= self.max_lines

    def has_bad_patterns(self, code: str) -> bool:
        """
        Check if code contains bad patterns (TODO, FIXME, etc.).

        Args:
            code: Code string to check

        Returns:
            True if contains bad patterns
        """
        for pattern in self.bad_regex:
            if pattern.search(code):
                return True
        return False

    def is_valid_python_syntax(self, code: str) -> bool:
        """
        Check if Python code has valid syntax.

        Args:
            code: Python code string

        Returns:
            True if valid syntax
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception as e:
            logger.debug(f"Error parsing Python code: {e}")
            return False

    def has_sufficient_complexity(self, code: str, language: str = 'python') -> bool:
        """
        Check if code has sufficient complexity (not just trivial).

        Args:
            code: Code string to check
            language: Programming language (for language-specific keywords)

        Returns:
            True if sufficiently complex
        """
        # Count unique tokens (simple heuristic)
        tokens = set(re.findall(r'\b\w+\b', code.lower()))
        
        # Should have at least 3 unique tokens (relaxed from 5)
        if len(tokens) < 3:
            return False

        # Language-specific structure keywords (relaxed - include 'return')
        structure_keywords_map = {
            'python': ['def', 'class', 'if', 'for', 'while', 'try', 'with', 'return', 'yield', 'async', 'await', 'lambda'],
            'javascript': ['function', 'class', 'if', 'for', 'while', 'try', 'return', 'async', 'await', 'const', 'let', 'var', '=>'],
            'go': ['func', 'if', 'for', 'switch', 'return', 'defer', 'go', 'select', 'range'],
            'rust': ['fn', 'impl', 'if', 'for', 'while', 'match', 'return', 'loop', 'let', 'mut'],
            'java': ['class', 'if', 'for', 'while', 'try', 'return', 'new', 'void', 'public', 'private', 'protected'],
            'cpp': ['class', 'if', 'for', 'while', 'try', 'return', 'new', 'delete', 'void', 'int', 'public', 'private'],
            'ruby': ['def', 'class', 'if', 'for', 'while', 'begin', 'return', 'yield', 'end'],
        }
        
        keywords = structure_keywords_map.get(language, structure_keywords_map['python'])
        has_structure = any(keyword in code.lower() for keyword in keywords)

        return has_structure

    def is_not_boilerplate(self, code: str) -> bool:
        """
        Check if code is not just boilerplate.

        Args:
            code: Code string to check

        Returns:
            True if not boilerplate
        """
        # Common boilerplate patterns
        boilerplate_patterns = [
            r'if\s+__name__\s*==\s*["\']__main__["\']',
            r'^\s*import\s+\w+\s*$',
            r'^\s*from\s+\w+\s+import\s+\w+\s*$',
            r'^\s*#.*$',  # Just comments
        ]

        # If code is only boilerplate, reject
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

    def has_meaningful_content(self, code: str) -> bool:
        """
        Check if code has meaningful content.

        Args:
            code: Code string to check

        Returns:
            True if has meaningful content
        """
        # Remove comments and docstrings
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

        # Should have at least 1 meaningful line (relaxed from 2)
        return len(lines) >= 1

    def is_valid_code(self, code: str, language: str = 'python') -> bool:
        """
        Comprehensive code quality check.
        
        Uses advanced metrics if enabled (radon-based), otherwise simple heuristics.

        Args:
            code: Code string to check
            language: Programming language

        Returns:
            True if code passes all quality checks
        """
        if not code or not code.strip():
            return False
        
        # If advanced filter enabled and code is Python, use it
        if self.use_advanced and self.advanced_filter and language == 'python':
            try:
                return self.advanced_filter.is_valid_code(code)
            except Exception as e:
                logger.debug(f"Advanced filter failed: {e}, using simple checks")
                # Fall through to simple checks

        # Simple validation checks (heuristic-based)
        # Length checks
        if not self.is_valid_length(code):
            logger.debug("Code failed length check")
            return False

        if not self.is_valid_line_count(code):
            logger.debug("Code failed line count check")
            return False

        # Bad patterns
        if self.has_bad_patterns(code):
            logger.debug("Code contains bad patterns")
            return False

        # Complexity check (language-aware)
        if not self.has_sufficient_complexity(code, language):
            logger.debug("Code lacks sufficient complexity")
            return False

        # Boilerplate check
        if not self.is_not_boilerplate(code):
            logger.debug("Code is mostly boilerplate")
            return False

        # Meaningful content
        if not self.has_meaningful_content(code):
            logger.debug("Code lacks meaningful content")
            return False

        # Language-specific checks
        if language == 'python':
            if not self.is_valid_python_syntax(code):
                logger.debug("Invalid Python syntax")
                return False

        return True

    def get_quality_score(self, code: str, language: str = 'python') -> float:
        """
        Get a quality score for code (0.0 to 1.0).

        Args:
            code: Code string to score
            language: Programming language

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 10.0

        # Length (0-2 points)
        if self.is_valid_length(code):
            score += 2.0

        # Line count (0-1 points)
        if self.is_valid_line_count(code):
            score += 1.0

        # No bad patterns (0-2 points)
        if not self.has_bad_patterns(code):
            score += 2.0

        # Complexity (0-2 points)
        if self.has_sufficient_complexity(code):
            score += 2.0

        # Not boilerplate (0-1 points)
        if self.is_not_boilerplate(code):
            score += 1.0

        # Meaningful content (0-1 points)
        if self.has_meaningful_content(code):
            score += 1.0

        # Valid syntax (0-1 points)
        if language == 'python' and self.is_valid_python_syntax(code):
            score += 1.0

        return score / max_score

    def filter_functions(self, functions: List[Dict], language: str = 'python') -> List[Dict]:
        """
        Filter a list of functions by quality.

        Args:
            functions: List of function dictionaries
            language: Programming language

        Returns:
            Filtered list of high-quality functions
        """
        filtered = []

        for func in functions:
            code = func.get('body') or func.get('code') or func.get('output', '')
            
            if self.is_valid_code(code, language):
                filtered.append(func)

        logger.info(f"Filtered {len(functions)} -> {len(filtered)} functions")
        return filtered


# Example usage
if __name__ == "__main__":
    # Test quality filter
    filter = QualityFilter()

    # Good code
    good_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

    # Bad code (too short)
    bad_code1 = "pass"

    # Bad code (has TODO)
    bad_code2 = """
def process():
    # TODO: implement this
    pass
"""

    # Bad code (just boilerplate)
    bad_code3 = """
import sys
from os import path
"""

    print(f"Good code valid: {filter.is_valid_code(good_code)}")
    print(f"Good code score: {filter.get_quality_score(good_code):.2f}")
    
    print(f"\nBad code 1 valid: {filter.is_valid_code(bad_code1)}")
    print(f"Bad code 1 score: {filter.get_quality_score(bad_code1):.2f}")
    
    print(f"\nBad code 2 valid: {filter.is_valid_code(bad_code2)}")
    print(f"Bad code 2 score: {filter.get_quality_score(bad_code2):.2f}")
    
    print(f"\nBad code 3 valid: {filter.is_valid_code(bad_code3)}")
    print(f"Bad code 3 score: {filter.get_quality_score(bad_code3):.2f}")
