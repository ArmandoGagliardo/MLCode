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
        elif language in {"cpp", "go", "php", "javascript"}:
            return self._extract_c_family(node)
        else:
            return {}

    def _text(self, node):
        return self.code[node.start_byte:node.end_byte].strip()

    def _extract_docstring(self, node):
        start_line = node.start_point[0]
        doc_lines = []
        i = start_line - 1
        
        while i >= 0:
            if i == 0 or i < ( start_line - 10):
                break
            raw_line = self.code_lines[i]
            line = self._clean_text(raw_line)
            #print(f"📄 Analizzo linea {i}: {repr(line)}")
            # Se non è un commento → continua a risalire

            if not line or len(line) < 2  or (line[0]+line[1]) not in{ "//", "#","/*"}:
                i -= 1
                if i <=0:
                    break
                continue

            if line.startswith("//") or line.startswith("#") or line.startswith("/*") or line.startswith("*"):
                #print(f"📄 Trovato commento: {repr(raw_line)}")
                
                while i < start_line:
                    
                    if(i == start_line):
                        break

                    raw_line = self.code_lines[i]
                    line = raw_line.strip()
                    cleaned = self._clean_text(raw_line)
                    if cleaned:
                        doc_lines.append(cleaned)

                    # Verifica se la prossima riga è ancora un commento
                    if i + 1 < start_line:
                        next_line = self.code_lines[i + 1].strip()
                        if not (next_line.startswith("//") or next_line.startswith("#") or next_line.startswith("/*") or next_line.startswith("*")):
                            break
                    i += 1

            # Se arrivi qui: riga non commento → esci
            break

        # Pulisci il testo finale
        doc = " ".join(doc_lines)

        if doc:
            print(f"🧠 Docstring trovata → {doc}")

        # Scarta descrizioni banali
        if not doc or len(doc) < 10 or doc.lower() in {
            "main", "debug", "wfs", "ここから", "list", "math class", "output sample"
        }:
            return ""
        return doc
    
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
        info["doc"] = self._extract_docstring(node)
        return info

    def _extract_python(self, node: Node):
        info = {"kind": node.type}

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
                    return None  # Scarta o marca come da rivedere
                info["args"] = self._text(child)
            elif child.type == "block":
                info["body"] = self._text(child)
        info["signature"] = self._build_signature(info)
        info["doc"] = self._extract_docstring(node)
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
            elif n.type == "compound_statement" and not body:
                body = self._text(n)
            for c in n.children:
                find(c)

        find(node)
        info["name"] = name or "funzione"
        info["args"] = args or "()"
        info["body"] = body or ""
        info["return_type"] = return_type or ""
        info["signature"] = self._build_signature(info)
        info["doc"] = self._extract_docstring(node)
        return info

    def _build_signature(self, info):
        parts = []
        if "modifiers" in info:
            parts.extend(info["modifiers"])
        if info.get("return_type"):
            parts.append(info["return_type"])
        if info.get("name"):
            parts.append(info["name"] + (info.get("args") or "()"))
        return " ".join(parts)