"""
Parser Interface
================

Defines the contract for code parsers that extract structured information from source code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class IParser(ABC):
    """
    Interface for code parsers.

    Parsers extract structured information (functions, classes, etc.) from source code
    using various techniques (AST, tree-sitter, regex, etc.).

    Example:
        >>> parser = TreeSitterParser()
        >>> if parser.supports_language('python'):
        ...     samples = parser.parse(code, 'python')
    """

    @abstractmethod
    def parse(self, code: str, language: str, **options) -> List[Dict]:
        """
        Parse source code and extract structured information.

        Args:
            code: Source code to parse
            language: Programming language (e.g., 'python', 'javascript')
            **options: Additional parsing options:
                - extract_functions: bool = True
                - extract_classes: bool = False
                - extract_docstrings: bool = False
                - extract_context: bool = False (imports, parent class)

        Returns:
            List of dictionaries containing extracted code samples.
            Each dict should have at minimum:
            - 'name': str - Name of the function/class
            - 'code': str - The actual code
            - 'type': str - 'function', 'class', or 'file'
            - 'language': str - Programming language

        Raises:
            ValueError: If language is not supported
            ParsingError: If parsing fails

        Example:
            >>> samples = parser.parse("def foo(): pass", "python")
            >>> samples[0]['name']
            'foo'
        """
        pass

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if this parser supports the given language.

        Args:
            language: Programming language name

        Returns:
            True if language is supported, False otherwise

        Example:
            >>> parser.supports_language('python')
            True
            >>> parser.supports_language('cobol')
            False
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of all supported languages.

        Returns:
            List of supported language names

        Example:
            >>> parser.get_supported_languages()
            ['python', 'javascript', 'java', 'cpp', 'go']
        """
        pass
