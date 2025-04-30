from tree_sitter import Language, Parser
from .parsers.base_parser import BaseParser
from .function_parser import FunctionExtractor

class UniversalParser(BaseParser):
    def __init__(self, lib_path='build/my-languages.so'):
        self.languages = {
            "python": Language(lib_path, "python"),
            "cpp": Language(lib_path, "cpp"),
            "java": Language(lib_path, "java"),
            "javascript": Language(lib_path, "javascript"),
            "php": Language(lib_path, "php"),
            "go": Language(lib_path, "go")
        }

    def parse(self, code: str, language: str) -> list[dict]:
        lang = self.languages.get(language)
        if not lang:
            return []

        parser = Parser()
        parser.set_language(lang)
        tree = parser.parse(bytes(code, "utf8"))
        root = tree.root_node

        return self._extract_units(root, code, language)

    def _extract_units(self, root, code: str, language: str):
        results = []

        kind_map = {
            "python": ["function_definition", "class_definition"],
            "cpp": ["function_definition", "class_specifier"],
            "java": ["method_declaration", "constructor_declaration", "class_declaration"],
            "javascript": ["function_declaration", "method_definition", "class_declaration"],
            "php": ["function_definition", "class_declaration"],
            "go": ["function_declaration", "method_declaration"]
        }

        extractor = FunctionExtractor(code)
        target_kinds = kind_map.get(language, ["function_definition"])

        def walk(node):

            if node.type in target_kinds:
                if node.is_missing or node.has_error:
                    return
                info = extractor.extract(node, language)
                if not info:
                    return
                if not info.get("name") or not info.get("body"):
                    return
                if not info["name"].isidentifier() or any(c in info["name"] for c in "():") or len(info["name"]) > 50:
                    return
                print(info["doc"])
                task_type = "class_extraction" if "class" in node.type else "code_generation"
                prompt = info["doc"] if info["doc"] else f"Scrivi una funzione {language} chiamata '{info['name']}' con argomenti: {info.get('args', '')}"
                results.append({
                    "task_type": task_type,
                    "language": language,
                    "func_name": info["name"],
                    "input": prompt,
                    "output": info["signature"] + " " + info["body"]
                })
            for child in node.children:
                walk(child)

        walk(root)
        return results