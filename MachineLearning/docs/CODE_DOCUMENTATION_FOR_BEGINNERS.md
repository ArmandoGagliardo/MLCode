# 📚 DOCUMENTAZIONE CODICE PER AUTODIDATTI

## Guida Completa alla Comprensione del Progetto

**Target:** Sviluppatori autodidatti che vogliono capire come funziona il sistema  
**Livello:** Intermedio (richiede conoscenza base di Python)  
**Tempo lettura:** ~2 ore

---

## 📖 INDICE

1. [Architettura Generale](#architettura-generale)
2. [Concetti Chiave](#concetti-chiave)
3. [Flusso di Esecuzione](#flusso-di-esecuzione)
4. [File per File](#file-per-file)
5. [Concetti Avanzati](#concetti-avanzati)
6. [Pattern e Best Practices](#pattern-e-best-practices)
7. [Debugging e Troubleshooting](#debugging-e-troubleshooting)

---

## 🏗️ ARCHITETTURA GENERALE

### Il Sistema in 3 Frasi:
1. **Raccoglie** codice da GitHub → Lo pulisce e lo salva
2. **Addestra** un modello AI con quel codice
3. **Usa** il modello per generare nuovo codice o classificarlo

### Architettura a Livelli:

```
┌─────────────────────────────────────────────────┐
│  main.py - INTERFACCIA UTENTE (CLI)            │
│  "Cosa vuoi fare? Raccogliere dati? Training?" │
└──────────────────┬──────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌─────────────┐           ┌──────────────┐
│ RACCOLTA    │           │  TRAINING    │
│ DATI        │           │  MODELLI     │
└──────┬──────┘           └──────┬───────┘
       │                         │
       ▼                         ▼
┌─────────────────┐     ┌────────────────┐
│ github_repo_    │     │ training_      │
│ processor.py    │     │ model_*.py     │
│                 │     │                │
│ • Clone repo    │     │ • Load data    │
│ • Parse code    │     │ • Train AI     │
│ • Extract funcs │     │ • Save model   │
└────────┬────────┘     └────────┬───────┘
         │                       │
         ▼                       ▼
┌────────────────────────────────────────┐
│  STORAGE LAYER (Salvataggio Cloud)    │
│  storage_manager.py                    │
│  • Upload a DigitalOcean/AWS/etc.     │
│  • Download quando serve              │
└────────────────────────────────────────┘
```

---

## 🎯 CONCETTI CHIAVE

### 1. **Tree-Sitter: Il Parser Magico** 🌲

**Cos'è:** Una libreria che "capisce" la sintassi del codice

**Analogia:** Immagina di avere un testo in italiano. Tree-sitter è come un grammatico che:
- Identifica soggetto, verbo, complemento
- Capisce dove inizia e finisce una frase
- Riconosce citazioni, parentesi, ecc.

Ma lo fa per il **codice**!

```python
# Codice da analizzare
def calculate_sum(a, b):
    """Somma due numeri."""
    return a + b

# Tree-sitter lo vede così (AST - Abstract Syntax Tree):
function_definition
├── name: "calculate_sum"
├── parameters: (a, b)
├── docstring: "Somma due numeri."
└── body: return a + b
```

**Nel nostro progetto:** `module/preprocessing/universal_parser_new.py`
- Prende codice Python/JavaScript/Java/etc.
- Estrae SOLO le funzioni
- Salva: nome, parametri, docstring, corpo

---

### 2. **HuggingFace Transformers: L'AI** 🤗

**Cos'è:** Libreria con modelli AI pre-addestrati (come GPT, BERT)

**Analogia:** Immagina di voler insegnare a un bambino a scrivere:
1. **Pre-training:** Il bambino legge 1000 libri (fatto da HuggingFace)
2. **Fine-tuning:** Tu gli insegni il TUO stile specifico (questo progetto)

**Nel nostro progetto:** `module/model/training_model_advanced.py`
```python
# Carica modello pre-addestrato (già sa programmare in generale)
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-350M-mono")

# Lo addestriamo sul NOSTRO codice (impara lo stile dei nostri repository)
trainer.train(dataset_path="our_functions.json")

# Ora il modello genera codice simile al nostro!
```

---

### 3. **Batching: Lavorare a Pezzi** 📦

**Perché:** La memoria RAM/GPU è limitata

**Analogia:** Devi lavare 1000 piatti:
- ❌ Non puoi lavarli tutti insieme (lavandino pieno!)
- ✅ Li lavi a gruppi di 10 (batch)

```python
# Nel progetto:
BATCH_SIZE = 100

all_functions = []
for file in code_files:
    functions = extract_functions(file)
    all_functions.extend(functions)
    
    # Ogni 100 funzioni, salva e svuota
    if len(all_functions) >= BATCH_SIZE:
        save_to_cloud(all_functions)
        all_functions = []  # Svuota per il prossimo batch
```

---

### 4. **Environment Variables: Configurazione Sicura** 🔐

**Cos'è:** Variabili segrete salvate FUORI dal codice

**Perché:** Password e API keys NON devono stare nel codice!

```python
# ❌ MALE - Password visibile a tutti
password = "mypassword123"
s3.connect(password="mypassword123")

# ✅ BENE - Password in file .env (non committato su git)
# File: .env
# DO_SECRET_ACCESS_KEY=mypassword123

# Codice Python:
import os
password = os.getenv("DO_SECRET_ACCESS_KEY")
s3.connect(password=password)
```

**Nel progetto:** Tutte le credenziali sono in `config/.env.common`

---

### 5. **Async/Threading: Parallelizzazione** ⚡

**Analogia:** Cucinare la pasta:
- ❌ Sequenziale: Metti acqua → ASPETTI che bolle → Aggiungi pasta → ASPETTI
- ✅ Parallelo: Metti acqua → Mentre bolle, prepari il sugo → Tutto pronto prima!

```python
# Sequenziale (LENTO - 10 secondi x 10 repo = 100 secondi)
for repo in repositories:
    download_and_process(repo)  # 10 secondi ciascuno

# Parallelo (VELOCE - 10 repo in parallelo = 10 secondi totali)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(download_and_process, repositories)
```

**Nel progetto:** `github_repo_processor.py` usa questo per processare repository in parallelo

---

## 🔄 FLUSSO DI ESECUZIONE

### FASE 1: Data Collection (`--collect-data`)

```
1. UTENTE ESEGUE COMANDO
   $ python main.py --collect-data --language python --count 20
   
2. MAIN.PY CHIAMA collect_data_from_repos()
   ├─ Legge argomenti (language=python, count=20)
   └─ Crea GitHubRepoProcessor
   
3. GITHUBREPOPROCESSOR.GET_POPULAR_REPOS()
   ├─ Cerca repository Python popolari
   └─ Trova: ['psf/requests', 'django/django', ...]
   
4. PER OGNI REPOSITORY:
   
   4.1 CLONE_REPOSITORY()
       ├─ git clone --depth 1 https://github.com/psf/requests
       └─ Salva in /tmp/repos_xyz/psf_requests/
   
   4.2 FIND_CODE_FILES()
       ├─ Scansiona directory
       ├─ Trova tutti i .py
       └─ Esclude: __pycache__, tests, .git
       
   4.3 EXTRACT_FUNCTIONS_FROM_FILE()
       ├─ UniversalParser.parse(file_content, 'python')
       ├─ Tree-sitter trova tutte le funzioni
       └─ Per ogni funzione:
           ├─ Nome: get_auth_token
           ├─ Parametri: (self, username, password)
           ├─ Docstring: "Retrieves authentication token..."
           └─ Body: (codice completo della funzione)
   
   4.4 QUALITY_FILTER.IS_VALID_CODE()
       ├─ Controlla sintassi valida
       ├─ Esclude boilerplate (pass, raise NotImplemented)
       ├─ Verifica lunghezza minima
       └─ Se OK → Aggiunge al batch
   
   4.5 DUPLICATE_MANAGER.IS_DUPLICATE()
       ├─ Calcola hash MD5 del codice
       ├─ Controlla se già visto
       └─ Se nuovo → Aggiunge alla lista
   
   4.6 SAVE_DATASET_BATCH() (ogni 100 funzioni)
       ├─ Formatta in JSON:
       │   {
       │     "task_type": "code_generation",
       │     "language": "python",
       │     "func_name": "get_auth_token",
       │     "input": "Write a function named get_auth_token",
       │     "output": "def get_auth_token(self, ...):\n    ...",
       │     "signature": "def get_auth_token(self, username, password)",
       │     "doc": "Retrieves authentication token...",
       │     "repo_url": "https://github.com/psf/requests",
       │     "file_path": "requests/auth.py",
       │     "extracted_at": "2025-11-03T10:30:45"
       │   }
       ├─ Upload a cloud storage (DigitalOcean Spaces)
       │   └─ Path: dataset_storage/requests_20251103_100.json
       └─ Retry 3 volte se fallisce
   
   4.7 AUTO_CLEANUP()
       └─ Elimina repository clonato (libera spazio)

5. STATISTICHE FINALI
   Processed: 20 repositories
   Files: 458
   Functions extracted: 3,247
   Upload success: ✅
   Duration: 125 seconds
```

---

### FASE 2: Training (`--train code_generation`)

```
1. UTENTE ESEGUE COMANDO
   $ python main.py --train code_generation
   
2. MAIN.PY CHIAMA train()
   ├─ Verifica dataset esiste
   └─ Se non esiste:
       ├─ AUTO_DOWNLOAD_DATASETS=true?
       │   ├─ YES → storage_manager.download_datasets()
       │   └─ NO → Errore: "Dataset not found"
       
3. CREA MODEL_MANAGER
   ├─ Carica modello: Salesforce/codegen-350M-mono
   ├─ Carica tokenizer (converte testo → numeri per AI)
   └─ Sposta su GPU se disponibile
   
4. CREA ADVANCEDTRAINER
   └─ Setup per training con GPU + mixed precision
   
5. TRAINER.TRAIN()
   
   5.1 LOAD_DATASET()
       ├─ Valida JSON format
       ├─ load_dataset("json", files="requests_20251103_100.json")
       └─ Carica in memoria: 3,247 esempi
   
   5.2 TOKENIZE_EXAMPLE()
       Per ogni esempio:
       ├─ Input:  "Write a function named get_auth_token"
       ├─ Output: "def get_auth_token(self, username, password):\n    ..."
       └─ Tokenizza (converte in numeri):
           Input tokens:  [123, 456, 789, ...]
           Output tokens: [321, 654, 987, ...]
   
   5.3 SPLIT TRAIN/VAL (80/20)
       ├─ Training set: 2,598 esempi
       └─ Validation set: 649 esempi
   
   5.4 CREATE DATALOADERS
       ├─ Batch size: 4 (processa 4 esempi alla volta)
       └─ Shuffle training (mischia ordine)
   
   5.5 SETUP OPTIMIZER (AdamW)
       └─ Learning rate: 5e-5 (quanto cambiare pesi ad ogni step)
   
   5.6 TRAINING LOOP (per ogni epoca)
       
       Per batch in training_set:
           
           6.1 FORWARD PASS
               ├─ Passa dati al modello
               └─ Modello genera output
           
           6.2 CALCOLA LOSS (errore)
               ├─ Compara output modello vs output vero
               └─ Loss: quanto è sbagliato (vogliamo minimizzare)
           
           6.3 BACKWARD PASS
               ├─ Calcola gradient (direzione per migliorare)
               └─ Backpropagation (aggiorna pesi del modello)
           
           6.4 OPTIMIZER STEP
               └─ Applica cambiamenti ai pesi
       
       Dopo ogni epoca:
       
       6.5 VALIDATION
           ├─ Testa su validation set (dati mai visti)
           ├─ Calcola validation loss
           └─ Se migliorato:
               ├─ Verifica spazio disco (>5GB liberi)
               └─ Salva modello: models/code_generation/
       
       6.6 EARLY STOPPING
           └─ Se validation non migliora per 3 epoche → STOP
   
   5.7 TRAINING COMPLETATO
       ├─ Salva modello finale
       ├─ Log statistiche
       └─ Se AUTO_BACKUP → Upload a cloud

7. OUTPUT
   Epoch 1: train_loss=2.345 | val_loss=2.123
   Epoch 2: train_loss=1.987 | val_loss=1.856 ✅ Best model saved
   Epoch 3: train_loss=1.654 | val_loss=1.892
   Epoch 4: train_loss=1.432 | val_loss=1.915
   🛑 Early stopping activated
   ✅ Training completed!
   Model saved to: models/code_generation/
```

---

## 📁 FILE PER FILE (Analisi Dettagliata)

### 1. `main.py` - Il Direttore d'Orchestra

**Cosa fa:** Gestisce tutti i comandi dell'utente

```python
def main():
    """
    Funzione principale che processa i comandi CLI
    
    Flow:
    1. Parse argomenti (argparse)
    2. Chiama funzione appropriata basata su comando
    3. Gestisce errori globali
    """
    parser = argparse.ArgumentParser()
    
    # Define tutti i comandi possibili
    parser.add_argument('--collect-data', action='store_true')
    parser.add_argument('--train', type=str)
    # ... altri comandi
    
    args = parser.parse_args()
    
    # Router: quale comando è stato chiamato?
    if args.collect_data:
        collect_data_from_repos(...)
    elif args.train:
        train(...)
    # ... ecc.
```

**Funzioni chiave:**
- `collect_data_from_repos()` → Raccolta dati da GitHub
- `bulk_process()` → Elaborazione massiva
- `train()` → Training modelli
- `validate_pipeline()` → Test completo sistema

---

### 2. `github_repo_processor.py` - Il Minatore di Codice

**Cosa fa:** Scarica repository e estrae funzioni

**Componenti:**

#### A. `__init__()` - Inizializzazione
```python
def __init__(self, cloud_save=True, batch_size=100):
    """
    Prepara il processor per lavorare
    
    Args:
        cloud_save: Se True, carica dati su cloud
        batch_size: Quante funzioni salvare insieme
    
    Crea:
        - StorageManager (per cloud)
        - UniversalParser (per estrarre funzioni)
        - DuplicateManager (per evitare duplicati)
        - QualityFilter (per filtrare codice brutto)
        - AutoCleanup (per pulire repo temporanei)
    """
    self.storage = StorageManager() if cloud_save else None
    self.parser = UniversalParser()
    self.duplicate_manager = DuplicateManager()
    # ...
```

#### B. `clone_repository()` - Scarica Repository
```python
def clone_repository(self, repo_url):
    """
    Clona repository da GitHub in directory temporanea
    
    Args:
        repo_url: URL repository (es. https://github.com/psf/requests)
    
    Returns:
        Path locale dove è stato clonato
    
    Steps:
        1. Crea path temporaneo (/tmp/repos_xyz/psf_requests)
        2. Prepara comando git con autenticazione
        3. Esegue: git clone --depth 1 <url> <path>
        4. Verifica successo
        5. Ritorna path locale
    
    Note:
        --depth 1 → Scarica solo ultimo commit (più veloce!)
        Token GitHub passato via env vars (sicuro)
    """
    # Crea path locale
    local_path = os.path.join(self.temp_dir, repo_name)
    
    # Setup autenticazione sicura
    env = os.environ.copy()
    env['GIT_PASSWORD'] = github_token
    
    # Clone
    subprocess.run(['git', 'clone', '--depth', '1', repo_url, local_path], env=env)
    
    return local_path
```

#### C. `extract_functions_from_file()` - Estrae Funzioni
```python
def extract_functions_from_file(self, file_path):
    """
    Estrae tutte le funzioni da un file di codice
    
    Args:
        file_path: Path al file .py, .js, etc.
    
    Returns:
        Lista di dizionari, uno per funzione:
        [{
            'name': 'calculate_sum',
            'signature': 'def calculate_sum(a, b)',
            'body': '    return a + b',
            'doc': 'Somma due numeri',
            'language': 'python',
            'file_path': 'src/math.py',
            'hash': 'abc123...',
            'extracted_at': '2025-11-03T10:30:45'
        }]
    
    Steps:
        1. Legge contenuto file
        2. Rileva linguaggio da estensione (.py → python)
        3. Chiama parser universale
        4. Aggiunge metadata (file_path, hash, timestamp)
        5. Ritorna lista funzioni
    
    Error handling:
        - File non leggibile → Ritorna []
        - Linguaggio non supportato → Ritorna []
        - Errore parsing → Log e ritorna []
    """
    # Legge file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Rileva linguaggio
    ext = Path(file_path).suffix  # .py
    language = self.FILE_EXTENSIONS.get(ext)  # python
    
    # Parse
    functions = self.parser.extract_all_functions(content, language)
    
    # Aggiungi metadata
    for func in functions:
        func['file_path'] = file_path
        func['hash'] = hashlib.md5(func['body'].encode()).hexdigest()
        func['extracted_at'] = datetime.now().isoformat()
    
    return functions
```

#### D. `process_repository()` - Pipeline Completa
```python
def process_repository(self, repo_url):
    """
    Processa repository completo: clone → extract → filter → save
    
    Args:
        repo_url: URL repository GitHub
    
    Returns:
        Dizionario con statistiche:
        {
            'repo_url': 'https://github.com/psf/requests',
            'files_processed': 45,
            'functions_extracted': 287,
            'duration': 34.5,
            'status': 'success'
        }
    
    Pipeline:
        1. Clone repository
        2. Find all code files
        3. For each file:
           a. Extract functions
           b. Filter quality (QualityFilter)
           c. Check duplicates (DuplicateManager)
           d. Add to batch
        4. Save batches to cloud
        5. Cleanup (delete repo)
        6. Return stats
    
    Error handling:
        - Clone fails → status='clone_failed'
        - Processing error → status='error'
        - Always cleanup repo (finally block)
    """
    local_path = self.clone_repository(repo_url)
    code_files = self.find_code_files(local_path)
    
    all_functions = []
    for file in code_files:
        functions = self.extract_functions_from_file(file)
        
        # Filter
        for func in functions:
            if not self.quality_filter.is_valid_code(func['output']):
                continue  # Skip low quality
            
            if self.duplicate_manager.is_duplicate(func['hash']):
                continue  # Skip duplicate
            
            all_functions.append(func)
            
            # Save batch quando raggiunto batch_size
            if len(all_functions) >= self.batch_size:
                self.save_dataset_batch(all_functions, repo_url)
                all_functions = []
    
    # Save remaining
    if all_functions:
        self.save_dataset_batch(all_functions, repo_url)
    
    # Cleanup
    shutil.rmtree(local_path)
    
    return stats
```

---

### 3. `module/preprocessing/universal_parser_new.py` - Il Traduttore Universale

**Cosa fa:** Capisce codice in 7 linguaggi diversi

**Perché serve:** Ogni linguaggio ha sintassi diversa!

```python
# Python
def calculate_sum(a, b):
    return a + b

# JavaScript
function calculateSum(a, b) {
    return a + b;
}

# Java
public int calculateSum(int a, int b) {
    return a + b;
}
```

Il parser capisce TUTTI questi formati!

**Come funziona:**

```python
class UniversalParser:
    """
    Parser che supporta 7 linguaggi di programmazione
    
    Linguaggi supportati:
        - Python
        - JavaScript (+ TypeScript)
        - Java
        - C/C++
        - Go
        - Ruby
        - Rust
    
    Usa tree-sitter per parsing AST (Abstract Syntax Tree)
    """
    
    def __init__(self):
        """
        Inizializza parser per tutti i linguaggi
        
        Tree-sitter richiede:
        1. Parser binario (.so/.dll) per ogni linguaggio
        2. Language() object che wrappa il parser
        
        Se un parser manca, logga warning ma continua
        """
        self.parsers = {}
        
        # Per ogni linguaggio, carica parser
        for lang in ['python', 'javascript', 'java', ...]:
            try:
                # Language.build_library compila parser se necessario
                Language.build_library(f'build/{lang}.so', [f'vendor/tree-sitter-{lang}'])
                
                # Carica language
                self.parsers[lang] = Language(f'build/{lang}.so', lang)
                
            except Exception as e:
                logger.warning(f"Parser {lang} not available: {e}")
    
    def parse(self, code: str, language: str) -> Dict:
        """
        Parse codice e ritorna dizionario standardizzato
        
        Args:
            code: Stringa con codice sorgente
            language: 'python', 'javascript', etc.
        
        Returns:
            {
                'task_type': 'code_generation',
                'language': 'python',
                'name': 'calculate_sum',
                'signature': 'def calculate_sum(a, b)',
                'body': '    return a + b',
                'doc': 'Somma due numeri',
                'input': 'Write a function named calculate_sum',
                'output': 'def calculate_sum(a, b):\n    return a + b'
            }
        
        Steps:
            1. Converti code in bytes
            2. Parser.parse() → AST tree
            3. Cerca nodi funzione nel tree
            4. Estrai nome, parametri, body, docstring
            5. Formatta output
            6. Ritorna dizionario
        """
        # Parse → AST
        tree = self.parsers[language].parse(bytes(code, 'utf8'))
        
        # Trova nodi funzione
        # In Python: function_definition
        # In JavaScript: function_declaration
        # In Java: method_declaration
        function_nodes = self._find_function_nodes(tree.root_node, language)
        
        results = []
        for node in function_nodes:
            # Estrai componenti
            name = self._extract_name(node, language)
            params = self._extract_parameters(node, language)
            body = self._extract_body(node, language)
            doc = self._extract_docstring(node, language)
            
            # Crea signature
            signature = self._build_signature(name, params, language)
            
            # Crea output completo (signature + body)
            output = self._format_output(signature, body, language)
            
            results.append({
                'task_type': 'code_generation',
                'language': language,
                'name': name,
                'signature': signature,
                'body': body,
                'doc': doc,
                'input': f"Write a {language} function named {name}",
                'output': output
            })
        
        return results
```

**Esempio pratico:**

```python
# INPUT: Codice Python
code = '''
def calculate_area(width, height):
    """Calculate rectangle area."""
    return width * height
'''

# PROCESSING
parser = UniversalParser()
result = parser.parse(code, 'python')

# OUTPUT: Dizionario standardizzato
{
    'task_type': 'code_generation',
    'language': 'python',
    'name': 'calculate_area',
    'signature': 'def calculate_area(width, height)',
    'body': '    return width * height',
    'doc': 'Calculate rectangle area.',
    'input': 'Write a python function named calculate_area',
    'output': 'def calculate_area(width, height):\n    """Calculate rectangle area."""\n    return width * height'
}
```

---

### 4. `module/model/training_model_advanced.py` - Il Maestro AI

**Cosa fa:** Addestra il modello AI

**Concetti chiave:**

#### A. Forward Pass - Predizione
```python
"""
Il modello riceve input e genera output

INPUT (tokenizzato):
"Write a function named calculate_sum" → [123, 456, 789]

MODEL (neural network):
[123, 456, 789] → [hidden layers] → [321, 654, 987]

OUTPUT (detokenizzato):
[321, 654, 987] → "def calculate_sum(a, b):\n    return a + b"
"""
```

#### B. Loss - Quanto è Sbagliato
```python
"""
Compara output modello vs output vero

OUTPUT VERO:
"def calculate_sum(a, b):\n    return a + b"

OUTPUT MODELLO:
"def calculate_sum(x, y):\n    return x + y"

LOSS:
- Stesso nome funzione ✅
- Parametri diversi (a,b vs x,y) ❌
- Body uguale ✅
→ Loss = 0.15 (basso = buono, alto = male)
"""
```

#### C. Backpropagation - Imparare dagli Errori
```python
"""
Aggiorna pesi del modello per ridurre loss

1. Calcola gradient (quale peso cambiare e quanto)
2. Applica cambiamento (optimizer step)
3. Ripeti per batch successivo

Dopo 1000 iterazioni:
Loss: 2.5 → 1.8 → 1.2 → 0.8 → 0.5
(il modello migliora!)
"""
```

**Codice semplificato:**

```python
class AdvancedTrainer:
    """
    Trainer per modelli di generazione codice
    
    Features:
        - Mixed Precision (fp16) per velocità
        - Gradient Accumulation per batch grandi
        - Early Stopping per evitare overfitting
        - Checkpoint automatici del miglior modello
    """
    
    def train(self, dataset_path, num_epochs=4, batch_size=4):
        """
        Training loop principale
        
        Args:
            dataset_path: Path al file JSON con esempi
            num_epochs: Quante volte vedere tutto il dataset
            batch_size: Quanti esempi per batch
        
        Steps:
            1. Load e validate dataset
            2. Tokenize (testo → numeri)
            3. Split train/validation (80/20)
            4. Training loop
            5. Validation dopo ogni epoca
            6. Save best model
        """
        # 1. Load dataset
        dataset = load_dataset("json", data_files=dataset_path)
        
        # 2. Tokenize
        dataset = dataset.map(self.tokenize_example)
        # Esempio:
        # Input: "Write a function..." → [123, 456, 789]
        # Output: "def func()..." → [321, 654, 987]
        
        # 3. Split
        dataset = dataset.train_test_split(test_size=0.2)
        train_dataset = dataset['train']  # 80%
        val_dataset = dataset['test']     # 20%
        
        # 4. Training loop
        for epoch in range(num_epochs):
            # Train on batches
            for batch in train_loader:
                # Forward pass
                outputs = self.model(**batch)
                loss = outputs.loss
                
                # Backward pass
                loss.backward()  # Calcola gradient
                optimizer.step()  # Applica cambiamenti
                optimizer.zero_grad()  # Reset gradient
            
            # 5. Validation
            val_loss = self.validate(val_loader)
            
            # 6. Save if improved
            if val_loss < best_val_loss:
                self.model.save_pretrained(output_dir)
                print(f"✅ Best model saved! val_loss={val_loss:.4f}")
    
    def tokenize_example(self, example):
        """
        Converti testo in numeri per il modello
        
        Args:
            example: Dict con 'input' e 'output'
        
        Returns:
            Dict con 'input_ids', 'attention_mask', 'labels'
        
        Tokenizer mapping:
            "Write" → 123
            "a" → 456
            "function" → 789
            "def" → 321
            ...
        
        Il modello capisce solo numeri!
        """
        # Tokenize input
        inputs = self.tokenizer(
            example['input'],
            max_length=256,
            truncation=True,
            padding='max_length'
        )
        
        # Tokenize output (labels per training)
        labels = self.tokenizer(
            example['output'],
            max_length=256,
            truncation=True,
            padding='max_length'
        )
        
        return {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
            'labels': labels['input_ids']
        }
```

---

### 5. `module/storage/storage_manager.py` - Il Guardiano del Cloud

**Cosa fa:** Gestisce upload/download da cloud storage

**Provider supportati:**
- DigitalOcean Spaces
- AWS S3
- Backblaze B2
- Wasabi
- Cloudflare R2

```python
class StorageManager:
    """
    Manager unificato per cloud storage
    
    Funzionalità:
        - Upload files/directory
        - Download files/directory
        - Sync (upload solo nuovi)
        - Validazione integrità
        - Retry automatici (3 tentativi)
    
    Setup:
        1. Configura .env con credenziali
        2. storage = StorageManager()
        3. storage.connect()
        4. storage.upload_datasets()
    """
    
    def __init__(self, config=None):
        """
        Inizializza storage manager
        
        Args:
            config: Dict con configurazione (opzionale)
                    Se None, carica da environment variables
        
        Load da .env:
            STORAGE_PROVIDER=digitalocean
            DO_BUCKET_NAME=my-bucket
            DO_ACCESS_KEY_ID=xxx
            DO_SECRET_ACCESS_KEY=yyy
        """
        self.config = config or self._load_config_from_env()
        self.provider = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connetti al provider cloud
        
        Returns:
            True se connessione riuscita
        
        Steps:
            1. Legge provider type (digitalocean, aws, etc.)
            2. Carica credenziali specifiche
            3. Crea provider object
            4. Testa connessione (list_files)
            5. Se OK → self.connected = True
        """
        provider_type = self.config['provider_type']
        credentials = self.config[provider_type]
        
        # Crea provider
        self.provider = create_provider(provider_type, credentials)
        
        # Test connection
        try:
            self.provider.list_files(prefix='', max_results=1)
            self.connected = True
            logger.info(f"✅ Connected to {provider_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def upload_datasets(self, force=False) -> Dict:
        """
        Upload datasets da disco locale a cloud
        
        Args:
            force: Se True, carica tutto. Se False, solo nuovi
        
        Returns:
            {
                'uploaded': 15,
                'skipped': 3,
                'failed': 0
            }
        
        Steps:
            1. Scansiona local_dataset_dir
            2. Per ogni file:
               - Se force=False, controlla se già esiste su cloud
               - Se nuovo o force=True, upload
               - Retry 3 volte se fallisce
            3. Ritorna statistiche
        """
        if not self.connected:
            logger.error("Not connected to cloud")
            return {'uploaded': 0, 'failed': 1}
        
        stats = {'uploaded': 0, 'skipped': 0, 'failed': 0}
        
        # Trova tutti i file
        local_files = list(Path(self.local_dataset_dir).rglob('*.json'))
        
        for file_path in local_files:
            # Path relativo
            relative_path = file_path.relative_to(self.local_dataset_dir)
            remote_path = f"{self.remote_dataset_prefix}/{relative_path}"
            
            # Check se esiste
            if not force and self.provider.file_exists(remote_path):
                stats['skipped'] += 1
                continue
            
            # Upload con retry
            for attempt in range(3):
                try:
                    success = self.provider.upload_file(file_path, remote_path)
                    if success:
                        stats['uploaded'] += 1
                        break
                except Exception as e:
                    if attempt == 2:  # Ultimo tentativo
                        logger.error(f"Upload failed: {file_path}")
                        stats['failed'] += 1
        
        return stats
    
    def download_datasets(self, force=False) -> Dict:
        """
        Download datasets da cloud a disco locale
        
        Args:
            force: Se True, scarica tutto. Se False, solo nuovi
        
        Returns:
            {
                'downloaded': 12,
                'skipped': 5,
                'failed': 0
            }
        
        Steps:
            1. Lista file su cloud (prefix=dataset_storage)
            2. Per ogni file:
               - Se force=False, controlla se già esiste locale
               - Se nuovo o force=True, download
               - Valida integrità (JSON format)
               - Retry 3 volte se fallisce
            3. Ritorna statistiche
        """
        if not self.connected:
            return {'downloaded': 0, 'failed': 1}
        
        stats = {'downloaded': 0, 'skipped': 0, 'failed': 0}
        
        # Lista file cloud
        remote_files = self.provider.list_files(prefix=self.remote_dataset_prefix)
        
        for remote_path in remote_files:
            # Path locale
            relative_path = remote_path.replace(f"{self.remote_dataset_prefix}/", "")
            local_path = Path(self.local_dataset_dir) / relative_path
            
            # Check se esiste
            if not force and local_path.exists():
                stats['skipped'] += 1
                continue
            
            # Download
            local_path.parent.mkdir(parents=True, exist_ok=True)
            success = self.provider.download_file(remote_path, local_path)
            
            if success:
                # Valida integrità
                if self._validate_downloaded_file(local_path):
                    stats['downloaded'] += 1
                else:
                    stats['failed'] += 1
                    local_path.unlink()  # Elimina file corrotto
        
        return stats
    
    def _validate_downloaded_file(self, file_path) -> bool:
        """
        Valida che file scaricato sia integro
        
        Args:
            file_path: Path al file
        
        Returns:
            True se valido
        
        Checks:
            - File esiste
            - File non vuoto
            - Per JSON: formato valido
            - Per binari: checksum (TODO)
        """
        # Esiste?
        if not file_path.exists():
            return False
        
        # Vuoto?
        if file_path.stat().st_size == 0:
            logger.warning(f"Empty file: {file_path}")
            return False
        
        # JSON valido?
        if file_path.suffix in ['.json', '.jsonl']:
            try:
                with open(file_path) as f:
                    json.load(f)  # Prova a parsare
                return True
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON: {file_path}")
                return False
        
        return True  # Altri formati: assume OK
```

---

## 🎓 CONCETTI AVANZATI

### 1. **Abstract Syntax Tree (AST)** 🌳

**Cos'è:** Rappresentazione strutturata del codice

**Analogia:** Una frase italiana:
```
"Il gatto mangia il topo"

AST (struttura grammaticale):
Frase
├── Soggetto: "Il gatto"
├── Verbo: "mangia"
└── Complemento: "il topo"
```

**Nel codice:**
```python
def calculate_sum(a, b):
    return a + b

AST:
function_definition
├── name: "calculate_sum"
├── parameters
│   ├── identifier: "a"
│   └── identifier: "b"
└── body
    └── return_statement
        └── binary_expression
            ├── left: identifier "a"
            ├── operator: "+"
            └── right: identifier "b"
```

**Perché serve:** Tree-sitter crea l'AST, noi lo attraversiamo per estrarre pezzi

---

### 2. **Tokenization** 🔢

**Cos'è:** Convertire testo in numeri

**Perché:** Le reti neurali capiscono solo numeri!

```python
# Vocabolario del tokenizer
vocab = {
    "def": 1,
    "function": 2,
    "return": 3,
    "a": 4,
    "+": 5,
    "b": 6,
    ...
}

# Testo
code = "def function(a, b):\n    return a + b"

# Tokenizzato
tokens = [1, 2, 4, 6, 3, 4, 5, 6]

# Il modello vede solo i numeri!
```

**Max Length:** 256 tokens in questo progetto
- Se più lungo → truncation (taglia)
- Se più corto → padding (riempie con zeri)

---

### 3. **Batch Processing** 📦

**Perché batching:**
- GPU ha memoria limitata
- Elaborare 1 esempio alla volta = LENTO
- Elaborare tutti insieme = OOM (Out of Memory)
- **Soluzione: Batch di 4-16 esempi**

```python
# Esempio: 1000 funzioni, batch_size=100

Batch 1: funzioni 0-99    → Process → Save
Batch 2: funzioni 100-199 → Process → Save
Batch 3: funzioni 200-299 → Process → Save
...
Batch 10: funzioni 900-999 → Process → Save
```

**Vantaggi:**
- Memoria sotto controllo
- Progress visibile (batch 3/10)
- Errore in batch 5 → Batch 1-4 già salvati!

---

### 4. **Mixed Precision (FP16)** ⚡

**Cos'è:** Usare numeri a 16 bit invece di 32

**Normale (FP32):**
```python
weight = 0.123456789  # 32 bit
```

**Mixed Precision (FP16):**
```python
weight = 0.1235  # 16 bit (meno preciso ma più veloce)
```

**Vantaggi:**
- 2x velocità
- 2x meno memoria
- Stessa accuratezza (per training)

**Nel progetto:**
```python
# Automatico con PyTorch AMP
with torch.autocast(device_type="cuda"):
    outputs = model(**batch)  # Usa FP16 automaticamente
```

---

### 5. **Gradient Accumulation** 🔄

**Problema:** Vogliamo batch_size=64 ma GPU supporta solo 4

**Soluzione:** Accumula gradient per 16 step (4×16=64)

```python
# Invece di:
batch_size = 64  # OOM!
loss.backward()
optimizer.step()

# Facciamo:
accumulation_steps = 16
for i, batch in enumerate(train_loader):
    loss = model(batch) / accumulation_steps
    loss.backward()  # Accumula gradient
    
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()  # Applica dopo 16 batch
        optimizer.zero_grad()  # Reset
```

**Risultato:** Simula batch_size=64 con memoria per 4!

---

### 6. **Early Stopping** 🛑

**Problema:** Modello potrebbe overfittare (memorizza training, non generalizza)

**Soluzione:** Ferma training quando validation loss smette di migliorare

```python
best_val_loss = float('inf')
patience = 3  # Quante epoche senza miglioramento
patience_counter = 0

for epoch in range(100):
    train_loss = train()
    val_loss = validate()
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        save_model()  # Salva miglior modello
    else:
        patience_counter += 1
        
    if patience_counter >= patience:
        print("🛑 Early stopping!")
        break

# Training si ferma automaticamente quando non migliora più
```

---

## 🔨 PATTERN E BEST PRACTICES

### 1. **Dependency Injection**

**Invece di:**
```python
class Trainer:
    def __init__(self):
        self.storage = StorageManager()  # Hardcoded!
```

**Meglio:**
```python
class Trainer:
    def __init__(self, storage=None):
        self.storage = storage or StorageManager()  # Iniettabile!

# Test:
fake_storage = MockStorage()
trainer = Trainer(storage=fake_storage)  # Test senza cloud reale
```

---

### 2. **Try-Except con Logging**

**Sempre:**
```python
try:
    result = dangerous_operation()
except SpecificError as e:
    logger.error(f"Failed: {e}", exc_info=True)
    # exc_info=True salva stack trace completo
```

**Mai:**
```python
try:
    result = dangerous_operation()
except:  # ❌ Cattura tutto, anche Ctrl+C!
    pass  # ❌ Silenzioso, impossibile debuggare
```

---

### 3. **Context Managers**

**Per file:**
```python
# ✅ Chiude file automaticamente
with open('file.txt', 'r') as f:
    data = f.read()
# File chiuso qui

# ❌ Devi ricordare di chiudere
f = open('file.txt', 'r')
data = f.read()
f.close()  # Se dimentichi → memory leak!
```

**Per database/connessioni:**
```python
with connection.cursor() as cursor:
    cursor.execute("SELECT...")
# Connessione chiusa automaticamente
```

---

### 4. **Logging Levels**

```python
logger.debug("Step 1: Loading data")     # Solo per debug
logger.info("Processing 1000 files")     # Info generale
logger.warning("Disk space low: 5GB")    # Attenzione
logger.error("Failed to save model")     # Errore recuperabile
logger.critical("Out of memory!")        # Errore fatale
```

**Quando usare:**
- DEBUG: Dettagli interni, step-by-step
- INFO: Progress normale, successi
- WARNING: Problemi non bloccanti
- ERROR: Fallimenti recuperabili
- CRITICAL: Sistema non può continuare

---

### 5. **Type Hints**

```python
# ✅ Con type hints (chiaro cosa aspettarsi)
def process_file(file_path: str, max_size: int = 1000) -> List[Dict]:
    ...

# ❌ Senza type hints (devi indovinare)
def process_file(file_path, max_size=1000):
    ...
```

**Benefici:**
- Editor mostra errori prima di eseguire
- Documentazione automatica
- Refactoring più sicuro

---

## 🐛 DEBUGGING E TROUBLESHOOTING

### Errori Comuni e Soluzioni

#### 1. **"CUDA out of memory"**

**Causa:** Batch size troppo grande per GPU

**Soluzione:**
```python
# Riduci batch size
batch_size = 4  # Invece di 16

# O usa gradient accumulation
accumulation_steps = 4  # Simula batch_size=16
```

---

#### 2. **"No module named 'tree_sitter_python'"**

**Causa:** Parser tree-sitter non installato

**Soluzione:**
```bash
pip install tree-sitter-python
pip install tree-sitter-javascript
# ... per ogni linguaggio
```

---

#### 3. **"Dataset not found"**

**Causa:** File non scaricato da cloud

**Soluzione:**
```bash
# Download manuale
python main.py --sync download

# O abilita auto-download
# .env:
AUTO_DOWNLOAD_DATASETS=true
```

---

#### 4. **"Connection refused" (cloud storage)**

**Causa:** Credenziali sbagliate o network issue

**Debugging:**
```bash
# Test connessione
python main.py --test-connection

# Verifica .env
cat config/.env.common | grep DO_

# Test manuale con boto3
python -c "import boto3; s3 = boto3.client('s3', ...); print(s3.list_buckets())"
```

---

### Come Debuggare

**1. Usa logging invece di print:**
```python
# ❌ Print sparisce
print(f"Processing {file}")

# ✅ Logger salva su file
logger.debug(f"Processing {file}")
```

**2. Aggiungi breakpoint:**
```python
import pdb

def problematic_function():
    data = load_data()
    pdb.set_trace()  # ← Ferma esecuzione qui
    # Puoi ispezionare variabili, step attraverso codice
    result = process(data)
    return result
```

**3. Usa try-except con traceback:**
```python
import traceback

try:
    risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    logger.error(traceback.format_exc())  # Stack trace completo
```

**4. Valida input:**
```python
def process_data(data):
    # Assumi niente!
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) > 0, "Empty data list"
    assert all('name' in item for item in data), "Missing 'name' field"
    
    # Ora sei sicuro che data è valido
    ...
```

---

## 🎓 RISORSE PER APPROFONDIRE

### Documentazione Ufficiale:
- **PyTorch:** https://pytorch.org/tutorials/
- **HuggingFace:** https://huggingface.co/docs/transformers/
- **Tree-sitter:** https://tree-sitter.github.io/tree-sitter/

### Tutorial Consigliati:
- **Deep Learning:** Fast.ai (https://course.fast.ai/)
- **NLP:** CS224n Stanford
- **Transformers:** Illustrated Transformer (Jay Alammar)

### Libri:
- "Deep Learning" - Ian Goodfellow
- "Natural Language Processing with Transformers" - O'Reilly
- "Python Machine Learning" - Sebastian Raschka

---

## 📞 SUPPORTO

**Ho un bug!**
1. Controlla logs: `tail -f ml_system.log`
2. Cerca errore in questo documento
3. Prova soluzioni suggerite
4. Se persiste: apri issue su GitHub

**Voglio contribuire!**
1. Leggi CONTRIBUTING.md
2. Fork repository
3. Crea branch: `feature/my-improvement`
4. Pull request con descrizione chiara

**Domande?**
- GitHub Discussions
- Stack Overflow (tag: machine-learning, pytorch)

---

**Autore:** ML Code Intelligence Project  
**Ultima Revisione:** Novembre 2025  
**Versione:** 1.0  
**Licenza:** MIT
