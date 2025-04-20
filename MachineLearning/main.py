import os
import sys
import argparse
import subprocess
from pathlib import Path

# 📌 PATH BASE
BASE_PATH = Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH))
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

# 📁 CREAZIONE STRUTTURA
def ensure_directories():
    for folder in ["module", "module/model", "module/tasks", "module/data", "module/preprocessing", "models", "dataset"]:
        path = BASE_PATH / folder
        path.mkdir(parents=True, exist_ok=True)
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)

# 🧠 TRAINING
def train(task):
    from module.model.model_manager import ModelManager

    paths = {
        "code_generation": ("Salesforce/codet5-base", "dataset/dataset_migrated.json"),
        "text_classification": ("microsoft/codebert-base", "dataset/dataset_classification_v2.json"),
        "security_classification": ("microsoft/codebert-base", "dataset/dataset_security.json"),
    }

    model_name, dataset_path = paths[task]

    # Istanzia il model manager generico (gestisce loading e salvataggio modello/tokenizer)
    model_manager = ModelManager(task=task, model_name=model_name)

    # Usa Trainer custom per generazione o sicurezza
    if task in ["code_generation", "security_classification"]:
        print("🚀 Addestramento con TrainingModel (custom)...")
        from module.model.training_model_advanced import AdvancedTrainer
        trainer = AdvancedTrainer(model_manager, use_gpu=False)

        trainer.train_model(
            dataset_path=dataset_path,
            model_save_path=f"models/{task}",
            batch_size=4,
            num_epochs=4,
            learning_rate=5e-5,
            remove_labes=["task_type", "language", "func_name", "input", "output"]
        )
    
    # Altrimenti usa il trainer HuggingFace
    else:
        from module.model.advanced_trainer_classifier import AdvancedTrainerClassifier
        print("🚀 Addestramento con HuggingFace Trainer...")
        trainer = AdvancedTrainerClassifier(model_manager)
        trainer.train_model(
            dataset_path=dataset_path,
            model_save_path=f"models/{task}",
            batch_size=4,
            num_epochs=4,
            learning_rate=5e-5,
        )

# 🧪 VALIDAZIONE DATASET
def validate():
    from module.scripts.validate_dataset import main as validate_main
    validate_main()

# 🖥️ STREAMLIT UI
def run_ui():
    subprocess.run(["streamlit", "run", str(BASE_PATH / "module/ui/app.py"), "--server.runOnSave=False" ])

# 💻 CLI PIPELINE INTERATTIVA
def run_pipeline():
    from module.tasks.task_pipeline import TaskPipeline
    model_paths = {
        "code_generation": "models/code_generation",
        "text_classification": "models/text_classification",
        "security_classification": "models/security_classification"
    }

    pipeline = TaskPipeline(model_paths)

    print("🚀 Pipeline interattiva attiva (scrivi 'exit' per uscire)\n")
    while True:
        text = input("✏️ Inserisci una richiesta o del codice: ")
        if text.strip().lower() == "exit":
            break

        result = pipeline.process(text)  # usa la logica centralizzata e chiara
        print(f"✅ Risultato: {result}\n")

def crawl_github():
    from module.preprocessing.github_crawler import crawl
    crawl()

# 🎯 AVVIO
if __name__ == "__main__":

    ensure_directories()

    parser = argparse.ArgumentParser(description="Avvio generico progetto ML multi-task")
    parser.add_argument("--train", choices=["code_generation", "text_classification", "security_classification"])
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--ui", action="store_true")
    parser.add_argument("--pipeline", action="store_true")
    parser.add_argument("--crawl", action="store_true")
    args = parser.parse_args()

    if args.train:
        train(args.train)
    elif args.validate:
        validate()
    elif args.ui:
        run_ui()
    elif args.pipeline:
        run_pipeline()
    elif args.crawl:
        crawl_github()
    else:
        parser.print_help()
