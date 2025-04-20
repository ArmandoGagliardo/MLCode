# module/preprocessing/python_parser.py
import ast
from module.preprocessing.base_parser import BaseParser

class PythonParser(BaseParser):
    def parse(self, code):
        results = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    doc = ast.get_docstring(node) or ""
                    start = node.lineno - 1
                    end = getattr(node.body[-1], 'end_lineno', node.body[-1].lineno)
                    lines = code.splitlines()[start:end]
                    results.append({
                        "task_type": "code_generation",
                        "language": "python",
                        "func_name": node.name,
                        "input": doc.strip(),
                        "output": "\n".join(lines).strip(),
                    })
        except Exception:
            pass
        return results