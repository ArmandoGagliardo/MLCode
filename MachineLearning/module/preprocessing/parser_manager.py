# module/preprocessing/parser_manager.py
from pathlib import Path
import importlib

PARSER_DIR = Path(__file__).parent / "parsers"
LANGUAGE_PARSERS = {}

for parser_path in PARSER_DIR.glob("*_parser.py"):
    if parser_path.name == "base_parser.py":
        continue
    ext = "." + parser_path.stem.split("_")[0]  # ".py", ".js", ".java"
    mod_name = f"module.preprocessing.parsers.{parser_path.stem}"
    mod = importlib.import_module(mod_name)
    class_name = [cls for cls in dir(mod) if cls.endswith("Parser") and cls != "BaseParser"][0]
    LANGUAGE_PARSERS[ext] = getattr(mod, class_name)()

def get_parser(language: str):
    return LANGUAGE_PARSERS.get(language)
