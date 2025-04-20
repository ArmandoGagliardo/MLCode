from .base_parser import BaseParser
import re

class CppParser(BaseParser):
    def parse(self, source_code: str):
        pattern = re.compile(r'(?:[\w:<>\s]+)\s+(\w+)\s*\(([^)]*)\)\s*{', re.MULTILINE)
        matches = pattern.finditer(source_code)
        functions = []
        for match in matches:
            name = match.group(1)
            args = match.group(2)
            start = match.start()
            brace_count = 1
            end = start + len(match.group(0))
            while end < len(source_code) and brace_count > 0:
                if source_code[end] == '{':
                    brace_count += 1
                elif source_code[end] == '}':
                    brace_count -= 1
                end += 1
            body = source_code[start:end]
            functions.append({
                "task_type": "code_generation",
                "language": "cpp",
                "func_name": name,
                "input": f"Scrivi una funzione C++ chiamata '{name}' con argomenti: {args}",
                "output": body.strip()
            })
        return functions
