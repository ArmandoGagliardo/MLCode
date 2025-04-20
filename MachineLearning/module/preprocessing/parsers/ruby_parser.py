from .base_parser import BaseParser
import re

class RubyParser(BaseParser):
    def parse(self, source_code: str):
        pattern = re.compile(r'def\s+(\w+)\s*(\([^\)]*\))?', re.MULTILINE)
        matches = pattern.finditer(source_code)
        functions = []
        lines = source_code.splitlines()
        for match in matches:
            name = match.group(1)
            start_line = source_code[:match.start()].count('\n')
            end_line = start_line
            while end_line < len(lines) and not lines[end_line].strip().startswith("end"):
                end_line += 1
            body = "\n".join(lines[start_line:end_line + 1])
            functions.append({
                "task_type": "code_generation",
                "language": "ruby",
                "func_name": name,
                "input": f"Scrivi una funzione Ruby chiamata '{name}'",
                "output": body.strip()
            })
        return functions
