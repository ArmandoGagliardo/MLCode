from tree_sitter import Node
import re

class FunctionExtractor:
    def __init__(self, code: str):
        self.code = code
        self.code_lines = code.splitlines()

    def extract(self, node: Node, language: str):
        if language == "java":
            return self._extract_java(node)
        elif language == "python":
            return self._extract_python(node)
        elif language == "rust":
            return self._extract_rust(node)
        elif language == "ruby":
            return self._extract_ruby(node)
        elif language in {"cpp", "go", "php", "javascript"}:
            return self._extract_c_family(node)
        else:
            return {}

    def _text(self, node):
        return self.code[node.start_byte:node.end_byte].strip()

    def _extract_docstring(self, node, language=""):
        """
        Extract docstring/comments from a function/class node.
        Supports:
        - External comments (above the function): //, #, /* */
        - Internal docstrings (inside the function): Python, Java/JS /* */
        """
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        doc_lines = []
        
        # 1. Try to extract INTERNAL docstring (for Python, JavaScript, Java)
        internal_doc = self._extract_internal_docstring(node, language)
        if internal_doc:
            return internal_doc
        
        # 2. Try to extract EXTERNAL comments (above the function)
        # Look up to 20 lines above the function
        i = start_line - 1
        comment_start = None
        
        while i >= 0 and i >= (start_line - 20):
            raw_line = self.code_lines[i]
            stripped = raw_line.strip()
            
            # Check if this is a comment line
            is_comment = False
            if stripped.startswith("//") or stripped.startswith("#"):
                is_comment = True
            elif stripped.startswith("/*") or stripped.startswith("*"):
                is_comment = True
            elif stripped.startswith("/**"):  # JavaDoc/JSDoc
                is_comment = True
            
            if is_comment:
                comment_start = i
                i -= 1
                continue
            elif stripped == "":
                # Empty line - continue looking up
                i -= 1
                continue
            else:
                # Non-comment, non-empty line - stop here
                break
        
        # Collect comment lines from comment_start to function start
        if comment_start is not None:
            for line_idx in range(comment_start, start_line):
                raw_line = self.code_lines[line_idx]
                cleaned = self._clean_comment_line(raw_line)
                if cleaned:
                    doc_lines.append(cleaned)
        
        # Join and clean
        doc = " ".join(doc_lines).strip()
        
        # Filter out trivial descriptions
        if not doc or len(doc) < 5:
            return ""
        
        doc_lower = doc.lower()
        trivial_patterns = ["main", "debug", "wfs", "ここから", "list", "math class", "output sample"]
        if any(pattern in doc_lower for pattern in trivial_patterns):
            return ""
        
        return doc
    
    def _extract_internal_docstring(self, node, language):
        """
        Extract docstring from INSIDE a function/class body.
        Works for Python triple-quoted strings and Java/JS block comments.
        """
        # Find the body/block node
        body_node = None
        for child in node.named_children:
            if child.type in ["block", "statement_block", "compound_statement"]:
                body_node = child
                break
        
        if not body_node:
            return ""
        
        # Get first few lines of the body
        body_start_line = body_node.start_point[0]
        body_end_line = min(body_start_line + 10, body_node.end_point[0])
        
        doc_lines = []
        in_docstring = False
        docstring_delimiter = None
        triple_double = '"""'  # noqa
        triple_single = "'''"  # noqa
        
        for line_idx in range(body_start_line, body_end_line + 1):
            if line_idx >= len(self.code_lines):
                break
            
            line = self.code_lines[line_idx].strip()
            
            # Python triple-quoted strings
            has_triple = ('"""' in line) or ("'''" in line)
            if has_triple:
                if not in_docstring:
                    # Start of docstring
                    in_docstring = True
                    if '"""' in line:
                        docstring_delimiter = '"""'
                    else:
                        docstring_delimiter = "'''"
                    
                    # Extract content from this line
                    if line.count(docstring_delimiter) >= 2:
                        # Single-line docstring: """text"""
                        content = line.replace(docstring_delimiter, "").strip()
                        if content:
                            return content
                    else:
                        # Multi-line docstring starts
                        content = line.replace(docstring_delimiter, "").strip()
                        if content:
                            doc_lines.append(content)
                else:
                    # End of docstring
                    content = line.replace(docstring_delimiter, "").strip()
                    if content:
                        doc_lines.append(content)
                    break
            elif in_docstring:
                # Inside multi-line docstring
                if line:
                    doc_lines.append(line)
            
            # JavaScript/Java block comments inside function
            elif line.startswith("/*") or line.startswith("/**"):
                # Start of block comment
                if "*/" in line:
                    # Single-line block comment
                    content = line.replace("/*", "").replace("/**", "").replace("*/", "").strip()
                    if content:
                        return content
                else:
                    in_docstring = True
                    content = line.replace("/*", "").replace("/**", "").strip()
                    if content:
                        doc_lines.append(content)
            elif "*/" in line and in_docstring:
                # End of block comment
                content = line.replace("*/", "").strip()
                if content and not content.startswith("*"):
                    doc_lines.append(content)
                break
            elif in_docstring and line.startswith("*"):
                # Inside block comment
                content = line.lstrip("*").strip()
                if content:
                    doc_lines.append(content)
        
        if doc_lines:
            return " ".join(doc_lines).strip()
        
        return ""
    
    def _clean_comment_line(self, line: str) -> str:
        """Clean a comment line by removing comment markers and extra whitespace."""
        stripped = line.strip()
        
        # Remove common comment markers
        if stripped.startswith("//"):
            stripped = stripped[2:].strip()
        elif stripped.startswith("#"):
            stripped = stripped[1:].strip()
        elif stripped.startswith("/**"):
            stripped = stripped[3:].strip()
        elif stripped.startswith("/*"):
            stripped = stripped[2:].strip()
        elif stripped.startswith("*"):
            stripped = stripped[1:].strip()
        
        # Remove trailing comment markers
        if stripped.endswith("*/"):
            stripped = stripped[:-2].strip()
        
        # Remove extra whitespace
        stripped = re.sub(r'\s+', ' ', stripped)
        
        return stripped.strip()
    
    def _clean_text(self, text: str) -> str:
        # Rimuove doppi spazi, strip iniziale/finale, spazi e a capo eccessivi
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_java(self, node: Node):
        info = {"kind": node.type}
        for child in node.named_children:
            t = child.type
            if t == "modifiers":
                info["modifiers"] = [self._text(c) for c in child.named_children]
            elif t == "type":
                info["return_type"] = self._text(child)
            elif t == "identifier":
                info["name"] = self._text(child)
            elif t == "formal_parameters":
                info["args"] = self._text(child)
            elif t == "block":
                info["body"] = self._text(child)
        info["signature"] = self._build_signature(info)
        info["doc"] = self._extract_docstring(node, "java")
        return info

    def _extract_python(self, node: Node):
        info = {"kind": node.type, "language": "python"}

        for child in node.named_children:
            if not node.is_named or node.is_missing:
                continue
            if child.type == "identifier":
                info["name"] = self._text(child)
                if "name" not in info:
                    header_line = self.code_lines[node.start_point[0]]
                    m = re.search(r"def\s+([a-zA-Z_][\w]*)", header_line)
                    if m:
                        info["name"] = m.group(1)
            elif child.type == "parameters":
                if not info.get("name") or not info["name"].isidentifier():
                    return None  # Scarta o marca da rivedere
                info["args"] = self._text(child)
            elif child.type == "block":
                info["body"] = self._text(child)
        info["signature"] = self._build_signature(info)
        info["doc"] = self._extract_docstring(node, "python")
        return info

    def _extract_c_family(self, node: Node):
        info = {"kind": node.type}
        name = None
        args = None
        body = None
        return_type = None

        def find(n):
            nonlocal name, args, body, return_type
            if n.type in {"identifier", "name"} and not name:
                name = self._text(n)
            elif n.type in {"parameter_list", "parameters", "formal_parameters"} and not args:
                args = self._text(n)
            elif n.type == "type" and not return_type:
                return_type = self._text(n)
            elif n.type in {"compound_statement", "block", "statement_block"} and not body:  # Added 'block' for Go, 'statement_block' for JS
                body = self._text(n)
            for c in n.children:
                find(c)

        find(node)
        info["name"] = name or "funzione"
        info["args"] = args or "()"
        info["body"] = body or ""
        info["return_type"] = return_type or ""
        info["signature"] = self._build_signature(info)
        info["doc"] = self._extract_docstring(node, "c_family")
        return info

    def _extract_rust(self, node: Node):
        """Extract Rust function information from function_item node"""
        info = {"kind": node.type, "language": "rust"}
        name = None
        args = None
        body = None
        return_type = None
        visibility = None

        def find(n):
            nonlocal name, args, body, return_type, visibility
            if n.type == "identifier" and not name:
                name = self._text(n)
            elif n.type == "parameters" and not args:
                args = self._text(n)
            elif n.type == "block" and not body:
                body = self._text(n)
            elif n.type == "visibility_modifier" and not visibility:
                visibility = self._text(n)
            # Return type comes after -> in Rust
            elif n.type in {"primitive_type", "type_identifier", "generic_type", "reference_type"} and not return_type:
                # Check if previous sibling is ->
                parent = n.parent
                if parent:
                    idx = parent.children.index(n)
                    if idx > 0 and parent.children[idx-1].type == "->":
                        return_type = self._text(n)
            
            for c in n.children:
                find(c)

        find(node)
        info["name"] = name or "function"
        info["args"] = args or "()"
        info["body"] = body or ""
        info["return_type"] = return_type or ""
        info["visibility"] = visibility or ""
        info["signature"] = self._build_rust_signature(info)
        info["doc"] = self._extract_docstring(node, "rust")
        return info

    def _build_rust_signature(self, info):
        """Build Rust function signature"""
        parts = []
        
        # Add visibility (pub, pub(crate), etc)
        if info.get("visibility"):
            parts.append(info["visibility"])
        
        # Add fn keyword
        parts.append("fn")
        
        # Add name with parameters
        if info.get("name"):
            name_with_args = info["name"] + (info.get("args") or "()")
            parts.append(name_with_args)
        
        # Add return type if present
        if info.get("return_type"):
            parts.append("->")
            parts.append(info["return_type"])
        
        return " ".join(parts)

    def _extract_ruby(self, node: Node):
        """Extract Ruby method/class information"""
        info = {"kind": node.type, "language": "ruby"}
        name = None
        args = None
        body = None

        # Extract information only from direct children (not recursively)
        # to avoid picking up nested methods/classes
        for child in node.children:
            if child.type == "identifier" and not name:
                name = self._text(child)
            elif child.type == "method_parameters" and not args:
                args = self._text(child)
            elif child.type == "body_statement" and not body:
                body = self._text(child)
            elif child.type == "block_body" and not body:  # For blocks
                body = self._text(child)

        info["name"] = name or "method"
        info["args"] = args or ""
        info["body"] = body or ""
        info["return_type"] = ""
        info["signature"] = self._build_ruby_signature(info)
        info["doc"] = self._extract_docstring(node, "ruby")
        return info

    def _build_ruby_signature(self, info):
        """Build signature for Ruby methods"""
        parts = ["def", info.get("name", "method")]
        
        # Add arguments (Ruby uses parentheses or no parentheses)
        args = info.get("args", "")
        if args:
            # If args don't have parentheses, add them
            if not args.startswith("("):
                parts.append(f"({args})")
            else:
                parts.append(args)
        
        return " ".join(parts)

    def _build_signature(self, info):
        parts = []
        
        # Add language-specific keyword (e.g., 'def' for Python)
        if info.get("language") == "python" and info.get("kind") == "function_definition":
            parts.append("def")
        
        if "modifiers" in info:
            parts.extend(info["modifiers"])
        if info.get("return_type"):
            parts.append(info["return_type"])
        if info.get("name"):
            name_with_args = info["name"] + (info.get("args") or "()")
            parts.append(name_with_args)
        
        signature = " ".join(parts)
        
        # Add colon for Python (without space before it)
        if info.get("language") == "python":
            signature += ":"
        
        return signature