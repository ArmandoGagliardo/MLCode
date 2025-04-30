# module/preprocessing/shell_parser.py
from .base_parser import BaseParser

class ShellParser(BaseParser):
    def parse(self, script):
        lines = script.strip().splitlines()
        doc = lines[0][1:].strip() if lines and lines[0].startswith("#") else ""
        return [{
            "task_type": "security_classification",
            "language": "shell",
            "input": doc,
            "output": "\n".join(lines[1:]).strip()
        }] if doc else []