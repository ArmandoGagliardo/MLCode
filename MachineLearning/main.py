"""
ML Code Intelligence System - Main Entry Point
===============================================

**DEPRECATION NOTICE**
----------------------
This file is DEPRECATED and will be removed in v3.0.0

Please use the new CLI interface instead:
    python -m presentation.cli --help

Migration examples:
    OLD: python main.py --collect-data --language python --count 20
    NEW: python -m presentation.cli collect --language python --count 20

    OLD: python main.py --train code_generation
    NEW: python -m presentation.cli train --dataset data/dataset.json

    OLD: python main.py --validate
    NEW: python -m presentation.cli info --validate

See MIGRATION_GUIDE.md for complete migration guide.

**END DEPRECATION NOTICE**
--------------------------

Questo è il file principale del sistema di Machine Learning per l'analisi e
generazione di codice. Il sistema è composto da 3 fasi principali:

1. DATA COLLECTION (--collect-data)
   Scarica codice da repository GitHub, lo analizza ed estrae funzioni

2. TRAINING (--train)
   Addestra modelli AI (GPT-like) per generare o classificare codice

3. VALIDATION (--validate)
   Verifica la qualità dei modelli addestrati

ARCHITETTURA:
------------
main.py (questo file)              → Punto di ingresso, gestisce comandi CLI
├── github_repo_processor.py       → Scarica e processa repository GitHub
├── bulk_processor.py              → Elabora grandi quantità di dati
├── module/model/training_*.py     → Addestra modelli AI
├── module/storage/storage_manager.py → Gestisce upload/download cloud
└── config.py                      → Configurazioni (GPU, storage, API keys)

ESEMPI D'USO:
------------
# 1. Raccogliere dati da repository Python popolari
python main.py --collect-data --language python --count 20

# 2. Elaborazione massiva da lista di repository
python main.py --bulk-process --repos-file repo_list.txt

# 3. Addestrare modello per generazione di codice
python main.py --train code_generation

# 4. Validare il sistema completo
python main.py --validate

# 5. Avviare interfaccia web
python main.py --ui

REQUISITI:
---------
- Python 3.8+
- PyTorch con CUDA (per GPU)
- HuggingFace Transformers
- Tree-sitter (per parsing codice)
- Credenziali cloud storage (DigitalOcean Spaces, AWS S3, etc.)

CONFIGURAZIONE:
--------------
1. Copia config/.env.common.example a config/.env.common
2. Aggiungi le tue API keys (GitHub, Cloud Storage)
3. Configura GPU se disponibile (CUDA_VISIBLE_DEVICES)

AUTORI:
-------
Machine Learning Code Intelligence Project
Data: Novembre 2025
"""

# ============================================================================
# IMPORT LIBRERIE STANDARD
# ============================================================================
import os          # Interazione con sistema operativo (file, env variables)
import sys         # Accesso a variabili e funzioni del sistema Python
import argparse    # Parsing argomenti da linea di comando
import subprocess  # Esecuzione comandi esterni (es. git clone)
import logging     # Sistema di logging per debug e monitoraggio
from pathlib import Path      # Gestione percorsi file cross-platform
from datetime import datetime # Gestione date e timestamp

# ============================================================================
# CONFIGURAZIONE PATH BASE
# ============================================================================
# __file__ contiene il path del file corrente (main.py)
# .resolve() risolve symlink e path relativi in path assoluto
# .parent ottiene la directory contenitore
BASE_PATH = Path(__file__).resolve().parent

# Aggiunge la directory base al PYTHONPATH per importare moduli custom
# Questo permette di fare "from config import ..." ovunque nel progetto
sys.path.append(str(BASE_PATH))

# ============================================================================
# SETUP LOGGING
# ============================================================================
# Il logging è fondamentale per debugging e monitoraggio in produzione
# Invece di usare print(), usiamo logger.info/warning/error per:
# - Avere timestamp automatici
# - Salvare su file oltre che console
# - Filtrare per livello (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(
    level=logging.INFO,  # Mostra solo messaggi INFO e superiori
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output su console
        logging.FileHandler(BASE_PATH / 'ml_system.log')  # Output su file
    ]
)
logger = logging.getLogger(__name__)  # Logger specifico per questo modulo


# ============================================================================
# CARICAMENTO CONFIGURAZIONE
# ============================================================================
# La configurazione è centralizzata in config.py e file .env
# Questo permette di cambiare impostazioni senza modificare codice
try:
    # Importa funzioni e variabili dal modulo config
    from config import validate_config, CUDA_VISIBLE_DEVICES, PYTORCH_CUDA_ALLOC_CONF
    
    # Valida che tutte le configurazioni necessarie siano presenti
    validate_config()
    
    # Imposta variabili d'ambiente per PyTorch/CUDA
    # Queste controllano quale GPU usare e come allocare memoria
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = PYTORCH_CUDA_ALLOC_CONF
    os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_VISIBLE_DEVICES
    
    logger.info(f"[OK] Configuration loaded successfully")
    
