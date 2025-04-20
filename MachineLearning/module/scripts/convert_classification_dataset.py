import json
#module/scripts/convert_classification_dataset.py
with open("dataset/dataset_classification.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

converted = []

for item in raw:
    label = item["label"]
    converted.append({
        "task_type": "text_classification",
        "language": "python",  # o generico
        "input": item["text"],
        "output": label  # intero, es: 0 = testo, 1 = codice
    })

with open("dataset/dataset_classification_v2.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, indent=4, ensure_ascii=False)

print("✅ Dataset classification convertito in 'dataset_classification_v2.json'")
