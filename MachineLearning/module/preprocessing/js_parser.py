# module/preprocessing/js_parser.py
import re
from module.preprocessing.base_parser import BaseParser

class JSParser(BaseParser):
    def parse(self, code):
        pattern = re.compile(r"/\*\*(.*?)\*/\s*function\s+(\w+)\(.*?\)\s*\{", re.DOTALL)
        results = []
        for match in pattern.finditer(code):
            doc, name = match.groups()
            start = match.start()
            func_code = code[start:].split("}", 1)[0] + "}"
            results.append({
                "task_type": "code_generation",
                "language": "javascript",
                "func_name": name,
                "input": doc.strip().replace("*", "").strip(),
                "output": func_code.strip(),
            })
        return results