"""
Universal Parser using modern tree-sitter API (>= 0.20.0).
Uses pre-built language bindings from pip packages.
"""

from tree_sitter import Language, Parser, Node
from .parsers.base_parser import BaseParser
from .function_parser import FunctionExtractor
from typing import List, Dict, Optional
import logging
import textwrap

logger = logging.getLogger(__name__)


class UniversalParser(BaseParser):
    """
    Universal parser using tree-sitter for multiple languages.
    Updated for modern tree-sitter API with pip-installed language bindings.
    """

    def __init__(self):
        """Initialize parser with available languages."""
        self.languages = {}
        self._load_languages()

    def _load_languages(self):
        """Load available tree-sitter language bindings."""

        # Try to import each language binding
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
                    # Wrap PyCapsule with Language class for new API
                    self.languages[lang_key] = Language(lang_capsule)
                    logger.info(f"[OK] Loaded {display_name} parser")
                else:
                    logger.warning(f"[WARNING] {display_name}: no language() function found")
            except ImportError:
                logger.warning(f"[WARNING] {display_name} parser not available. Install {module_name}")
            except Exception as e:
                logger.error(f"[ERROR] Error loading {display_name}: {e}")

        if not self.languages:
            logger.error("[ERROR] No language parsers available! Install tree-sitter-* packages.")
        else:
            logger.info(f"[INFO] Loaded {len(self.languages)} language parsers")

    def parse(self, code: str, language: str) -> List[Dict]:
        """
        Parse code and extract functions/classes.

        Args:
            code: Source code to parse
            language: Programming language name

        Returns:
            List of dictionaries with extracted code units
        """
        lang = self.languages.get(language)
        if not lang:
            logger.warning(f"Language '{language}' not supported. Available: {list(self.languages.keys())}")
            return []

        try:
            parser = Parser()
            # Modern tree-sitter API (0.20+): use parser.language instead of parser.set_language
            parser.language = lang
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node

            return self._extract_units(root, code, language)

        except Exception as e:
            logger.error(f"Error parsing {language} code: {e}")
            return []

    def _extract_units(self, root: Node, code: str, language: str) -> List[Dict]:
        """Extract functions and classes from parsed tree."""
        results = []

        # Node type mappings for different languages
        kind_map = {
            "python": ["function_definition", "class_definition"],
            "cpp": ["function_definition", "class_specifier"],
            "java": ["method_declaration", "constructor_declaration", "class_declaration"],
            "javascript": ["function_declaration", "method_definition", "class_declaration", "arrow_function"],
            "php": ["function_definition", "class_declaration"],
            "go": ["function_declaration", "method_declaration"],
            "ruby": ["method"],  # Only extract methods, not classes (classes are traversed for nested methods)
            "rust": ["function_item", "impl_item"],
        }

        extractor = FunctionExtractor(code)
        target_kinds = kind_map.get(language, ["function_definition"])

        def walk(node: Node):
            """Recursively walk the AST and extract target nodes."""

            # Extract if this is a target node type
            extracted = False
            if node.type in target_kinds:
                # Skip error nodes
                if not (node.is_missing or node.has_error):
                    # Extract function/class information
                    info = extractor.extract(node, language)
                    if info and info.get("name") and info.get("body"):
                        # Validate function name
                        name = info["name"]
                        if name.isidentifier() and not any(c in name for c in "():") and len(name) <= 50:
                            # Valid extraction - add to results
                            extracted = True
                            
                            # Determine task type
                            task_type = "class_extraction" if "class" in node.type else "code_generation"

                            # Create prompt (in English for consistency)
                            prompt = info.get("doc", "")
                            if not prompt:
                                args = info.get("args", "")
                                prompt = f"Write a {language} function called '{name}'"
                                if args:
                                    prompt += f" with arguments: {args}"

                            # Prepare full function code with proper indentation
                            signature = info.get("signature", "")
                            body = info["body"]
                            
                            # For Python, combine signature and body correctly preserving newlines
                            if language == "python" and signature and '\n' in body:
                                # The body might have mixed indentation (e.g., docstring at level 0, code at level 4)
                                # We need to ensure all lines have consistent 4-space indentation
                                body_lines = body.split('\n')
                                
                                # Find minimum non-zero indentation (excluding first line if it's a docstring)
                                min_indent = None
                                for i, line in enumerate(body_lines):
                                    if line.strip() and not (i == 0 and line.strip().startswith('"""')):
                                        leading = len(line) - len(line.lstrip())
                                        if leading > 0:
                                            if min_indent is None or leading < min_indent:
                                                min_indent = leading
                                
                                if min_indent is None:
                                    min_indent = 0
                                
                                # Reindent: remove min_indent, add 4 spaces
                                indented_lines = []
                                for line in body_lines:
                                    if line.strip():
                                        # Remove min_indent if present
                                        if len(line) >= min_indent and line[:min_indent].isspace():
                                            clean_line = line[min_indent:]
                                        else:
                                            clean_line = line.lstrip()
                                        indented_lines.append('    ' + clean_line)
                                    else:
                                        indented_lines.append('')
                                
                                indented_body = '\n'.join(indented_lines).rstrip()
                                full_code = signature + '\n' + indented_body
                            
                            # For Ruby, always format with proper structure and add 'end'
                            elif language == "ruby" and signature:
                                # Ruby methods need proper formatting with 'end' keyword
                                indent_size = 2
                                body_lines = body.split('\n') if '\n' in body else [body]
                                
                                # Find minimum non-zero indentation
                                min_indent = None
                                for line in body_lines:
                                    if line.strip():
                                        leading = len(line) - len(line.lstrip())
                                        if leading > 0:
                                            if min_indent is None or leading < min_indent:
                                                min_indent = leading
                                
                                if min_indent is None:
                                    min_indent = 0
                                
                                # Reindent: remove min_indent, add 2 spaces
                                indented_lines = []
                                for line in body_lines:
                                    if line.strip():
                                        # Remove min_indent if present
                                        if len(line) >= min_indent and line[:min_indent].isspace():
                                            clean_line = line[min_indent:]
                                        else:
                                            clean_line = line.lstrip()
                                        indented_lines.append(' ' * indent_size + clean_line)
                                    else:
                                        indented_lines.append('')
                                
                                indented_body = '\n'.join(indented_lines).rstrip()
                                
                                # Add 'end' keyword if not present
                                if not indented_body.rstrip().endswith('end'):
                                    full_code = signature + '\n' + indented_body + '\nend'
                                else:
                                    full_code = signature + '\n' + indented_body
                            
                            else:
                                full_code = (signature + " " + body).strip()
                            
                            # Add to results with both old and new formats for compatibility
                            results.append({
                                "task_type": task_type,
                                "language": language,
                                "func_name": name,
                                "name": name,  # Also add 'name' field for github_repo_processor
                                "body": body,  # Keep original body for reference
                                "signature": signature,
                                "doc": info.get("doc", ""),  # Include extracted docstring/comment
                                "input": prompt.strip(),
                                "output": full_code.strip()
                            })

            # Always recursively process children, even if extraction failed
            # This allows finding nested functions/methods
            for child in node.children:
                walk(child)

        walk(root)
        return results

    def extract_all_functions(self, code: str, language: str) -> List[Dict]:
        """
        Extract all functions from code. Alias for parse() method.
        Used by github_repo_processor.py and bulk_processor.py.

        Args:
            code: Source code as string
            language: Programming language name

        Returns:
            List of dictionaries with extracted functions
        """
        return self.parse(code, language)
    
    def extract_classes(self, code: str, language: str) -> List[Dict]:
        """
        Extract class definitions from code.

        Args:
            code: Source code to parse
            language: Programming language

        Returns:
            List of class definitions with methods and context
        """
        lang = self.languages.get(language)
        if not lang:
            logger.warning(f"Language '{language}' not supported for class extraction")
            return []

        try:
            parser = Parser()
            parser.language = lang
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node

            classes = []

            # Node types for classes in different languages
            class_types = {
                "python": "class_definition",
                "java": "class_declaration",
                "javascript": "class_declaration",
                "cpp": "class_specifier",
                "csharp": "class_declaration",
                "ruby": "class",
                "php": "class_declaration"
            }

            class_node_type = class_types.get(language, "class_definition")

            def find_classes(node: Node):
                if node.type == class_node_type:
                    class_info = self._extract_class_info(node, code, language)
                    if class_info:
                        classes.append(class_info)

                for child in node.children:
                    find_classes(child)

            find_classes(root)
            return classes

        except Exception as e:
            logger.error(f"Error extracting classes from {language} code: {e}")
            return []

    def _extract_class_info(self, node: Node, code: str, language: str) -> Optional[Dict]:
        """
        Extract detailed information from a class node.

        Args:
            node: Tree-sitter class node
            code: Original source code
            language: Programming language

        Returns:
            Dictionary with class information
        """
        try:
            # Extract class name
            class_name = None
            for child in node.children:
                if child.type in ["identifier", "name"]:
                    class_name = code[child.start_byte:child.end_byte]
                    break

            if not class_name:
                return None

            # Extract class body
            class_code = code[node.start_byte:node.end_byte]

            # Extract methods within the class
            methods = []
            for child in node.children:
                if child.type in ["function_definition", "method_definition", "method_declaration"]:
                    method_info = self._extract_function_info(child, code, language)
                    if method_info:
                        methods.append(method_info)

            # Extract docstring if Python
            docstring = None
            if language == "python":
                # Look for string literal as first statement in class body
                for child in node.children:
                    if child.type == "block":
                        for stmt in child.children:
                            if stmt.type == "expression_statement":
                                for expr_child in stmt.children:
                                    if expr_child.type == "string":
                                        docstring = code[expr_child.start_byte:expr_child.end_byte].strip('"""\'\'\'')
                                        break
                                break

            # Extract parent class if any
            parent_class = None
            for child in node.children:
                if child.type in ["argument_list", "superclass"]:
                    parent_class = code[child.start_byte:child.end_byte].strip('()')
                    break

            return {
                'task_type': 'class_definition',
                'language': language,
                'class_name': class_name,
                'parent_class': parent_class,
                'input': docstring or f"Write a {language} class named {class_name}",
                'output': class_code,
                'doc': docstring,
                'methods': methods,
                'method_count': len(methods),
                'line_count': class_code.count('\n') + 1
            }

        except Exception as e:
            logger.debug(f"Error extracting class info: {e}")
            return None

    def extract_with_docstring_pairs(self, code: str, language: str = 'python') -> List[Dict]:
        """
        Extract functions with explicit docstring→code pairing for training.
        
        Creates high-quality training examples with:
        - Input: Docstring + function signature
        - Output: Complete implementation
        
        Only functions WITH docstrings are included (higher quality indicator).
        
        Args:
            code: Source code to parse
            language: Programming language (currently optimized for Python)
            
        Returns:
            List of training pairs:
            [{
                'task_type': 'doc_to_code',
                'language': 'python',
                'input': 'Calculate sum of two numbers\n\nSignature: sum(a, b)',
                'output': 'def sum(a, b):\n    Calculate sum\n    return a + b',
                'has_docstring': True,
                'quality_indicator': 'high'
            }]
        
        Example:
            parser = UniversalParser()
            pairs = parser.extract_with_docstring_pairs(python_code)
            # Returns only functions with docstrings for better training data
        """
        pairs = []
        
        if language != 'python':
            logger.warning(f"Docstring pairing optimized for Python, got {language}")
            # Fall back to regular extraction for non-Python
            return self.parse(code, language)
        
        try:
            import ast
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Extract docstring
                    docstring = ast.get_docstring(node)
                    
                    if not docstring:
                        # Skip functions without docstrings (lower quality)
                        continue
                    
                    # Extract function name
                    func_name = node.name
                    
                    # Extract parameters
                    params = []
                    for arg in node.args.args:
                        param_name = arg.arg
                        # Include type hint if present
                        if arg.annotation:
                            try:
                                type_hint = ast.unparse(arg.annotation)
                                params.append(f"{param_name}: {type_hint}")
                            except:
                                params.append(param_name)
                        else:
                            params.append(param_name)
                    
                    params_str = ", ".join(params)
                    
                    # Extract return type if present
                    return_type = ""
                    if node.returns:
                        try:
                            return_type = f" -> {ast.unparse(node.returns)}"
                        except:
                            pass
                    
                    # Build signature
                    signature = f"def {func_name}({params_str}){return_type}:"
                    
                    # Extract complete implementation
                    full_code = ast.unparse(node)
                    
                    # Create training pair
                    # Input: Clear instruction with docstring + signature
                    input_text = f"{docstring}\n\nSignature: {signature}"
                    
                    # Output: Complete implementation
                    output_code = full_code
                    
                    pair = {
                        'task_type': 'doc_to_code',
                        'language': 'python',
                        'func_name': func_name,
                        'input': input_text,
                        'output': output_code,
                        'signature': signature,
                        'doc': docstring,
                        'has_docstring': True,
                        'quality_indicator': 'high',  # Docstrings = better quality
                        'args': params_str,
                        'body': full_code
                    }
                    
                    pairs.append(pair)
                    
        except SyntaxError as e:
            logger.debug(f"Syntax error in code: {e}")
        except Exception as e:
            logger.error(f"Error extracting docstring pairs: {e}")
        
        return pairs

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.languages.keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in self.languages


