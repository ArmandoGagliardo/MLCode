import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# 📌 PATH BASE
BASE_PATH = Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_PATH / 'ml_system.log')
    ]
)
logger = logging.getLogger(__name__)

# Controllo dipendenze (solo se non stiamo controllando le dipendenze o mostrando l'help)
if '--check-deps' not in sys.argv and '--help' not in sys.argv and '-h' not in sys.argv:
    try:
        from check_dependencies import check_dependencies
        deps_ok = check_dependencies(verbose=False, auto_install=False)
        if not deps_ok:
            logger.warning("Alcune dipendenze critiche non sono soddisfatte")
            print("\n⚠️  ATTENZIONE: Alcune dipendenze critiche mancano o sono obsolete")
            print("   Esegui: python check_dependencies.py --auto-install")
            print("   Oppure: pip install -r requirements.txt\n")
            # Non bloccare l'esecuzione, ma avvisa l'utente
    except ImportError as e:
        logger.warning(f"Impossibile controllare le dipendenze: {e}")
    except Exception as e:
        logger.warning(f"Errore durante il controllo delle dipendenze: {e}")

# Load configuration
try:
    from config import validate_config, CUDA_VISIBLE_DEVICES, PYTORCH_CUDA_ALLOC_CONF
    validate_config()
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = PYTORCH_CUDA_ALLOC_CONF
    os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_VISIBLE_DEVICES
    logger.info(f"Configuration loaded successfully")
except Exception as e:
    logger.error(f"Configuration error: {e}")
    print(f"Error loading configuration: {e}")
    print("Please ensure config.py exists and .env is properly configured.")
    sys.exit(1)

# 📁 CREAZIONE STRUTTURA
def ensure_directories():
    for folder in ["module", "module/model", "module/tasks", "module/data", "module/preprocessing", "models", "dataset"]:
        path = BASE_PATH / folder
        path.mkdir(parents=True, exist_ok=True)
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)

# 🧠 TRAINING
def train(task):
    logger.info(f"Starting training for task: {task}")
    from module.model.model_manager import ModelManager
    from config import MODEL_PATHS, DEFAULT_BATCH_SIZE, DEFAULT_EPOCHS, DEFAULT_LEARNING_RATE

    if task not in MODEL_PATHS:
        logger.error(f"Unknown task: {task}")
        print(f"Error: Unknown task '{task}'. Available tasks: {list(MODEL_PATHS.keys())}")
        return

    model_name, dataset_path = MODEL_PATHS[task]
    logger.info(f"Using model: {model_name}, dataset: {dataset_path}")

    # Istanzia il model manager generico (gestisce loading e salvataggio modello/tokenizer)
    model_manager = ModelManager(task=task, model_name=model_name)

    # Usa Trainer custom per generazione o sicurezza
    if task in ["code_generation", "security_classification"]:
        logger.info("Using AdvancedTrainer for training...")
        from module.model.training_model_advanced import AdvancedTrainer
        trainer = AdvancedTrainer(model_manager, use_gpu=True)

        trainer.train_model(
            dataset_path=dataset_path,
            model_save_path=f"models/{task}",
            batch_size=DEFAULT_BATCH_SIZE,
            num_epochs=DEFAULT_EPOCHS,
            learning_rate=DEFAULT_LEARNING_RATE,
            remove_labes=["task_type", "language", "func_name", "input", "output"]
        )

    # Altrimenti usa il trainer HuggingFace
    else:
        logger.info("Using AdvancedTrainerClassifier for training...")
        from module.model.advanced_trainer_classifier import AdvancedTrainerClassifier
        trainer = AdvancedTrainerClassifier(model_manager)
        trainer.train_model(
            dataset_path=dataset_path,
            model_save_path=f"models/{task}",
            batch_size=DEFAULT_BATCH_SIZE,
            num_epochs=DEFAULT_EPOCHS,
            learning_rate=DEFAULT_LEARNING_RATE,
        )

    logger.info(f"Training completed for task: {task}")

# 🧪 VALIDAZIONE DATASET
def validate():
    from module.scripts.validate_dataset import main as validate_main
    validate_main()

