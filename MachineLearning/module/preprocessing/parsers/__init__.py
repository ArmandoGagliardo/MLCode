from .python_parser import PythonParser
from .js_parser import JSParser
from .shell_parser import ShellParser
from .java_parser import JavaParser

EXT_PARSER_MAP = {
    ".py": PythonParser(),
    ".js": JSParser(),
    ".sh": ShellParser(),
    ".java": JavaParser()
}
