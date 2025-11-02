import re
from .base_parser import BaseParser

class RubyParser(BaseParser):
    """
    Parser per file Ruby (.rb).
    Estrae le definizioni di metodi, opzionalmente preceduti da commenti.
    Restituisce dizionari formattati per code generation.
    """

    def parse(self, code: str):
        pattern = r"(?:#(.*?)\n)?def\s+(\w+)\s*(\([^\)]*\))?"
        matches = re.finditer(pattern, code)

        results = []
        for match in matches:
            comment, name, args = match.groups()
            start = match.start()
            func_code = self._extract_full_function(code[start:])

            doc_clean = self._clean_docstring(comment)
            prompt = doc_clean.strip()

            if not prompt:
                prompt = doc_clean if doc_clean else f"Scrivi una funzione C++ chiamata '{name}' con argomenti: {args.strip()}"
            results.append({
                "task_type": "code_generation",
                "language": "ruby",
                "func_name": name,
                "input": prompt.strip(),
                "output": func_code.strip()
            })

        return results

    def _extract_full_function(self, code_segment):
        # Estende fino alla fine del metodo (identifica il primo 'end')
        lines = code_segment.splitlines()
        count = 0
        end_idx = 0
        for i, line in enumerate(lines):
            if re.search(r'\bdef\b', line):
                count += 1
            elif re.search(r'\bend\b', line):
                count -= 1
                if count == 0:
                    end_idx = i
                    break
        return "\n".join(lines[:end_idx+1])

    def _clean_docstring(self, comment):
        if not comment:
            return ""
        return comment.strip().lstrip("#").strip()
