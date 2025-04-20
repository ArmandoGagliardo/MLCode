# scripts/run_pipeline.py (aggiornato)
from module.tasks.task_pipeline import TaskPipeline

model_paths = {
    "code_generation": "models/code_generation",
    "text_classification": "models/text_classification",
    "security_classification": "models/security_classification"
}

pipeline = TaskPipeline(model_paths)

while True:
    text = input("✏️ Input: ")
    if text.lower() == "exit": break

    task = pipeline.process("text_classification", text)
    print(f"✅ Tipo identificato: {task}")

    if task == "code":
        print("🧠 Spiegazione codice non implementata")
    else:
        result = pipeline.process("code_generation", text)
        print("📝 Generazione codice:", result)