# 📂 module/preprocessing/wiki_text_crawler.py

import os
import json
from pathlib import Path
from transformers import AutoTokenizer
from module.preprocessing.cleaning.text_cleaner import TextCleaner
import hashlib

class WikiTextCrawler:
    def __init__(self):
        self.INPUT_DIR = Path("C:/Users/arman/OneDrive/Desktop/PythonRepo/MachineLearning/OUTPUT_FOLDER")
        self.DATA_DIR = Path("data/dataset_italiano")
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.CLEANED_DIR = self.DATA_DIR / "cleaned"
        self.METADATA_PATH = self.DATA_DIR / "metadata.jsonl"
        self.text_cleaner = TextCleaner(clean_wiki_markup=True)
        self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-italian-cased")

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    def crawl(self):
        print(f"🚀 Inizio elaborazione file Wikipedia in {self.INPUT_DIR}")

        files = list(self.INPUT_DIR.rglob("wiki_*"))
        if not files:
            print("⚠️ Nessun file trovato.")
            return

        for file_path in files:
            print(f"📄 Processo: {file_path.name}")
            try:
                raw_path = self._save_raw(file_path)
                cleaned_paths = self.text_cleaner.process_file(raw_path)
                self._append_metadata(cleaned_paths)
            except Exception as e:
                print(f"❌ Errore su {file_path.name}: {e}")

    def _save_raw(self, src_path: Path):

        filename_base = self._hash_string(src_path.name)
        dest_path = self.RAW_DIR /  (filename_base + f".txt")
        content = src_path.read_text(encoding='utf-8')
        dest_path.write_text(content, encoding='utf-8')
        return dest_path

    def _append_metadata(self, cleaned_paths: list[Path]):
        with open(self.METADATA_PATH, 'a', encoding='utf-8') as meta_file:
            for path in cleaned_paths:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Recupera titolo associato
                original_file_stem = "_".join(path.stem.split("_")[:-1])  # es. "6a69bb..._part0" → "6a69bb..."
                raw_filename = original_file_stem + ".txt"
                raw_path = self.RAW_DIR / raw_filename
                title = self._extract_title_from_raw(raw_path)  

                tokens = self.tokenizer.tokenize(content)

                metadata = {
                #"path": str(path.resolve()),
                "title": title,
                "text": content.strip(),
                "n_tokens": len(tokens)
                }
                json.dump(metadata, meta_file, ensure_ascii=False)
                meta_file.write('\n')

    def _hash_string(self, s: str):
        return hashlib.sha256(s.encode('utf-8')).hexdigest()
    
    def _extract_title_from_raw(self, raw_path: Path) -> str:
        try:
            with open(raw_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("<") and not line.startswith("https://"):
                        return line
        except Exception as e:
            print(f"⚠️ Errore lettura titolo da {raw_path.name}: {e}")
        return "UNKNOWN"
