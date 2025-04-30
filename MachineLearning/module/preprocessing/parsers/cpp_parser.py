import re
from .base_parser import BaseParser

class CppParser(BaseParser):
    def parse(self, code: str):
        pattern = r"""
(?:/\*\*([\s\S]*?)\*/\s*)?            # Docstring multilinea
(?:[\w:<>\*&]+\s+)+                  # Tipo di ritorno
(?P<name>\w+)\s*                     # Nome funzione
\((?P<args>[^)]*)\)\s*              # Parametri
(?:const)?\s*(?=\{)                 # const opzionale + lookahead su {
"""
        matches = re.finditer(pattern, code, re.VERBOSE | re.DOTALL)

        results = []

        for match in matches:
            print(match.group())
            raw_doc = match.group(1)
            name = match.group("name")
            args = match.group("args")

            search_window = code[match.end():match.end()+1000]
            open_index = search_window.find("{")
            if name in {"define", "ifdef", "endif", "template", "class", "struct","for", "while", "if", "switch", "else", "return"} or  len(name) < 3:
                continue
            if open_index == -1:
                continue
            func_start = match.end() + open_index
            func_code = self._extract_full_function(code[func_start:])
            # prompt robusto
            prompt = self._clean_docstring(raw_doc).strip()

            if not prompt:
                prompt = f"Scrivi una funzione C++ chiamata '{name}' con argomenti: {args.strip()}"
            if not func_code.strip():
                continue
            print(f"\nPrompt: {prompt}\nFunzione:\n{name + func_code}\n{'='*40}")

            if not func_code.strip():
                continue
            results.append({
                "task_type": "code_generation",
                "language": "cpp",
                "func_name": name,
                "input": prompt,
                "output": name + func_code.strip()
            })

        return results

    def _extract_full_function(self, code_segment):
        count = 0
        for i, c in enumerate(code_segment):
            if c == '{':
                count += 1
            elif c == '}':
                count -= 1
                if count == 0:
                    return code_segment[:i+1]
        return ""

    def _clean_docstring(self, raw_doc):
        if not raw_doc:
            return ""
        lines = raw_doc.splitlines()
        cleaned = [line.strip().lstrip("* ") for line in lines if line.strip()]
        return " ".join(cleaned).strip()
