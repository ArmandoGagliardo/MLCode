# module/data/dataset_loader.py
import json
from datasets import Dataset

def load_dataset_json(path, task_type):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return Dataset.from_list(raw)