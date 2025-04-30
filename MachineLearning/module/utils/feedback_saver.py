# 📂 module/utils/feedback_saver.py
import json
from pathlib import Path

FEEDBACK_PATH = Path("logs/feedback_dataset.json")


def save_feedback(input_text, output_text, feedback_text):
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if FEEDBACK_PATH.exists():
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    else:
        dataset = []
    dataset.append({
        "input": input_text,
        "output": output_text,
        "feedback": feedback_text
    })
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print("💬 Feedback salvato!")