except Exception as e:
    # Se la configurazione fallisce, logga l'errore ma non blocca il programma
    # L'utente vedrà l'errore e potrà correggere config.py o .env
    logger.error(f"❌ Configuration error: {e}")
    logger.warning("⚠️  Continuing with default configuration...")

    print(f"Error loading configuration: {e}")
    print("Please ensure config.py exists and .env is properly configured.")
    sys.exit(1)

# ============================================================================
# 📁 FUNZIONE: CREAZIONE STRUTTURA DIRECTORY
# ============================================================================
# Questa funzione è fondamentale per garantire che tutte le directory
# necessarie al funzionamento del sistema esistano. Python richiede che
# ogni directory contenente moduli abbia un file __init__.py per essere
# riconosciuta come package.

def ensure_directories():
    """
    Crea la struttura completa di directory del progetto
    
    Organizzazione directory:
        module/                  → Codice sorgente modulare
        ├── model/              → Classi per modelli ML
        ├── tasks/              → Task specifici (generation, classification)
        ├── data/               → Utilità per dataset
        ├── preprocessing/      → Parser e filtri
        ├── storage/            → Cloud storage manager
        └── utils/              → Funzioni di supporto
        
        models/                 → Modelli addestrati salvati (.bin, .pt)
        dataset_storage/        → Dataset raccolti da GitHub
        reports/                → Report di training e validazione
        temp/                   → File temporanei (repository clonati)
    
    Il metodo mkdir():
        parents=True  → Crea anche directory parent se non esistono
        exist_ok=True → Non genera errore se directory già esiste
    
    File __init__.py:
        - Rende una directory un "Python package"
        - Permette import: from module.model import ModelManager
        - Può contenere codice di inizializzazione (qui è vuoto)
    
    Returns:
        None (side effect: crea directory sul filesystem)
    
    Raises:
        PermissionError: Se l'utente non ha permessi di scrittura
        OSError: Se disco è pieno o path non valido
    """
    # Lista di tutte le directory necessarie
    # Ordine importante: prima parent, poi children
    required_folders = [
        "module",                          # Root del codice
        "module/model",                    # Modelli ML
        "module/tasks",                    # Task handlers
        "module/data",                     # Dataset utilities
        "module/preprocessing",            # Parser e filtri
        "module/storage",                  # Cloud storage
        "module/utils",                    # Helper functions
        "models",                          # Modelli salvati
        "dataset_storage",                 # Dataset locali
        "dataset_storage/local_backup",    # Backup locale (deprecato v1.1)
        "dataset_storage/local_backup/code_generation",  # Legacy
        "reports",                         # Report generati
        "temp"                            # File temporanei
    ]
    
    # Itera su ogni folder e crea se non esiste
    for folder in required_folders:
        # Costruisce path assoluto (BASE_PATH è directory di main.py)
        path = BASE_PATH / folder
        
        # Crea directory (ricorsivamente se necessario)
        path.mkdir(parents=True, exist_ok=True)
        
        # Crea file __init__.py per renderla un Python package
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)  # Crea se non esiste
    
    # Log conferma creazione struttura
    logger.info("[OK] Directory structure verified and created")
    logger.debug(f"Created {len(required_folders)} directories")


# ============================================================================
# 📊 FUNZIONE: DATA COLLECTION DA GITHUB
# ============================================================================
# Questa è la funzione centrale per la raccolta dati. Gestisce tre modalità:
# 1. Repository singolo (--repo URL)
# 2. Lista da file (--repos-file path)
# 3. Repository popolari per linguaggio (--language python --count 20)

