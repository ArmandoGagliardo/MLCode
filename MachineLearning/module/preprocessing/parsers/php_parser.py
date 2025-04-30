import re
from .base_parser import BaseParser

class PhpParser(BaseParser):
    """
    Parser per file PHP. Estrae le funzioni con eventuali docstring PHPDoc
    e crea un oggetto compatibile con il formato del dataset.
    """

    def parse(self, code: str):
        pattern = r"(?:/\*\*(.*?)\*/\s+)?function\s+(\w+)\s*\((.*?)\)\s*\{"  # Commento + funzione
        matches = re.finditer(pattern, code, re.DOTALL)

        results = []
        for match in matches:
            raw_doc, name, args = match.groups()
            start = match.start()
            func_code = self._extract_full_function(code[start:])

            doc_clean = self._clean_docstring(raw_doc)
            prompt = doc_clean.strip()

            if not prompt:
                prompt = doc_clean if doc_clean else f"Scrivi una funzione C++ chiamata '{name}' con argomenti: {args.strip()}"
            results.append({
                "task_type": "code_generation",
                "language": "php",
                "func_name": name,
                "input": prompt.strip(),
                "output": func_code.strip()
            })

        return results

    def _extract_full_function(self, code_segment):
        # Estrae la funzione completa basandosi sulle parentesi
        count = 0
        end = 0
        for i, c in enumerate(code_segment):
            if c == '{':
                count += 1
            elif c == '}':
                count -= 1
            if count == 0 and i > 0:
                end = i
                break
        return code_segment[:end+1].strip()

    def _clean_docstring(self, raw_doc):
        if not raw_doc:
            return ""
        lines = raw_doc.splitlines()
        cleaned = [line.strip().lstrip("* ") for line in lines if line.strip()]
        return " ".join(cleaned)