# Fallback parser using regex (for when tree-sitter is not available)
class FallbackParser(BaseParser):
    """Fallback parser using language-specific regex parsers."""

    def __init__(self):
        """Initialize with available regex parsers."""
        self.parsers = {}
        self._load_parsers()

    def _load_parsers(self):
        """Load regex-based parsers."""
        try:
            from .parsers.py_parser import PythonParser
            self.parsers["python"] = PythonParser()
        except ImportError:
            pass

        try:
            from .parsers.js_parser import JsParser
            self.parsers["javascript"] = JsParser()
        except ImportError:
            pass

        try:
            from .parsers.java_parser import JavaParser
            self.parsers["java"] = JavaParser()
        except ImportError:
            pass

        try:
            from .parsers.cpp_parser import CppParser
            self.parsers["cpp"] = CppParser()
        except ImportError:
            pass

        try:
            from .parsers.go_parser import GoParser
            self.parsers["go"] = GoParser()
        except ImportError:
            pass

        try:
            from .parsers.php_parser import PhpParser
            self.parsers["php"] = PhpParser()
        except ImportError:
            pass

        try:
            from .parsers.rb_parser import RubyParser
            self.parsers["ruby"] = RubyParser()
        except ImportError:
            pass

        logger.info(f"Loaded {len(self.parsers)} fallback parsers")

    def parse(self, code: str, language: str) -> List[Dict]:
        """Parse code using regex-based parser."""
        parser = self.parsers.get(language)
        if not parser:
            logger.warning(f"No fallback parser for {language}")
            return []

        try:
            return parser.parse(code)
        except Exception as e:
            logger.error(f"Fallback parser error for {language}: {e}")
            return []

    def extract_all_functions(self, code: str, language: str) -> List[Dict]:
        """Alias for compatibility."""
        return self.parse(code, language)


def get_parser() -> BaseParser:
    """
    Get the best available parser.

    Returns:
        UniversalParser if tree-sitter is available, otherwise FallbackParser
    """
    try:
        parser = UniversalParser()
        if parser.languages:
            logger.info("Using tree-sitter UniversalParser")
            return parser
    except Exception as e:
        logger.warning(f"Could not initialize UniversalParser: {e}")

    logger.info("Using regex-based FallbackParser")
    return FallbackParser()


# Export for compatibility
__all__ = ["UniversalParser", "FallbackParser", "get_parser"]