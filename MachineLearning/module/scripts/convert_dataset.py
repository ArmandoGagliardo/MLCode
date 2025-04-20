# module/scripts/convert_dataset.py
import json, os
from pathlib import Path

input_path = Path("dataset/dataset.txt")
output_path = Path("dataset/dataset_migrated.json")

with open(input_path, "r", encoding="utf-8") as f:
    raw = json.load(f)

new_data = []
for item in raw.values():
    new_data.append({
        "task_type": "code_generation",
        "language": item.get("language", "python"),
        "func_name": item.get("func_name", "unknown"),
        "input": item["docstring"],
        "output": item["code"]
    })

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(new_data, f, indent=4, ensure_ascii=False)

print(f"✅ Dataset convertito in {output_path}")