def collect_data_from_repos(language=None, count=10, repo_url=None, repos_file=None, workers=4, with_context=False):
    """
    Raccoglie funzioni di codice da repository GitHub e salva nel cloud
    
    Pipeline completa:
        1. Clone repository in directory temp
        2. Scansiona file .py/.js/.java etc.
        3. Parse con Tree-sitter (estrae funzioni)
        4. Filtra qualità (elimina boilerplate)
        5. Check duplicati (hash MD5)
        6. Formatta in JSON
        7. Upload a cloud storage (batch da 100)
        8. Cleanup (elimina repository clonato)
    
    Args:
        language (str, optional): Linguaggio di programmazione da cercare
            Valori supportati: python, javascript, java, cpp, go, ruby, rust
            Se specificato, cerca i repository più popolari per quel linguaggio
            Esempio: language="python" → Cerca su GitHub repo Python con più stelle
            
        count (int, optional): Numero di repository da processare
            Default: 10
            Range consigliato: 1-50 (più repo = più tempo)
            Esempio: count=20 → Processa i top 20 repository
            
        repo_url (str, optional): URL di un singolo repository
            Formato: https://github.com/owner/repo
            Se specificato, ignora language e count
            Esempio: repo_url="https://github.com/psf/requests"
            
        repos_file (str, optional): Path a file con lista di repository
            Formato file: un URL per riga
            Esempio file repos.txt:
                https://github.com/psf/requests
                https://github.com/django/django
                https://github.com/pallets/flask
                
        workers (int, optional): Numero di thread paralleli
            Default: 4
            Range: 1-16 (più worker = più veloce ma più memoria)
            Attenzione: troppi worker possono causare rate limit GitHub
    
    Returns:
        None (side effect: salva dati su cloud storage)
    
    Raises:
        ValueError: Se nessun parametro specificato (language, repo_url, repos_file)
        PermissionError: Se mancano permessi per scrivere su disk
        ConnectionError: Se cloud storage non raggiungibile
        RateLimitError: Se si supera rate limit GitHub (5000 richieste/ora)
    
    Esempio d'uso:
        # Modalità 1: Repository singolo
        collect_data_from_repos(repo_url="https://github.com/psf/requests")
        
        # Modalità 2: Repository popolari
        collect_data_from_repos(language="python", count=50)
        
        # Modalità 3: Lista custom
        collect_data_from_repos(repos_file="my_repos.txt", workers=8)
    
    Note:
        - Richiede GitHub token in .env: GITHUB_TOKEN=ghp_xxx
        - Richiede cloud storage configurato in .env
        - Repository clonati con --depth 1 (solo ultimo commit)
        - Salva batch da 100 funzioni (configurable in GitHubRepoProcessor)
    """
    # Header visivo per separare sezioni nel log
    logger.info("="*60)
    logger.info("FASE 1: DATA COLLECTION DA GITHUB REPOSITORIES")
    logger.info("="*60)
    
    try:
        # Import dinamico (carica modulo solo quando serve)
        # Questo riduce tempo di startup se si usa altro comando
        from github_repo_processor import GitHubRepoProcessor
        
        # Inizializza processor con configurazione AVANZATA
        processor = GitHubRepoProcessor(
            cloud_save=True,                # Salva su cloud (DigitalOcean/AWS/etc.)
            max_file_size_mb=10,            # Ignora file > 10MB (probabilmente non codice)
            batch_size=100,                 # Salva ogni 100 funzioni estratte
            extraction_mode='hybrid',       # 70% funzioni + 30% file completi
            use_advanced_quality=True,      # Usa radon per quality scoring
            enable_docstring_pairs=True,    # Estrai coppie docstring→code
            include_context=with_context    # Include imports, parent class, file path if True
        )
        
        # ===== MODALITÀ 1: Repository Singolo =====
        if repo_url:
            logger.info(f"Processing single repository: {repo_url}")
            print(f"\n[*] Processing: {repo_url}")
            
            # Processa repository (clone → extract → save → cleanup)
            stats = processor.process_repository(repo_url)
            
            # Mostra risultati
            print(f"[OK] Extracted {stats['functions_extracted']} functions")
            print(f"     Files processed: {stats.get('files_processed', 0)}")
            print(f"     Duration: {stats.get('duration', 0):.1f}s")

            # Aggiorna statistiche globali
            processor.stats['repos_processed'] += 1
            processor.stats['files_processed'] += stats.get('files_processed', 0)
            processor.stats['functions_extracted'] += stats.get('functions_extracted', 0)

            # Stampa report finale
            processor.print_statistics()
            
        # ===== MODALITÀ 2: Lista da File =====
        elif repos_file:
            logger.info(f"Processing repositories from file: {repos_file}")
            print(f"\n[*] Reading repository list: {repos_file}")
            
            # Verifica file esiste
            if not Path(repos_file).exists():
                raise FileNotFoundError(f"Repository list not found: {repos_file}")
            
            # Processa lista con worker paralleli
            processor.process_repos_from_file(repos_file, max_workers=workers)
            
        # ===== MODALITÀ 3: Repository Popolari per Linguaggio =====
        elif language:
            # Repository popolari per linguaggio
            logger.info(f"Processing popular {language} repositories")
            repos = processor.get_popular_repos(language, count)
            
            if not repos:
                logger.error(f"No repositories found for language: {language}")
                print(f"[FAIL] No repositories configured for language: {language}")
                return
            
            print(f"\n[*] Processing {len(repos)} {language} repositories...")
            for i, repo_url in enumerate(repos, 1):
                print(f"\n[{i}/{len(repos)}] Processing: {repo_url}")
                try:
                    stats = processor.process_repository(repo_url)
                    print(f"  [OK] Extracted: {stats['functions_extracted']} functions")

                    # Update processor statistics
                    processor.stats['repos_processed'] += 1
                    processor.stats['files_processed'] += stats.get('files_processed', 0)
                    processor.stats['functions_extracted'] += stats.get('functions_extracted', 0)

                except Exception as e:
                    print(f"  [FAIL] Error: {e}")
                    logger.error(f"Failed to process {repo_url}: {e}")
                    processor.stats['errors'] += 1
            
            processor.print_statistics()
        else:
            print("[FAIL] Error: Specify --language, --repo, or --repos-file")
            logger.error("No data collection parameters specified")
            
    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        print(f"\n[FAIL] Data collection failed: {e}")
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
                print(f"[FAIL] File not found: {repos_file}")
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
            print(f"[FAIL] Unknown source: {source}")
            print("Available sources: github, huggingface, local")
            
    except Exception as e:
        logger.error(f"Bulk processing failed: {e}", exc_info=True)
        print(f"\n[FAIL] Bulk processing failed: {e}")
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
        from infrastructure.training.model_manager import ModelManager
        from config import MODEL_PATHS, DEFAULT_BATCH_SIZE, DEFAULT_EPOCHS, DEFAULT_LEARNING_RATE

        if task not in MODEL_PATHS:
            logger.error(f"Unknown task: {task}")
            print(f"[FAIL] Error: Unknown task '{task}'")
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
            # Try to download from cloud if AUTO_DOWNLOAD_DATASETS is enabled
            auto_download = os.getenv('AUTO_DOWNLOAD_DATASETS', 'false').lower() == 'true'
            
            if auto_download:
                logger.info("Dataset not found locally, attempting cloud download...")
                print(f"\n[CLOUD] Dataset not found: {dataset_path}")
                print("[CLOUD] Attempting to download from cloud storage...")
                
                try:
                    from config.container import Container
