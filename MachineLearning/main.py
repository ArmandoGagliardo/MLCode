"""
ML Code Intelligence System - Main Entry Point

Nuovo sistema basato su:
- GitHub Repository Processing (github_repo_processor.py)
- Bulk Processing (bulk_processor.py)
- Cloud Storage Integration
- Dati locali di grandi dimensioni

Usage:
    python main.py --collect-data --language python --count 20
    python main.py --bulk-process --repos-file repo_list.txt
    python main.py --train code_generation
    python main.py --validate
    python main.py --ui
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime

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
        deps_ok = check_dependencies()
        if not deps_ok:
            logger.warning("Alcune dipendenze critiche non sono soddisfatte")
            print("\n⚠️  ATTENZIONE: Alcune dipendenze critiche mancano o sono obsolete")
            print("   Esegui: python check_dependencies.py --install")
            print("   Oppure: pip install -r requirements.txt\n")
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
    """Crea la struttura di directory necessaria"""
    for folder in [
        "module", "module/model", "module/tasks", "module/data", 
        "module/preprocessing", "module/storage", "module/utils",
        "models", "datasets", "datasets/local_backup", 
        "datasets/local_backup/code_generation",
        "reports", "temp"
    ]:
        path = BASE_PATH / folder
        path.mkdir(parents=True, exist_ok=True)
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)
    logger.info("Directory structure verified")


# ==================== DATA COLLECTION ====================

def collect_data_from_repos(language=None, count=10, repo_url=None, repos_file=None, workers=4):
    """
    Raccoglie dati da repository GitHub
    
    Args:
        language: Linguaggio di programmazione (python, javascript, etc.)
        count: Numero di repository da processare
        repo_url: URL singolo repository
        repos_file: File con lista repository
        workers: Numero di worker paralleli
    """
    logger.info("="*60)
    logger.info("FASE 1: DATA COLLECTION DA GITHUB REPOSITORIES")
    logger.info("="*60)
    
    try:
        from github_repo_processor import GitHubRepoProcessor
        
        processor = GitHubRepoProcessor(
            cloud_save=True,
            max_file_size_mb=10,
            batch_size=100
        )
        
        if repo_url:
            # Singolo repository
            logger.info(f"Processing single repository: {repo_url}")
            stats = processor.process_repository(repo_url)
            print(f"\n[OK] Processed: {stats['functions_extracted']} functions")
            
        elif repos_file:
            # Lista di repository
            logger.info(f"Processing repositories from file: {repos_file}")
            processor.process_repos_from_file(repos_file, max_workers=workers)
            
        elif language:
            # Repository popolari per linguaggio
            logger.info(f"Processing popular {language} repositories")
            repos = processor.get_popular_repos(language, count)
            
            if not repos:
                logger.error(f"No repositories found for language: {language}")
                print(f"❌ No repositories configured for language: {language}")
                return
            
            print(f"\n📦 Processing {len(repos)} {language} repositories...")
            for i, repo_url in enumerate(repos, 1):
                print(f"\n[{i}/{len(repos)}] Processing: {repo_url}")
                try:
                    stats = processor.process_repository(repo_url)
                    print(f"  [OK] Extracted: {stats['functions_extracted']} functions")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    logger.error(f"Failed to process {repo_url}: {e}")
            
            processor.print_statistics()
        else:
            print("❌ Error: Specify --language, --repo, or --repos-file")
            logger.error("No data collection parameters specified")
            
    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        print(f"\n❌ Data collection failed: {e}")
        raise


def bulk_process(repos_file=None, source='github', workers=8):
    """
    Bulk processing di grandi quantità di dati
    
    Args:
        repos_file: File con lista repository
        source: Sorgente dati (github, huggingface, local)
        workers: Numero di worker paralleli
    """
    logger.info("="*60)
    logger.info("FASE 1: BULK PROCESSING")
    logger.info("="*60)
    
    try:
        from bulk_processor import BulkProcessor
        
        processor = BulkProcessor()
        
        if source == 'github':
            if not repos_file:
                repos_file = 'repo_list.txt'
            
            if not Path(repos_file).exists():
                logger.error(f"Repository list file not found: {repos_file}")
                print(f"❌ File not found: {repos_file}")
                print("Create a file with one repository URL per line.")
                return
            
            logger.info(f"Bulk processing from file: {repos_file}")
            processor.process_github_repos(repos_file, max_workers=workers)
            
        elif source == 'huggingface':
            logger.info("Processing HuggingFace datasets")
            processor.process_huggingface_datasets()
            
        elif source == 'local':
            logger.info("Processing local directories")
            processor.process_local_directories()
            
        else:
            logger.error(f"Unknown source: {source}")
            print(f"❌ Unknown source: {source}")
            print("Available sources: github, huggingface, local")
            
    except Exception as e:
        logger.error(f"Bulk processing failed: {e}", exc_info=True)
        print(f"\n❌ Bulk processing failed: {e}")
        raise


# ==================== TRAINING ====================

def train(task, dataset_path=None, model_name=None):
    """
    Training del modello per un task specifico
    
    Args:
        task: Tipo di task (code_generation, text_classification, security_classification)
        dataset_path: Path opzionale al dataset (altrimenti usa quello di default)
        model_name: Nome modello opzionale (altrimenti usa quello di default)
    """
    logger.info("="*60)
    logger.info(f"FASE 2: TRAINING - {task.upper()}")
    logger.info("="*60)
    
    try:
        from module.model.model_manager import ModelManager
        from config import MODEL_PATHS, DEFAULT_BATCH_SIZE, DEFAULT_EPOCHS, DEFAULT_LEARNING_RATE

        if task not in MODEL_PATHS:
            logger.error(f"Unknown task: {task}")
            print(f"❌ Error: Unknown task '{task}'")
            print(f"Available tasks: {list(MODEL_PATHS.keys())}")
            return

        # Usa dataset e modello custom se specificati
        if not dataset_path or not model_name:
            default_model, default_dataset = MODEL_PATHS[task]
            model_name = model_name or default_model
            dataset_path = dataset_path or default_dataset
        
        logger.info(f"Model: {model_name}")
        logger.info(f"Dataset: {dataset_path}")

        # Verify that the dataset exists
        if not Path(dataset_path).exists():
            logger.error(f"Dataset not found: {dataset_path}")
            print(f"\n[FAIL] Dataset not found: {dataset_path}")
            print("Run data collection first:")
            print(f"  python main.py --collect-data --language python")
            return

        # Instantiate model manager
        print("\n[*] Loading model and tokenizer...")
        model_manager = ModelManager(task=task, model_name=model_name)

        # Select appropriate trainer
        if task in ["code_generation"]:
            logger.info("Using AdvancedTrainer for generation task")
            from module.model.training_model_advanced import AdvancedTrainer
            trainer = AdvancedTrainer(model_manager, use_gpu=True)

            trainer.train(
                dataset_path=dataset_path,
                model_save_path=f"models/{task}",
                batch_size=DEFAULT_BATCH_SIZE,
                num_epochs=DEFAULT_EPOCHS,
                learning_rate=DEFAULT_LEARNING_RATE,
                #remove_labels=["task_type", "language", "func_name", "input", "output"]
            )

        else:
            logger.info("Using AdvancedTrainerClassifier for classification task")
            from module.model.advanced_trainer_classifier import AdvancedTrainerClassifier
            trainer = AdvancedTrainerClassifier(model_manager)
            
            trainer.train_model(
                dataset_path=dataset_path,
                model_save_path=f"models/{task}",
                batch_size=DEFAULT_BATCH_SIZE,
                num_epochs=DEFAULT_EPOCHS,
                learning_rate=DEFAULT_LEARNING_RATE,
            )

        logger.info(f"[OK] Training completed for task: {task}")
        print(f"\n[OK] Training completed successfully!")
        print(f"Model saved to: models/{task}")
        
        # Backup su cloud se configurato
        try:
            if os.getenv('AUTO_BACKUP_AFTER_TRAINING', 'false').lower() == 'true':
                print("\n☁️  Uploading model to cloud storage...")
                from module.storage.storage_manager import StorageManager
                storage = StorageManager()
                if storage.connect():
                    storage.backup_model(f"models/{task}", model_name=f"{task}_latest")
                    print("[OK] Cloud backup completed")
        except Exception as e:
            logger.warning(f"Cloud backup failed: {e}")
            print(f"⚠️  Cloud backup failed: {e}")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        print(f"\n❌ Training failed: {e}")
        raise


# ==================== VALIDATION ====================

def validate():
    """Valida i dataset e i modelli"""
    logger.info("="*60)
    logger.info("VALIDATION")
    logger.info("="*60)
    
    try:
        from module.scripts.validate_dataset import main as validate_main
        validate_main()
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        print(f"\n❌ Validation failed: {e}")


# ==================== UI ====================

def run_ui():
    """Avvia l'interfaccia web Streamlit"""
    logger.info("="*60)
    logger.info("STARTING WEB UI")
    logger.info("="*60)
    
    try:
        import streamlit
        
        app_path = BASE_PATH / "module/ui/app.py"
        if not app_path.exists():
            logger.error(f"UI file not found: {app_path}")
            print(f"❌ Error: UI file not found at {app_path}")
            return

        print("\n🚀 Starting web interface...")
        print("ℹ️  Interface will be available at: http://localhost:8501")
        print("ℹ️  Press Ctrl+C to stop the application")
        
        import signal
        
        def handle_shutdown(signum, frame):
            """Handle shutdown signals gracefully"""
            logger.info("Stopping application...")
            print("\n👋 Shutting down application...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            print("[OK] Application stopped successfully")
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        try:
            # Use subprocess for better process management
            process = subprocess.Popen([
                'streamlit', 'run', str(app_path), 
                '--server.port=8501',
                '--server.headless=true'
            ])
            process.wait()
        except KeyboardInterrupt:
            handle_shutdown(None, None)
        
    except ImportError:
        logger.error("Streamlit not installed")
        print("\n❌ Streamlit is not installed. Run:")
        print("   pip install streamlit")
    except Exception as e:
        logger.error(f"UI error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")


# ==================== INTERACTIVE PIPELINE ====================

def run_pipeline():
    """Avvia la pipeline CLI interattiva"""
    logger.info("="*60)
    logger.info("INTERACTIVE PIPELINE")
    logger.info("="*60)
    
    try:
        from module.tasks.task_pipeline import TaskPipeline
        
        model_paths = {
            "code_generation": "models/code_generation",
            "text_classification": "models/text_classification",
            "security_classification": "models/security_classification"
        }

        pipeline = TaskPipeline(model_paths)

        print("\n🚀 Interactive pipeline active (type 'exit' to quit)\n")
        while True:
            text = input("✏️  Enter request or code: ")
            if text.strip().lower() == "exit":
                break

            result = pipeline.process(text)
            print(f"[OK] Result: {result}\n")
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        print(f"\n❌ Pipeline error: {e}")


# ==================== CLOUD STORAGE ====================

def sync_cloud(direction='download'):
    """
    Sincronizza dati con cloud storage
    
    Args:
        direction: 'download' per scaricare, 'upload' per caricare
    """
    logger.info("="*60)
    logger.info(f"CLOUD SYNC - {direction.upper()}")
    logger.info("="*60)
    
    try:
        from module.storage.storage_manager import StorageManager
        
        storage = StorageManager()
        if not storage.connect():
            print("❌ Failed to connect to cloud storage")
            logger.error("Cloud storage connection failed")
            return
        
        print(f"\n☁️  Cloud storage connected: {storage.config.get('provider_type')}")
        
        if direction == 'download':
            print("📥 Downloading datasets...")
            storage.download_datasets()
            print("📥 Downloading models...")
            storage.download_models()
            
        elif direction == 'upload':
            print("📤 Uploading datasets...")
            storage.upload_datasets()
            print("📤 Uploading models...")
            storage.upload_models()
            
        print("[OK] Cloud sync completed")
        
    except Exception as e:
        logger.error(f"Cloud sync failed: {e}", exc_info=True)
        print(f"\n❌ Cloud sync failed: {e}")


# ==================== STATISTICS ====================

def show_stats():
    """Mostra statistiche sui dataset e modelli"""
    logger.info("="*60)
    logger.info("SYSTEM STATISTICS")
    logger.info("="*60)
    
    print("\n📊 System Statistics\n")
    print("="*60)
    
    # Dataset statistics
    print("\n📁 Datasets:")
    datasets_dir = BASE_PATH / "datasets"
    local_backup_dir = datasets_dir / "local_backup" / "code_generation"
    
    if local_backup_dir.exists():
        json_files = list(local_backup_dir.glob("*.json"))
        print(f"  Local backup files: {len(json_files)}")
        
        total_examples = 0
        for file in json_files:
            try:
                import json
                with open(file, 'r') as f:
                    data = json.load(f)
                    total_examples += len(data)
            except:
                pass
        
        print(f"  Total examples: {total_examples:,}")
    else:
        print("  No local datasets found")
    
    # Model statistics
    print("\n🤖 Models:")
    models_dir = BASE_PATH / "models"
    if models_dir.exists():
        for task_dir in models_dir.iterdir():
            if task_dir.is_dir() and not task_dir.name.startswith('_'):
                model_files = list(task_dir.glob("*.bin")) + list(task_dir.glob("*.pt"))
                if model_files:
                    print(f"  {task_dir.name}: {len(model_files)} model files")
    else:
        print("  No models found")
    
    # Duplicate cache
    print("\n🔍 Duplicate Cache:")
    dup_cache = datasets_dir / "duplicates_cache.json"
    if dup_cache.exists():
        try:
            import json
            with open(dup_cache, 'r') as f:
                cache = json.load(f)
                print(f"  Tracked hashes: {len(cache.get('hashes', []))}")
        except:
            print("  Cache file corrupted")
    else:
        print("  No cache file")
    
    print("\n" + "="*60)

# ==================== MAIN ====================

def main():
    """Entry point principale"""
    parser = argparse.ArgumentParser(
        description='ML Code Intelligence System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Data Collection
  python main.py --collect-data --language python --count 20
  python main.py --collect-data --repo https://github.com/user/repo
  python main.py --collect-data --repos-file repo_list.txt --workers 4
  
  # Bulk Processing
  python main.py --bulk-process --repos-file repo_list.txt
  
  # Training
  python main.py --train code_generation
  python main.py --train text_classification
  
  # Cloud Sync
  python main.py --sync-cloud download
  python main.py --sync-cloud upload
  
  # Validation & UI
  python main.py --validate
  python main.py --ui
  python main.py --stats
  
  # Interactive
  python main.py --pipeline
        """
    )
    
    # Main actions
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('--collect-data', action='store_true',
                             help='Collect data from GitHub repositories')
    action_group.add_argument('--bulk-process', action='store_true',
                             help='Bulk process large amounts of data')
    action_group.add_argument('--train', type=str, metavar='TASK',
                             choices=['code_generation', 'text_classification', 'security_classification'],
                             help='Train model for specific task')
    action_group.add_argument('--validate', action='store_true',
                             help='Validate datasets and models')
    action_group.add_argument('--ui', action='store_true',
                             help='Start Streamlit web interface')
    action_group.add_argument('--pipeline', action='store_true',
                             help='Start interactive CLI pipeline')
    action_group.add_argument('--sync-cloud', type=str, metavar='DIRECTION',
                             choices=['download', 'upload'],
                             help='Sync data with cloud storage')
    action_group.add_argument('--stats', action='store_true',
                             help='Show system statistics')
    action_group.add_argument('--check-deps', action='store_true',
                             help='Check dependencies')
    
    # Data collection options
    parser.add_argument('--language', type=str,
                       help='Programming language for data collection')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of repositories to process')
    parser.add_argument('--repo', type=str,
                       help='Single repository URL to process')
    parser.add_argument('--repos-file', type=str,
                       help='File containing repository URLs')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers')
    
    # Training options
    parser.add_argument('--dataset', type=str,
                       help='Custom dataset path for training')
    parser.add_argument('--model', type=str,
                       help='Custom model name for training')
    
    # Bulk processing options
    parser.add_argument('--source', type=str, default='github',
                       choices=['github', 'huggingface', 'local'],
                       help='Data source for bulk processing')
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Execute requested action
    try:
        if args.check_deps:
            from check_dependencies import check_dependencies
            check_dependencies()
            
        elif args.collect_data:
            collect_data_from_repos(
                language=args.language,
                count=args.count,
                repo_url=args.repo,
                repos_file=args.repos_file,
                workers=args.workers
            )
            
        elif args.bulk_process:
            bulk_process(
                repos_file=args.repos_file,
                source=args.source,
                workers=args.workers
            )
            
        elif args.train:
            train(
                task=args.train,
                dataset_path=args.dataset,
                model_name=args.model
            )
            
        elif args.validate:
            validate()
            
        elif args.ui:
            run_ui()
            
        elif args.pipeline:
            run_pipeline()
            
        elif args.sync_cloud:
            sync_cloud(direction=args.sync_cloud)
            
        elif args.stats:
            show_stats()
            
        else:
            parser.print_help()
            print("\n💡 Quick Start:")
            print("  1. python main.py --collect-data --language python --count 10")
            print("  2. python main.py --train code_generation")
            print("  3. python main.py --ui")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user")
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