# 🖥️ STREAMLIT UI
def run_ui():
    try:
        import streamlit
        logger.info("Avvio dell'interfaccia Streamlit...")
        
        app_path = BASE_PATH / "module/ui/app.py"
        if not app_path.exists():
            logger.error(f"File UI non trovato: {app_path}")
            print(f"❌ Errore: File UI non trovato in {app_path}")
            return

        print("\n🚀 Avvio dell'interfaccia web...")
        print("ℹ️ L'interfaccia sarà disponibile su: http://localhost:8501")
        print("ℹ️ Premi Ctrl+C per terminare l'applicazione")
        
        import subprocess
        import signal
        
        def handle_shutdown(signum, frame):
            """Handle shutdown signals gracefully"""
            logger.info("Arresto dell'applicazione...")
            print("\n👋 Arresto dell'applicazione in corso...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            print("✅ Applicazione terminata con successo")
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        try:
            # Use subprocess instead of os.system for better process management
            process = subprocess.Popen(['streamlit', 'run', str(app_path), '--server.port=8501'])
            process.wait()
        except KeyboardInterrupt:
            handle_shutdown(None, None)
        
    except ImportError:
        logger.error("Streamlit non trovato")
        print("\n❌ Streamlit non è installato. Esegui:")
        print("pip install streamlit")
    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        print(f"\n❌ Errore: {str(e)}")

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
    logger.info("Starting GitHub crawl...")
    try:
        from module.preprocessing.github_crawler import crawl
        crawl()
        logger.info("GitHub crawl completed successfully")
    except Exception as e:
        logger.error(f"GitHub crawl failed: {e}", exc_info=True)
        raise

def crawl_local():
    logger.info("Starting local folder crawl...")
    try:
        from module.preprocessing.local_folder_crawler import LocalFolderCrawler
        local_crawler = LocalFolderCrawler(folder_path="models/_classification_/train/", max_files=100)
        local_crawler.crawl()
        logger.info("Local folder crawl completed successfully")
    except Exception as e:
        logger.error(f"Local folder crawl failed: {e}", exc_info=True)
        raise

def crawl_text():
    logger.info("Starting text crawl...")
    try:
        from module.preprocessing.text_crawler import crawl_text_dataset
        crawl_text_dataset()
        logger.info("Text crawl completed successfully")
    except Exception as e:
        logger.error(f"Text crawl failed: {e}", exc_info=True)
        raise

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

    searcher = WebsiteSearcher("https://www.repubblica.it/","repubblica.it")
    crawler = WebTextCrawler(searcher=searcher, max_pages=100)
    crawler.crawl(search_terms)

# 🔐 SECURITY SCANNING
def security_scan(target, scan_type='quick', output_format='text', verbose=False):
    """
    Security vulnerability scanner

    Args:
        target: File or directory to scan
        scan_type: 'quick' (pattern-based) or 'full' (pattern + ML)
        output_format: 'text', 'json', or 'html'
        verbose: Show detailed information
    """
    logger.info(f"Starting security scan on: {target}")
    from module.security.pattern_detector import PatternBasedDetector
    from pathlib import Path

    detector = PatternBasedDetector()
    target_path = Path(target)

    print(f"\n🔍 Security Scan Started")
    print(f"Target: {target}")
    print(f"Scan Type: {scan_type.upper()}")
    print("=" * 80)

    # Scan file or directory
    if target_path.is_file():
        vulnerabilities = detector.scan_file(str(target_path))
        files_scanned = 1
    elif target_path.is_dir():
        print(f"\n📁 Scanning directory recursively...")
        results = detector.scan_directory(str(target_path), recursive=True)
        vulnerabilities = []
        for file_path, vulns in results.items():
            vulnerabilities.extend(vulns)
        files_scanned = len(results)
    else:
        print(f"❌ Error: {target} not found")
        return

    # Output results
    if output_format == 'text':
        print(detector.format_report(vulnerabilities, verbose=verbose))

        # Statistics
        stats = detector.get_statistics()
        print(f"\n📊 Scan Statistics:")
        print(f"   Files Scanned: {files_scanned}")
        print(f"   Vulnerabilities Found: {len(vulnerabilities)}")

        if vulnerabilities:
            print(f"\n⚠️  Action Required: Review and fix {len(vulnerabilities)} vulnerabilities")

            critical_high = sum(1 for v in vulnerabilities if v['severity'] in ['CRITICAL', 'HIGH'])
            if critical_high > 0:
                print(f"   🔴 {critical_high} CRITICAL/HIGH severity issues need immediate attention!")

    elif output_format == 'json':
        import json
        output_file = 'security_report.json'
        with open(output_file, 'w') as f:
            json.dump({
                'target': str(target),
                'files_scanned': files_scanned,
                'vulnerabilities': vulnerabilities,
                'stats': detector.get_statistics()
            }, f, indent=2)
        print(f"\n✅ Report saved to: {output_file}")

    elif output_format == 'html':
        print("\n⚠️  HTML output not yet implemented. Use 'text' or 'json'.")

    logger.info(f"Security scan completed. Found {len(vulnerabilities)} vulnerabilities")

# ☁️ CLOUD STORAGE MANAGEMENT
def storage_connect():
    """Connect to cloud storage provider"""
    logger.info("Connecting to cloud storage...")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        print("\n✅ Storage connected successfully!")

        # Get storage info
        info = storage.get_storage_info()
        print(f"\n📦 Storage Information:")
        print(f"   Provider: {info.get('provider', 'unknown').upper()}")
        print(f"   Bucket: {info.get('bucket_name', 'unknown')}")
        print(f"   Files: {info.get('file_count', 0)}")
        print(f"   Total Size: {info.get('total_size_mb', 0)} MB")
        print(f"   Local Dataset Dir: {info.get('local_dataset_dir', 'unknown')}")
        print(f"   Local Models Dir: {info.get('local_models_dir', 'unknown')}")

        return storage
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")
        return None

def storage_download_datasets(force=False):
    """Download datasets from cloud storage"""
    logger.info("Downloading datasets from cloud storage...")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        print(f"\n⬇️  Downloading datasets...")
        stats = storage.download_datasets(force=force)

        print(f"\n✅ Download completed!")
        print(f"   Downloaded: {stats['downloaded']} files")
        print(f"   Skipped: {stats['skipped']} files")
        print(f"   Failed: {stats['failed']} files")
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")

def storage_upload_datasets(force=False):
    """Upload datasets to cloud storage"""
    logger.info("Uploading datasets to cloud storage...")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        print(f"\n⬆️  Uploading datasets...")
        stats = storage.upload_datasets(force=force)

        print(f"\n✅ Upload completed!")
        print(f"   Uploaded: {stats['uploaded']} files")
        print(f"   Skipped: {stats['skipped']} files")
        print(f"   Failed: {stats['failed']} files")
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")

def storage_backup_model(model_path, model_name=None):
    """Backup a trained model to cloud storage"""
    logger.info(f"Backing up model: {model_path}")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        print(f"\n💾 Backing up model: {model_path}")

        success = storage.backup_model(model_path, model_name=model_name)

        if success:
            print(f"\n✅ Model backup completed!")
        else:
            print(f"\n❌ Model backup failed!")
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")

def storage_restore_model(model_name, destination=None):
    """Restore a model from cloud storage"""
    logger.info(f"Restoring model: {model_name}")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        print(f"\n📥 Restoring model: {model_name}")

        success = storage.restore_model(model_name, destination=destination)

        if success:
            print(f"\n✅ Model restored successfully!")
        else:
            print(f"\n❌ Model restore failed!")
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")

def storage_list_models():
    """List all backed up models"""
    logger.info("Listing backed up models...")
    from module.storage import StorageManager

    storage = StorageManager()

    if storage.connect():
        models = storage.list_models()

        if models:
            print(f"\n📦 Backed up models ({len(models)}):")
            for model in models:
                print(f"   - {model}")
        else:
            print("\n📦 No backed up models found")
    else:
        print("\n❌ Failed to connect to storage")
        logger.error("Storage connection failed")

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

    # Security scanning arguments
    parser.add_argument("--security-scan", type=str, metavar="TARGET",
                       help="Scan file or directory for security vulnerabilities")
    parser.add_argument("--scan-type", choices=["quick", "full"], default="quick",
                       help="Scan type: quick (pattern-based) or full (pattern + ML)")
    parser.add_argument("--output", choices=["text", "json", "html"], default="text",
                       help="Output format for security report")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed vulnerability information")

    # Cloud storage arguments
    parser.add_argument("--storage-connect", action="store_true",
                       help="Connect to cloud storage and show info")
    parser.add_argument("--storage-download", action="store_true",
                       help="Download datasets from cloud storage")
    parser.add_argument("--storage-upload", action="store_true",
                       help="Upload datasets to cloud storage")
    parser.add_argument("--storage-backup", type=str, metavar="MODEL_PATH",
                       help="Backup a model to cloud storage")
    parser.add_argument("--storage-restore", type=str, metavar="MODEL_NAME",
                       help="Restore a model from cloud storage")
    parser.add_argument("--storage-list", action="store_true",
                       help="List all backed up models")
    parser.add_argument("--model-name", type=str,
                       help="Model name for backup/restore operations")
    parser.add_argument("--force", action="store_true",
                       help="Force upload/download all files (skip incremental sync)")

    # Dependency checking arguments
    parser.add_argument("--check-deps", action="store_true",
                       help="Check Python dependencies")
    parser.add_argument("--auto-install", action="store_true",
                       help="Automatically install missing dependencies")

    args = parser.parse_args()

    if args.check_deps:
        from check_dependencies import check_dependencies
        check_dependencies(verbose=args.verbose, auto_install=args.auto_install)
    elif args.train:
        train(args.train)
    elif args.validate:
        validate()
    elif args.ui:
        run_ui()
    elif args.pipeline:
        run_pipeline()
    elif args.security_scan:
        security_scan(args.security_scan, args.scan_type, args.output, args.verbose)
    elif args.storage_connect:
        storage_connect()
    elif args.storage_download:
        storage_download_datasets(force=args.force)
    elif args.storage_upload:
        storage_upload_datasets(force=args.force)
    elif args.storage_backup:
        storage_backup_model(args.storage_backup, model_name=args.model_name)
    elif args.storage_restore:
        storage_restore_model(args.storage_restore, destination=args.model_name)
    elif args.storage_list:
        storage_list_models()
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
