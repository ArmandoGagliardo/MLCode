# module/preprocessing/java_parser.py
import re
from module.preprocessing.base_parser import BaseParser

class JavaParser(BaseParser):
    def parse(self, code):
        pattern = re.compile(r"/\*\*(.*?)\*/\s+public.*? (\w+)\(.*?\)\s*\{", re.DOTALL)
        results = []
        for match in pattern.finditer(code):
            doc, name = match.groups()
            start = match.start()
            func_code = code[start:].split("}", 1)[0] + "}"
            results.append({
                "task_type": "code_generation",
                "language": "java",
                "func_name": name,
                "input": doc.strip().replace("*", "").strip(),
                "output": func_code.strip(),
            })
        return results