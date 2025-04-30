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
        "text_generation": ("gpt2", "dataset/dataset_text_gen.json")
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
    from MachineLearning.module.preprocessing.github_crawler import crawl
    crawl()

def crawl_local():
    from MachineLearning.module.preprocessing.local_folder_crawler import LocalFolderCrawler
    local_crawler = LocalFolderCrawler(folder_path="models/_classification_/train/", max_files=100)
    local_crawler.crawl()

def crawl_text():
    from MachineLearning.module.preprocessing.text_crawler import crawl_text_dataset
    crawl_text_dataset()

def crawl_web():
        from module.preprocessing.web_text_crawler import WebTextCrawler
        from module.preprocessing.searcher.duck_duck_go_searcher import DuckDuckGoSearcher
        from module.preprocessing.searcher.wikipedia_searcher import WikipediaSearcher
        #searcher = DuckDuckGoSearcher()
        searcher = WikipediaSearcher()
        search_terms = [
        "dialogo televisivo", "dialogo cortese", "dialogo letterario", 
        "discorso persuasivo", "descrizione narrativa", "parlato informale",
        "conversazione quotidiana", "racconto breve", "articolo divulgativo",
        "spiegazione scientifica", "recensione libro", "dialogo teatrale",
        "narrazione in prima persona", "notizia giornalistica","vocabolario","verbi",
        "sostantivi", "aggettivi", "avverbi", "frasi idiomatiche"
        ]
        werb_crawler = WebTextCrawler(searcher=searcher, max_pages=100)
        werb_crawler.crawl(search_terms)

def crawl_website():
    from module.preprocessing.web_text_crawler import WebTextCrawler
    from module.preprocessing.searcher.website_searcher import WebsiteSearcher
    search_terms = [
        # Politica e Leader
        "Meloni", "Salvini", "Conte", "Draghi", "Schlein",
        "Trump", "Biden", "Putin", "Macron", "Zelensky",

        # Conflitti e Geopolitica
        "Ucraina", "Gaza", "Medio Oriente", "Russia", "Israele", "NATO", "Iran", "Taiwan",

        # Economia e Lavoro
        "crisi economica", "tassi BCE", "inflazione", "spread", "debito pubblico",
        "occupazione", "pil", "borsa italiana", "credito", "mutui",

        # Energia e Ambiente
        "caro energia", "gasdotto", "rinnovabili", "nucleare", "transizione ecologica",
        "clima", "emissioni", "siccità", "alluvione", "incendi",

        # Salute e Società
        "vaccino", "covid", "long covid", "psicologia", "sanità", "ospedali", "tumori",

        # Cronaca e Interni
        "mafia", "ndrangheta", "arresti", "omicidio", "truffa", "incidenti", "sparatoria",

        # Tecnologia e Scienza
        "intelligenza artificiale", "ChatGPT", "cyber attacchi", "5G", "spazio", "clonazione",

        # Cultura e Costume
        "festival di Sanremo", "scuola", "università", "istruzione", "giornalismo", "libri", "arte contemporanea"
    ]

    searcher = WebsiteSearcher("https://www.ansa.it/","ansa.it")
    crawler = WebTextCrawler(searcher=searcher, max_pages=100)
    crawler.crawl(search_terms)

# 🎯 AVVIO
if __name__ == "__main__":

    ensure_directories()

    parser = argparse.ArgumentParser(description="Avvio generico progetto ML multi-task")
    parser.add_argument("--train", choices=["code_generation", "text_classification", "security_classification"])
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--ui", action="store_true")
    parser.add_argument("--pipeline", action="store_true")
    parser.add_argument("--crawl_git", action="store_true")
    parser.add_argument("--crawl_local", action="store_true")
    parser.add_argument("--crawl_text", action="store_true")
    parser.add_argument("--crawl_web", action="store_true")
    parser.add_argument("--crawl_wiki", action="store_true")
    parser.add_argument("--crawl_website", action="store_true")
    args = parser.parse_args()

    if args.train:
        train(args.train)
    elif args.validate:
        validate()
    elif args.ui:
        run_ui()
    elif args.pipeline:
        run_pipeline()
    elif args.crawl_git:
        crawl_github()
    elif args.crawl_local:
        crawl_local()
    elif args.crawl_text:
        crawl_text()
    elif args.crawl_web:
        crawl_web()
    elif args.crawl_wiki:
        from module.preprocessing.wiki_text_crawler import WikiTextCrawler
        crawler = WikiTextCrawler()
        crawler.crawl()
    elif args.crawl_website:
        crawl_website()
    else:
        parser.print_help()
