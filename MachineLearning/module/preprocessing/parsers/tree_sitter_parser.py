# module/preprocessing/tree_sitter_parser.py
from tree_sitter import Language, Parser
import os

# Costruzione dinamica della libreria se non esiste
tree_sitter_lang = "tree_sitter_languages.so"
if not os.path.exists(tree_sitter_lang):
    Language.build_library(
        tree_sitter_lang,
        [
            "vendor/tree-sitter-python",
            "vendor/tree-sitter-javascript",
            "vendor/tree-sitter-java",
        ]
    )

PY_LANGUAGE = Language(tree_sitter_lang, "python")

class TreeSitterParser:
    def __init__(self, lang="python"):
        self.parser = Parser()
        self.parser.set_language(PY_LANGUAGE)

    def parse(self, code):
        tree = self.parser.parse(bytes(code, "utf8"))
        root = tree.root_node
        return root.sexp()