from application.services.storage_service import StorageService
                    storage = StorageManager()
                    
                    if storage.connect():
                        print("[CLOUD] Connected to cloud storage")
                        stats = storage.download_datasets()
                        print(f"[CLOUD] Downloaded {stats.get('downloaded', 0)} files")
                        
                        # Check again if dataset exists
                        if Path(dataset_path).exists():
                            print(f"[OK] Dataset downloaded successfully: {dataset_path}")
                            logger.info(f"Dataset downloaded from cloud: {dataset_path}")
                        else:
                            print(f"[FAIL] Dataset not found in cloud storage: {dataset_path}")
                            logger.error(f"Dataset not in cloud storage: {dataset_path}")
                            return
                    else:
                        print("[FAIL] Could not connect to cloud storage")
                        logger.error("Cloud storage connection failed")
                        return
                        
                except Exception as e:
                    logger.error(f"Failed to download dataset from cloud: {e}")
                    print(f"[FAIL] Cloud download failed: {e}")
                    return
            else:
                logger.error(f"Dataset not found: {dataset_path}")
                print(f"\n[FAIL] Dataset not found: {dataset_path}")
                print("Options:")
                print(f"  1. Run data collection: python main.py --collect-data --language python")
                print(f"  2. Download from cloud: python main.py --sync download")
                print(f"  3. Enable auto-download: Set AUTO_DOWNLOAD_DATASETS=true in .env")
                return

        # Instantiate model manager
        print("\n[*] Loading model and tokenizer...")
        model_manager = ModelManager(task=task, model_name=model_name)

        # Select appropriate trainer
        if task in ["code_generation"]:
            logger.info("Using AdvancedTrainer for generation task")
            from infrastructure.training.advanced_trainer import AdvancedTrainer
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
            from infrastructure.training.advanced_trainer import AdvancedTrainer
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
                print("\n[CLOUD] Uploading model to cloud storage...")
                from config.container import Container
from application.services.storage_service import StorageService
                storage = StorageManager()
                if storage.connect():
                    storage.backup_model(f"models/{task}", model_name=f"{task}_latest")
                    print("[OK] Cloud backup completed")
        except Exception as e:
            logger.warning(f"Cloud backup failed: {e}")
            print(f"[WARN] Cloud backup failed: {e}")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        print(f"\n[FAIL] Training failed: {e}")
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
        print(f"\n[FAIL] Validation failed: {e}")


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
            print(f"[FAIL] Error: UI file not found at {app_path}")
            return

        print("\n[*] Starting web interface...")
        print("[INFO] Interface will be available at: http://localhost:8501")
        print("[INFO] Press Ctrl+C to stop the application")
        
        import signal
        
        def handle_shutdown(signum, frame):
            """Handle shutdown signals gracefully"""
            logger.info("Stopping application...")
            print("\n[INFO] Shutting down application...")
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
        print("\n[FAIL] Streamlit is not installed. Run:")
        print("   pip install streamlit")
    except Exception as e:
        logger.error(f"UI error: {str(e)}")
        print(f"\n[FAIL] Error: {str(e)}")


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

        print("\n[*] Interactive pipeline active (type 'exit' to quit)\n")
        while True:
            text = input("[INPUT] Enter request or code: ")
            if text.strip().lower() == "exit":
                break

            result = pipeline.process(text)
            print(f"[OK] Result: {result}\n")
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        print(f"\n[FAIL] Pipeline error: {e}")


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
        from config.container import Container
from application.services.storage_service import StorageService
        
        storage = StorageManager()
        if not storage.connect():
            print("[FAIL] Failed to connect to cloud storage")
            logger.error("Cloud storage connection failed")
            return
        
        print(f"\n[CLOUD] Cloud storage connected: {storage.config.get('provider_type')}")
        
        if direction == 'download':
            print("[DOWNLOAD] Downloading datasets...")
            storage.download_datasets()
            print("[DOWNLOAD] Downloading models...")
            storage.download_models()
            
        elif direction == 'upload':
            print("[UPLOAD] Uploading datasets...")
            storage.upload_datasets()
            print("[UPLOAD] Uploading models...")
            storage.upload_models()
            
        print("[OK] Cloud sync completed")
        
    except Exception as e:
        logger.error(f"Cloud sync failed: {e}", exc_info=True)
        print(f"\n[FAIL] Cloud sync failed: {e}")


