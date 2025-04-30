import os, re
from pathlib import Path
from .parser_manager import get_parser
from .crawlers.base_crawler import BaseCrawler
import json, hashlib
from .parsers.quality_filter import is_valid_code_sample
class LocalFolderCrawler(BaseCrawler):
    """
    Crawler per estrazione di funzioni da file sorgente in una cartella locale.
    Supporta estensioni multiple, con parsers dinamici basati su file.
    """
    def __init__(self,folder_path:str,max_files:int = 40):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.max_files = max_files
        self.ext_lang = {
                        ".py": "python",
                        ".cpp": "cpp",
                        ".java": "java",
                        ".js": "javascript",
                        ".php": "php",
                        ".go": "go"
                        }
        self.extensions = list(self.ext_lang.keys())
    def is_valid_entry(self,entry: dict) -> bool:
        name = entry.get("func_name", "")
        output = entry.get("output", "")
        prompt = entry.get("input", "")

        if not name or not name.isidentifier():
            return False
        if any(c in name for c in " \n\r\t():") or len(name) > 50:
            return False
        if not output or len(output) < 10:
            return False
        if not prompt or len(prompt.split()) < 3:
            return False
        if re.match(r".*[{};]$", name):  # es. name = "})"
            return False
        if output.count("\n") < 1:
            return False
        return True
    def crawl(self):
        for ext, lang in self.ext_lang.items():
            dataset = []
            file_count = 0
            existing_hashes = set()
            output_file = self.OUTPUT_DIR / f"from_local_{lang}.json"

            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    dataset = json.load(f)
                    for item in dataset:
                        h = hashlib.sha256((item["input"] + item["output"]).encode("utf-8")).hexdigest()
                        existing_hashes.add(h)

            parser = get_parser()
            if not parser:
                print(f"⚠️ Parser non trovato per {lang}")
                continue

            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    if file_count >= self.max_files:
                        break

                    file_path = Path(root) / file
                    if file_path.suffix.lower() != ext:
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code = f.read()
                    except Exception as e:
                        print(f"⚠️ Errore nella lettura del file {file_path}: {e}")
                        continue

                    try:
                        parsed_data = parser.parse(code, lang)
                        for item in parsed_data:
                            if not is_valid_code_sample(item):
                                continue
                            h = hashlib.sha256((item["input"] + item["output"]).encode("utf-8")).hexdigest()
                            if h not in existing_hashes and len(item["input"]) > 10 and len(item["output"]) > 10:
                                dataset.append(item)
                                existing_hashes.add(h)
                                file_count += 1
                            if file_count >= self.max_files:
                                break
                    except Exception as e:
                        print(f"⚠️ Errore nel parsing del file {file_path}: {e}")
                        continue

            # Scrive il dataset completo una sola volta
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(dataset, f, indent=4, ensure_ascii=False)
