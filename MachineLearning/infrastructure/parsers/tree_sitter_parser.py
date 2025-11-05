"""
Tree-sitter Parser Implementation
==================================

Concrete implementation of IParser using tree-sitter for multi-language parsing.
Migrated from module/preprocessing/universal_parser_new.py to infrastructure layer.
"""

import logging
from typing import List, Dict, Optional
from tree_sitter import Language, Parser, Node

from domain.interfaces.parser import IParser
from domain.exceptions import ParsingError, ValidationError

logger = logging.getLogger(__name__)


class TreeSitterParser(IParser):
    """
    Tree-sitter based parser implementation for multiple programming languages.

    This implementation:
    - Uses tree-sitter library for AST-based parsing
    - Supports 8+ programming languages
    - Extracts functions, classes, and methods
    - Provides structured code information
    - Handles errors gracefully

    Supported Languages:
    - Python, JavaScript, Java, C++, Go, PHP, Ruby, Rust

    Example:
        >>> parser = TreeSitterParser()
        >>> code = "def hello():\n    return 'world'"
        >>> results = parser.parse(code, 'python')
        >>> assert len(results) == 1
        >>> assert results[0]['name'] == 'hello'
    """

    def __init__(self):
        """
        Initialize parser and load language grammars.

        Loads tree-sitter language bindings from pip packages.
        Gracefully handles missing language bindings.
        """
        self._languages: Dict[str, Language] = {}
        self._load_languages()

        if not self._languages:
            logger.error("No language parsers loaded! Install tree-sitter-* packages.")
        else:
            logger.info(f"TreeSitterParser initialized with {len(self._languages)} languages")

    def _load_languages(self) -> None:
        """Load available tree-sitter language bindings."""
        language_modules = {
            "python": ("tree_sitter_python", "Python"),
            "javascript": ("tree_sitter_javascript", "JavaScript"),
            "java": ("tree_sitter_java", "Java"),
            "cpp": ("tree_sitter_cpp", "C++"),
            "go": ("tree_sitter_go", "Go"),
            "php": ("tree_sitter_php", "PHP"),
            "ruby": ("tree_sitter_ruby", "Ruby"),
            "rust": ("tree_sitter_rust", "Rust"),
        }

        for lang_key, (module_name, display_name) in language_modules.items():
            try:
                # Dynamically import the language module
                module = __import__(module_name)

                # Get the language function - returns PyCapsule
                if hasattr(module, 'language'):
                    lang_capsule = module.language()
                    # Wrap PyCapsule with Language class for modern API
                    self._languages[lang_key] = Language(lang_capsule)
                    logger.debug(f"Loaded {display_name} parser")
                else:
                    logger.warning(f"{display_name}: no language() function found")

            except ImportError:
                logger.debug(f"{display_name} parser not available (install {module_name})")
            except Exception as e:
                logger.error(f"Error loading {display_name}: {e}")

    def parse(self, code: str, language: str, **options) -> List[Dict]:
        """
        Parse source code and extract structured information.

        Args:
            code: Source code to parse
            language: Programming language
            **options: Parsing options:
                - extract_functions: bool (default True)
                - extract_classes: bool (default False)
                - extract_methods: bool (default True)
                - extract_docstrings: bool (default True)

        Returns:
            List of extracted code units (functions, classes, methods)

        Raises:
            ParsingError: If parsing fails
            ValidationError: If inputs are invalid

        Example:
            >>> parser = TreeSitterParser()
            >>> code = "def add(a, b):\\n    return a + b"
            >>> results = parser.parse(code, 'python')
            >>> assert results[0]['name'] == 'add'
        """
        # Validate inputs
        if not code or not code.strip():
            raise ValidationError("Code cannot be empty")
        if not language:
            raise ValidationError("Language must be specified")

        # Check if language is supported
        lang = self._languages.get(language.lower())
        if not lang:
            available = list(self._languages.keys())
            raise ValidationError(
                f"Language '{language}' not supported. "
                f"Available: {', '.join(available)}"
            )

        try:
            # Create parser instance
            parser = Parser()
            parser.language = lang

            # Parse code
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node

            # Extract units based on options
            extract_classes = options.get('extract_classes', False)
            if extract_classes:
                return self._extract_classes(root, code, language)
            else:
                return self._extract_functions(root, code, language, options)

        except Exception as e:
            logger.error(f"Parsing failed for {language}: {e}", exc_info=True)
            raise ParsingError(f"Failed to parse {language} code: {e}")

    def _extract_functions(
        self,
        root: Node,
        code: str,
        language: str,
        options: Dict
    ) -> List[Dict]:
        """Extract functions and methods from AST."""
        results = []

        # Node type mappings for different languages
        kind_map = {
            "python": ["function_definition", "class_definition"],
            "cpp": ["function_definition", "class_specifier"],
            "java": ["method_declaration", "constructor_declaration", "class_declaration"],
            "javascript": ["function_declaration", "method_definition", "class_declaration", "arrow_function"],
            "php": ["function_definition", "class_declaration"],
            "go": ["function_declaration", "method_declaration"],
            "ruby": ["method"],
            "rust": ["function_item", "impl_item"],
        }

        target_kinds = kind_map.get(language.lower(), ["function_definition"])

        def walk(node: Node):
            """Recursively walk AST and extract target nodes."""
            # Check if this is a target node type
            if node.type in target_kinds:
                # Skip error nodes
                if not (node.is_missing or node.has_error):
                    # Extract function information
                    info = self._extract_function_info(node, code, language)

                    if info and self._is_valid_extraction(info):
                        results.append(info)

            # Recursively process children
            for child in node.children:
                walk(child)

        walk(root)
        return results

    def _extract_function_info(self, node: Node, code: str, language: str) -> Optional[Dict]:
        """Extract detailed information from a function node."""
        try:
            # Extract function name
            func_name = self._get_function_name(node, code, language)
            if not func_name:
                return None

            # Extract signature
            signature = self._get_function_signature(node, code, language)

            # Extract body
            body = self._get_function_body(node, code, language)
            if not body:
                return None

            # Extract docstring/comment
            docstring = self._get_docstring(node, code, language)

            # Determine type
            code_type = "class" if "class" in node.type else "function"

            # Create prompt
            prompt = docstring if docstring else f"Write a {language} function named '{func_name}'"

            # Combine signature and body
            full_code = self._format_function(signature, body, language)

            return {
                "task_type": "class_extraction" if code_type == "class" else "code_generation",
                "language": language,
                "func_name": func_name,
                "name": func_name,
                "signature": signature,
                "body": body,
                "doc": docstring or "",
                "input": prompt.strip(),
                "output": full_code.strip(),
            }

        except Exception as e:
            logger.debug(f"Error extracting function info: {e}")
            return None

    def _extract_classes(self, root: Node, code: str, language: str) -> List[Dict]:
        """Extract class definitions from AST."""
        classes = []

        class_types = {
            "python": "class_definition",
            "java": "class_declaration",
            "javascript": "class_declaration",
            "cpp": "class_specifier",
            "ruby": "class",
            "php": "class_declaration"
        }

        class_node_type = class_types.get(language.lower(), "class_definition")

        def find_classes(node: Node):
            if node.type == class_node_type:
                class_info = self._extract_class_info(node, code, language)
                if class_info:
                    classes.append(class_info)

            for child in node.children:
                find_classes(child)

        find_classes(root)
        return classes

    def _extract_class_info(self, node: Node, code: str, language: str) -> Optional[Dict]:
        """Extract detailed information from a class node."""
        try:
            # Extract class name
            class_name = None
            for child in node.children:
                if child.type in ["identifier", "name"]:
                    class_name = code[child.start_byte:child.end_byte]
                    break

            if not class_name:
                return None

            # Extract full class code
            class_code = code[node.start_byte:node.end_byte]

            # Extract docstring
            docstring = self._get_docstring(node, code, language)

            return {
                'task_type': 'class_definition',
                'language': language,
                'class_name': class_name,
                'name': class_name,
                'input': docstring or f"Write a {language} class named {class_name}",
                'output': class_code,
                'doc': docstring or "",
            }

        except Exception as e:
            logger.debug(f"Error extracting class info: {e}")
            return None

    def _get_function_name(self, node: Node, code: str, language: str) -> Optional[str]:
        """Extract function name from node."""
        for child in node.children:
            if child.type in ["identifier", "name", "property_identifier"]:
                name = code[child.start_byte:child.end_byte]
                # Validate name
                if name and name.isidentifier() and len(name) <= 50:
                    return name
        return None

    def _get_function_signature(self, node: Node, code: str, language: str) -> str:
        """Extract function signature."""
        # For most languages, extract up to the body
        for child in node.children:
            if child.type in ["block", "body", "suite"]:
                # Signature is everything before the body
                return code[node.start_byte:child.start_byte].strip()

        # Fallback: first line
        first_line = code[node.start_byte:node.end_byte].split('\n')[0]
        return first_line.strip()

    def _get_function_body(self, node: Node, code: str, language: str) -> Optional[str]:
        """Extract function body."""
        for child in node.children:
            if child.type in ["block", "body", "suite"]:
                return code[child.start_byte:child.end_byte].strip()
        return None

    def _get_docstring(self, node: Node, code: str, language: str) -> Optional[str]:
        """Extract docstring or documentation comment."""
        if language != "python":
            return None

        # Look for string literal as first statement
        for child in node.children:
            if child.type in ["block", "suite"]:
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr_child in stmt.children:
                            if expr_child.type == "string":
                                doc = code[expr_child.start_byte:expr_child.end_byte]
                                # Remove quotes
                                doc = doc.strip('"""\'\'\'')
                                return doc.strip()
        return None

    def _format_function(self, signature: str, body: str, language: str) -> str:
        """Format function with proper indentation."""
        if language == "python":
            # Ensure body is properly indented
            body_lines = body.strip().split('\n')
            indented_lines = []
            for line in body_lines:
                if line.strip():
                    # Add 4-space indentation if not already indented
                    if not line.startswith('    '):
                        indented_lines.append('    ' + line.lstrip())
                    else:
                        indented_lines.append(line)
                else:
                    indented_lines.append('')

            return signature + '\n' + '\n'.join(indented_lines)

        elif language == "ruby":
            # Ruby needs 'end' keyword
            body_lines = body.strip().split('\n')
            indented_lines = []
            for line in body_lines:
                if line.strip():
                    indented_lines.append('  ' + line.lstrip())
                else:
                    indented_lines.append('')

            result = signature + '\n' + '\n'.join(indented_lines)
            if not result.rstrip().endswith('end'):
                result += '\nend'
            return result

        else:
            # Default: signature + space + body
            return (signature + " " + body).strip()

    def _is_valid_extraction(self, info: Dict) -> bool:
        """Validate extracted function information."""
        if not info.get('name'):
            return False
        if not info.get('body'):
            return False

        name = info['name']
        # Check name validity
        if not name.isidentifier():
            return False
        if any(c in name for c in "():"):
            return False
        if len(name) > 50:
            return False

        return True

    def supports_language(self, language: str) -> bool:
        """
        Check if this parser supports the given language.

        Args:
            language: Programming language

        Returns:
            True if language is supported

        Example:
            >>> parser = TreeSitterParser()
            >>> assert parser.supports_language('python')
            >>> assert not parser.supports_language('cobol')
        """
        return language.lower() in self._languages

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages.

        Returns:
            List of language names

        Example:
            >>> parser = TreeSitterParser()
            >>> langs = parser.get_supported_languages()
            >>> assert 'python' in langs
        """
        return list(self._languages.keys())

    def validate_syntax(self, code: str, language: str) -> bool:
        """
        Validate code syntax without extracting functions.

        Args:
            code: Source code to validate
            language: Programming language

        Returns:
            True if syntax is valid, False otherwise

        Example:
            >>> parser = TreeSitterParser()
            >>> assert parser.validate_syntax('def f(): pass', 'python')
            >>> assert not parser.validate_syntax('def f(:', 'python')
        """
        if not self.supports_language(language):
            return False

        try:
            lang = self._languages[language.lower()]
            parser = Parser()
            parser.language = lang
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node

            # Check for errors
            return not root.has_error

        except Exception:
            return False

    def get_statistics(self) -> Dict:
        """
        Get parser statistics.

        Returns:
            Dictionary with statistics

        Example:
            >>> parser = TreeSitterParser()
            >>> stats = parser.get_statistics()
            >>> print(stats['languages_loaded'])
        """
        return {
            'parser_type': 'TreeSitter',
            'languages_loaded': len(self._languages),
            'supported_languages': self.get_supported_languages(),
        }