# ==================== THE STACK DOWNLOAD ====================

def download_from_stack(languages=None, language=None, count=10000,
                       min_stars=0, min_quality=60):
    """
    Download and process datasets from The Stack (HuggingFace).

    Args:
        languages: List of languages
        language: Single language
        count: Examples per language
        min_stars: Minimum repository stars
        min_quality: Minimum quality score
    """
    logger.info("="*60)
    logger.info("DOWNLOADING FROM THE STACK DATASET")
    logger.info("="*60)

    try:
        from integrations.the_stack_loader import TheStackLoader

        # Determine languages
        langs = languages if languages else ([language] if language else ['python'])

        logger.info(f"Languages: {', '.join(langs)}")
        logger.info(f"Examples per language: {count:,}")
        logger.info(f"Minimum stars: {min_stars}")
        logger.info(f"Minimum quality: {min_quality}")

        # Initialize loader
        loader = TheStackLoader(
            output_dir="dataset_storage/the_stack",
            min_quality_score=min_quality,
            use_ast_dedup=True
        )

        # Download and process
        loader.download_and_process(
            languages=langs,
            count_per_language=count,
            batch_size=100,
            min_stars=min_stars
        )

        logger.info("[OK] The Stack download completed")
        print("\n[OK] The Stack download completed")
        print(f"Dataset saved to: dataset_storage/the_stack/")

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"[FAIL] Missing dependency: {e}")
        print("[INFO] Install required packages:")
        print("  pip install datasets radon")
    except Exception as e:
        logger.error(f"The Stack download failed: {e}", exc_info=True)
        print(f"\n[FAIL] Download failed: {e}")
        raise


# ==================== DOMAIN ADAPTIVE TRAINING ====================

def train_adaptive(task, dataset_path=None, base_model='Salesforce/codegen-350M-mono',
                  num_epochs=3, batch_size=8, learning_rate=2e-5,
                  warmup_ratio=0.1, gradient_accumulation=1,
                  fp16=False, max_length=1024, evaluate=False):
    """
    Perform domain-adaptive training on pre-trained model.

    Args:
        task: Task name for organizing outputs
        dataset_path: Path to dataset
        base_model: HuggingFace base model
        num_epochs: Training epochs
        batch_size: Batch size
        learning_rate: Learning rate (lower than pre-training)
        warmup_ratio: Warmup ratio
        gradient_accumulation: Gradient accumulation steps
        fp16: Use mixed precision
        max_length: Max sequence length
        evaluate: Run evaluation after training
    """
    logger.info("="*60)
    logger.info(f"DOMAIN ADAPTIVE TRAINING - {task.upper()}")
    logger.info("="*60)

    try:
        from training.domain_adaptive_trainer import DomainAdaptiveTrainer
        from config import MODEL_PATHS

        # Determine dataset path
        if not dataset_path:
            # Try to find dataset in common locations
            possible_paths = [
                f"dataset_storage/the_stack/python/*.jsonl",
                f"dataset_storage/local_backup/code_generation/*.jsonl",
                f"dataset_storage/*.jsonl"
            ]

            for path_pattern in possible_paths:
                from glob import glob
                files = glob(path_pattern)
                if files:
                    dataset_path = files[0]
                    logger.info(f"Auto-detected dataset: {dataset_path}")
                    break

            if not dataset_path:
                logger.error("No dataset found")
                print("[FAIL] No dataset found in common locations")
                print("\nOptions:")
                print("  1. Download from The Stack: python main.py --download-stack")
                print("  2. Collect from GitHub: python main.py --collect-data")
                print("  3. Specify path: python main.py --train-adaptive code_generation --dataset path/to/dataset.jsonl")
                return

        # Verify dataset exists
        from pathlib import Path
        if not Path(dataset_path).exists() and not glob(dataset_path):
            logger.error(f"Dataset not found: {dataset_path}")
            print(f"[FAIL] Dataset not found: {dataset_path}")
            return

        # Initialize trainer
        output_dir = f"models/{task}_adapted"
        trainer = DomainAdaptiveTrainer(
            base_model=base_model,
            output_dir=output_dir,
            use_gpu=True
        )

        # Prepare dataset
        logger.info("Preparing dataset...")
        print("[*] Preparing dataset...")
        train_dataset, val_dataset = trainer.prepare_dataset(
            dataset_path=dataset_path,
            max_length=max_length
        )

        # Train
        print(f"\n[*] Starting domain adaptive training...")
        print(f"    Base model: {base_model}")
        print(f"    Task: {task}")
        print(f"    Epochs: {num_epochs}")
        print(f"    Batch size: {batch_size}")
        print(f"    Learning rate: {learning_rate}")

        result = trainer.train(
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            num_epochs=num_epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_ratio=warmup_ratio,
            gradient_accumulation_steps=gradient_accumulation,
            fp16=fp16
        )

        # Evaluate if requested
        if evaluate:
            logger.info("Evaluating adapted model...")
            print("\n[*] Evaluating model with test prompts...")
            trainer.evaluate_model()

        logger.info(f"[OK] Adaptive training completed: {output_dir}")
        print(f"\n[OK] Model saved to: {output_dir}")

        # Optional: Upload to cloud
        if os.getenv('AUTO_BACKUP_AFTER_TRAINING', 'false').lower() == 'true':
            try:
                from config.container import Container
