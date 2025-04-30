# 📂 module/preprocessing/text_crawler.py
import os, json, hashlib
from pathlib import Path
from .cleaning.text_quality import is_valid_text

EXTENSIONS = {".txt", ".md", ".rst", ".html"}
OUTPUT_FILE = Path("dataset/dataset_text_gen.json")
CHUNK_SIZE = 500  # numero di caratteri per porzione


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def crawl_text_dataset(folder="data/texts"):
    folder = Path(folder)
    dataset = []
    seen_hashes = set()
    for root, _, files in os.walk(folder):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext not in EXTENSIONS:
                continue
            path = Path(root) / file
            with open(path, encoding="utf-8", errors="ignore") as f:
                full_text = f.read().strip()

            if len(full_text) < 50:
                continue

            base_id = hash_text(str(path))[:8]

            # Dividi in buffer
            for i in range(0, len(full_text), CHUNK_SIZE):
                chunk = full_text[i:i + CHUNK_SIZE].strip()
                if not is_valid_text(chunk):
                    continue
                chunk_hash = hash_text(chunk)
                if chunk_hash in seen_hashes:
                    continue
                seen_hashes.add(chunk_hash)

                dataset.append({
                    "task_type": "text_generation",
                    "language": "natural",
                    "group_id": base_id,
                    "input": chunk[:150],
                    "output": chunk
                })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"✅ Salvato dataset con {len(dataset)} porzioni in {OUTPUT_FILE}")
