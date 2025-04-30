# 📂 module/utils/logger.py
from pathlib import Path
import json

LOG_PATH = Path("logs/session_log.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_interaction(input_text, output_text):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"input": input_text, "output": output_text}) + "\n")