from application.services.storage_service import StorageService
                storage = StorageManager()
                if storage.connect():
                    storage.backup_model(output_dir, model_name=f"{task}_adapted_latest")
                    print("[OK] Cloud backup completed")
            except Exception as e:
                logger.warning(f"Cloud backup failed: {e}")

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"[FAIL] Missing dependency: {e}")
        print("Install required packages: pip install transformers datasets torch")
    except Exception as e:
        logger.error(f"Adaptive training failed: {e}", exc_info=True)
        print(f"\n[FAIL] Adaptive training failed: {e}")
        raise


# ==================== ENHANCED DATASET BUILDING ====================

def build_dataset_enhanced(source, subset='python', count=100000,
                          repos_file=None, repo_urls=None, directory=None,
                          language='python', min_quality=60,
                          extraction_mode='hybrid', enable_docstring_pairs=False,
                          upload_cloud=False, output_dir='dataset_storage'):
    """
    Build dataset using unified builder with context-aware extraction.

    Args:
        source: Data source (the-stack, github, local)
        subset: Language subset
        count: Number of examples
        repos_file: GitHub repos file
        repo_urls: List of GitHub URLs
        directory: Local directory
        language: Programming language
        min_quality: Quality threshold
        extraction_mode: Extraction mode
        enable_docstring_pairs: Extract doc→code pairs
        upload_cloud: Upload to cloud
        output_dir: Output directory
    """
    logger.info("="*60)
    logger.info("ENHANCED DATASET BUILDING")
    logger.info("="*60)

    try:
        from dataset_builder import DatasetBuilder

        logger.info(f"Source: {source}")
        logger.info(f"Language: {language if source == 'local' else subset}")
        logger.info(f"Extraction mode: {extraction_mode}")
        logger.info(f"Quality threshold: {min_quality}")

        # Initialize builder
        builder = DatasetBuilder(
            min_quality_score=min_quality,
            use_ast_dedup=True,
            extraction_mode=extraction_mode,
            enable_docstring_pairs=enable_docstring_pairs,
            upload_cloud=upload_cloud,
            output_dir=output_dir
        )

        # Build based on source
        if source == 'the-stack':
            logger.info(f"Building from The Stack ({subset} subset)")
            print(f"[*] Building from The Stack ({subset} subset)")
            builder.build_from_the_stack(subset=subset, count=count)

        elif source == 'github':
            logger.info("Building from GitHub repositories")
            print("[*] Building from GitHub repositories")
            if repos_file:
                builder.build_from_github(repos_file=repos_file)
            elif repo_urls:
                builder.build_from_github(repo_urls=repo_urls)
            else:
                logger.error("GitHub source requires --repos-file or --repos")
                print("[FAIL] Specify --repos-file or --repos for GitHub source")
                return

        elif source == 'local':
            logger.info(f"Building from local directory: {directory}")
            print(f"[*] Building from local directory: {directory}")
            if not directory:
                logger.error("Local source requires --directory")
                print("[FAIL] Specify --directory for local source")
                return
            builder.build_from_local(directory=directory, language=language)

        else:
            logger.error(f"Unknown source: {source}")
            print(f"[FAIL] Unknown source: {source}")
            return

        logger.info("[OK] Dataset building completed")
        print(f"\n[OK] Dataset saved to: {output_dir}")

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"[FAIL] Missing dependency: {e}")
    except Exception as e:
        logger.error(f"Dataset building failed: {e}", exc_info=True)
        print(f"\n[FAIL] Dataset building failed: {e}")
        raise


# ==================== STATISTICS ====================

