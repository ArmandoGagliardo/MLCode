# module/scripts/validate_dataset.py
import json
from collections import Counter

def main():
    try:
        with open("dataset/dataset_migrated.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ File non trovato. Controlla il percorso.")
        return

    print(f"✅ Totale esempi: {len(data)}")
    tasks = Counter(item["task_type"] for item in data)
    languages = Counter(item["language"] for item in data)
    print("\n📊 Tasks:", tasks)
    print("\n📊 Linguaggi:", languages)

    for i, item in enumerate(data[:5]):
        print(f"\n🔹 Esempio {i+1}\nTask: {item['task_type']}\nInput: {item['input']}\nOutput: {item['output'][:80]}...")

# 👇 Importabile o eseguibile direttamente
if __name__ == "__main__":
    main()