def show_stats():
    """Mostra statistiche sui dataset e modelli"""
    logger.info("="*60)
    logger.info("SYSTEM STATISTICS")
    logger.info("="*60)
    
    print("\n[STATS] System Statistics\n")
    print("="*60)

    # Dataset statistics
    print("\n[DATA] Datasets:")
    datasets_dir = BASE_PATH / "dataset_storage"
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
    print("\n[MODEL] Models:")
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
    print("\n[CACHE] Duplicate Cache:")
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
    # ========================================================================
    # DEPRECATION WARNING
    # ========================================================================
    import warnings
    warnings.warn(
        "\n" + "="*70 + "\n" +
        "DEPRECATION WARNING: main.py is deprecated!\n" +
        "Please use the new CLI interface instead:\n\n" +
        "  python -m presentation.cli --help\n\n" +
        "This file will be removed in v3.0.0\n" +
        "See MIGRATION_GUIDE.md for migration instructions.\n" +
        "="*70,
        DeprecationWarning,
        stacklevel=2
    )
    print("\n" + "="*70)
    print("⚠️  DEPRECATION WARNING")
    print("="*70)
    print("This main.py is deprecated and will be removed in v3.0.0")
    print("\nPlease use the new CLI interface:")
    print("  python -m presentation.cli --help")
    print("\nSee MIGRATION_GUIDE.md for migration instructions.")
    print("="*70 + "\n")

    # ========================================================================
    # END DEPRECATION WARNING
    # ========================================================================

    parser = argparse.ArgumentParser(
        description='ML Code Intelligence System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Data Collection
  python main.py --collect-data --language python --count 20
  python main.py --collect-data --repo https://github.com/user/repo
  python main.py --collect-data --repos-file repo_list.txt --workers 4
  python main.py --collect-data --language python --with-context  # Include imports & context

  # Download from The Stack Dataset (HuggingFace)
  python main.py --download-stack --stack-languages python javascript
  python main.py --download-stack --stack-languages python --stack-count 50000 --stack-min-stars 100
  python main.py --download-stack --stack-languages java --stack-min-quality 80

  # Build Enhanced Dataset
  python main.py --build-dataset --data-source local --extraction-mode hybrid
  python main.py --build-dataset --data-source the-stack --with-context
  python main.py --build-dataset --extraction-mode functions --max-file-size 2000

  # Domain Adaptive Training (100x faster than from scratch)
  python main.py --train-adaptive --adaptive-dataset dataset.jsonl
  python main.py --train-adaptive --base-model bigcode/santacoder --adaptive-dataset data.jsonl
  python main.py --train-adaptive --adaptive-dataset data.jsonl --fp16 --adaptive-epochs 5 --evaluate-model

  # Bulk Processing
  python main.py --bulk-process --repos-file repo_list.txt

  # Training (Standard)
  python main.py --train code_generation
  python main.py --train text_classification

  # Training (Advanced - with metrics, validation, reports)
  python main.py --train-adv code_generation
  python main.py --train-adv code_generation --epochs 5 --batch-size 8
  python main.py --train-adv code_generation --experiment my_experiment

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
    action_group.add_argument('--train-adv', type=str, metavar='TASK',
                             choices=['code_generation', 'text_classification', 'security_classification'],
                             help='Advanced training with full orchestration (metrics, validation, reports)')
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
    action_group.add_argument('--download-stack', action='store_true',
                             help='Download high-quality code from The Stack dataset')
    action_group.add_argument('--train-adaptive', action='store_true',
                             help='Domain adaptive training from pre-trained model (100x faster than from scratch)')
    action_group.add_argument('--build-dataset', action='store_true',
                             help='Build enhanced training dataset with context')

    # Test connection storage
    parser.add_argument('--test-connection', action='store_true',
                       help='Test cloud storage connection')

    # The Stack download options
    parser.add_argument('--stack-languages', type=str, nargs='+',
                       help='Languages to download from The Stack (e.g., python javascript java)')
    parser.add_argument('--stack-count', type=int, default=10000,
                       help='Number of examples per language (default: 10000)')
    parser.add_argument('--stack-min-stars', type=int, default=0,
                       help='Minimum repository stars (default: 0)')
    parser.add_argument('--stack-min-quality', type=int, default=60,
                       help='Minimum quality score 0-100 (default: 60)')

    # Domain adaptive training options
    parser.add_argument('--base-model', type=str, default='Salesforce/codegen-350M-mono',
                       help='Base model for adaptive training (default: Salesforce/codegen-350M-mono)')
    parser.add_argument('--adaptive-dataset', type=str,
                       help='Dataset for adaptive training (JSONL format)')
    parser.add_argument('--adaptive-epochs', type=int, default=3,
                       help='Number of adaptive training epochs (default: 3)')
    parser.add_argument('--fp16', action='store_true',
                       help='Use mixed precision training (faster on GPU)')
    parser.add_argument('--output-model', type=str, default='models/adapted',
                       help='Output directory for adapted model')
    parser.add_argument('--evaluate-model', action='store_true',
                       help='Evaluate model after training')

    # Enhanced dataset building options
    parser.add_argument('--data-source', type=str, default='local',
                       choices=['local', 'github', 'the-stack'],
                       help='Data source for dataset building')
    parser.add_argument('--extraction-mode', type=str, default='hybrid',
                       choices=['functions', 'files', 'hybrid'],
                       help='Extraction mode: functions only, files only, or hybrid (default: hybrid)')
    parser.add_argument('--with-context', action='store_true',
                       help='Include context (imports, parent class) in dataset')
    parser.add_argument('--max-file-size', type=int, default=5000,
                       help='Maximum file size in lines (default: 5000)')

    # Data collection options
    parser.add_argument('--language', type=str,
                       help='Programming language for data collection')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of repositories to process')
    parser.add_argument('--repo', type=str,
                       help='Single repository URL to process')
    parser.add_argument('--repos-file', type=str,
                       help='File containing repository URLs')
    parser.add_argument('--directory', type=str,
                       help='Local directory to process (for --data-source local)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers')
    
    # Training options
    parser.add_argument('--dataset', type=str,
                       help='Custom dataset path for training')
    parser.add_argument('--model', type=str,
                       help='Custom model name for training')
    parser.add_argument('--epochs', type=int,
                       help='Number of training epochs (for --train-adv)')
    parser.add_argument('--batch-size', type=int,
                       help='Batch size for training (for --train-adv)')
    parser.add_argument('--learning-rate', type=float,
                       help='Learning rate for training (for --train-adv)')
    parser.add_argument('--experiment', type=str,
                       help='Experiment name for tracking (for --train-adv)')

    # Bulk processing options
    parser.add_argument('--source', type=str, default='github',
                       choices=['github', 'huggingface', 'local'],
                       help='Data source for bulk processing')
    # clean file cleanup_temp_repos.py
    parser.add_argument('--clean', action='store_true',
                       help='Clean up temporary repository files')

    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Execute requested action
    try:
        if args.check_deps:
            try:
                from check_dependencies import check_dependencies
                deps_ok = check_dependencies()
                if not deps_ok:
                    logger.warning("Alcune dipendenze critiche non sono soddisfatte")
                    print("\n[WARN] ATTENZIONE: Alcune dipendenze critiche mancano o sono obsolete")
                    print("   Esegui: python check_dependencies.py --install")
                    print("   Oppure: pip install -r requirements.txt\n")
            except ImportError as e:
                logger.warning(f"Impossibile controllare le dipendenze: {e}")
            except Exception as e:
                logger.warning(f"Errore durante il controllo delle dipendenze: {e}")
    
        elif args.test_connection:
            from config.container import Container
from application.services.storage_service import StorageService
            storage_manager = StorageManager()
            if storage_manager.connect():
                print("[OK] Cloud storage connection successful")
                logger.info("Cloud storage connection successful")
            else:
                print("[FAIL] Cloud storage connection failed")
                logger.error("Cloud storage connection failed")

        elif args.collect_data:
            # Validate input parameters
            if args.language:
                valid_languages = ['python', 'javascript', 'java', 'cpp', 'go', 'ruby', 'rust', 'php']
                if args.language.lower() not in valid_languages:
                    print(f"[FAIL] Invalid language: {args.language}")
                    print(f"Valid languages: {', '.join(valid_languages)}")
                    logger.error(f"Invalid language specified: {args.language}")
                    return
            
            if args.count:
                if args.count < 1 or args.count > 1000:
                    print(f"[FAIL] Invalid count: {args.count}")
                    print("Count must be between 1 and 1000")
                    logger.error(f"Invalid count specified: {args.count}")
                    return
            
            if args.workers:
                if args.workers < 1 or args.workers > 32:
                    print(f"[FAIL] Invalid workers: {args.workers}")
                    print("Workers must be between 1 and 32")
                    logger.error(f"Invalid workers specified: {args.workers}")
                    return
            
            collect_data_from_repos(
                language=args.language,
                count=args.count,
                repo_url=args.repo,
                repos_file=args.repos_file,
                workers=args.workers,
                with_context=args.with_context
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

        elif args.train_adv:
            from train_advanced_impl import train_advanced
            train_advanced(
                task=args.train_adv,
                dataset_path=args.dataset,
                model_name=args.model,
                num_epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                experiment_name=args.experiment
            )

        elif args.download_stack:
            # Download from The Stack dataset
            languages = args.stack_languages or ['python']
            download_from_stack(
                languages=languages,
                count=args.stack_count,
                min_stars=args.stack_min_stars,
                min_quality=args.stack_min_quality
            )

        elif args.train_adaptive:
            # Domain adaptive training
            if not args.adaptive_dataset:
                print("[FAIL] --adaptive-dataset is required for adaptive training")
                print("Usage: python main.py --train-adaptive --adaptive-dataset dataset.jsonl")
                return

            train_adaptive(
                base_model=args.base_model,
                dataset_path=args.adaptive_dataset,
                output_dir=args.output_model,
                epochs=args.adaptive_epochs,
                batch_size=args.batch_size or 8,
                learning_rate=args.learning_rate or 2e-5,
                fp16=args.fp16,
                evaluate=args.evaluate_model
            )

        elif args.build_dataset:
            # Build enhanced dataset
            build_dataset_enhanced(
                source=args.data_source,
                extraction_mode=args.extraction_mode,
                subset=args.stack_languages[0] if args.stack_languages else 'python',
                count=getattr(args, 'count', 100000),
                min_quality=getattr(args, 'min_quality', 60),
                enable_docstring_pairs=True,
                upload_cloud=getattr(args, 'upload_cloud', False),
                directory=getattr(args, 'directory', None),
                repos_file=getattr(args, 'repos_file', None),
                repo_urls=getattr(args, 'repos', None)
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
        
        elif args.clean:
            from cleanup_temp_repos import RepoCleanup
            cleaner = RepoCleanup(dry_run=False, verbose=True)

            cleaner.cleanup(datasets_only=True)
            
        else:
            parser.print_help()
            print("\n[INFO] Quick Start:")
            print("  1. python main.py --collect-data --language python --count 10")
            print("  2. python main.py --train code_generation")
            print("  3. python main.py --ui")
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Operation cancelled by user")
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[FAIL] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
