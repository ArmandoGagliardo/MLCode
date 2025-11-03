# 🚀 Sistema ML Code Intelligence - Guida Rapida

## ✅ Aggiornamento Completato

Il sistema è stato completamente riorganizzato per utilizzare il nuovo approccio basato su:
- **GitHub Repository Processing** (`github_repo_processor.py`)
- **Bulk Processing** (`bulk_processor.py`)
- **Cloud Storage Integration**
- **Dati locali di grandi dimensioni**

### ❌ Rimosso (Obsoleto)
- `crawl_web()` - Web crawling generico
- `crawl_text()` - Text crawling
- `crawl_website()` - Website scraping specifico
- Vecchie funzioni di crawling non più necessarie

### ✅ Nuovo Sistema

Il file `main.py` ora orchestra tutto attraverso comandi semplici e chiari.

---

## 🎯 Workflow Completo

### 1. **Raccolta Dati**

#### Opzione A: Linguaggio Specifico
```bash
python main.py --collect-data --language python --count 20
```

#### Opzione B: Repository Singolo
```bash
python main.py --collect-data --repo https://github.com/tensorflow/tensorflow
```

#### Opzione C: Lista Repository
```bash
python main.py --collect-data --repos-file repo_list.txt --workers 4
```

#### Opzione D: Bulk Processing
```bash
python main.py --bulk-process --repos-file repo_list.txt --workers 8
```

#### 🛑 Stop Manuale (Graceful Shutdown)
Durante la raccolta dati, puoi interromperla in modo sicuro:
- **1° Ctrl+C**: Finisce il repository corrente e salva i dati
- **2° Ctrl+C**: Forza l'uscita immediata

```bash
# Avvia raccolta
python main.py --collect-data --repos-file repo_list.txt

# Durante l'esecuzione, premi Ctrl+C
# Log: "Stop requested, finishing current repository..."
# Il sistema completa il repo corrente e salva tutto
```

---

### 2. **Training**

```bash
# Training code generation
python main.py --train code_generation

# Training classification
python main.py --train text_classification

# Training security
python main.py --train security_classification
```

**Con dataset custom:**
```bash
python main.py --train code_generation --dataset datasets/my_dataset.json --model Salesforce/codegen-350M-mono
```

---

### 3. **Cloud Sync**

```bash
# Download datasets e modelli
python main.py --sync-cloud download

# Upload datasets e modelli
python main.py --sync-cloud upload
```

---

### 4. **Validazione e UI**

```bash
# Valida dataset
python main.py --validate

# Statistiche sistema
python main.py --stats

# Avvia UI web
python main.py --ui

# Pipeline interattiva
python main.py --pipeline
```

---

## 📊 Architettura Componenti

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                             │
│              (Orchestrator Principale)                   │
└───────────┬─────────────────────────────────────────────┘
            │
            ├─────► github_repo_processor.py
            │       ├── Clone repository
            │       ├── Extract functions
            │       ├── Quality filtering
            │       └── Save to cloud
            │
            ├─────► bulk_processor.py
            │       ├── Multi-source processing
            │       ├── Parallel workers
            │       └── Batch processing
            │
            ├─────► module/preprocessing/
            │       ├── universal_parser_new.py (7 languages)
            │       ├── code_quality_filter.py
            │       └── parser_manager.py
            │
            ├─────► module/utils/
            │       └── duplicate_manager.py
            │
            ├─────► module/model/
            │       ├── model_manager.py
            │       ├── advanced_trainer_classifier.py
            │       └── training_model_advanced.py
            │
            ├─────► module/storage/
            │       └── storage_manager.py
            │           ├── DigitalOcean Spaces
            │           ├── AWS S3
            │           ├── Backblaze B2
            │           ├── Wasabi
            │           └── Cloudflare R2
            │
            └─────► module/ui/
                    └── app.py (Streamlit)
```

---

## 🔧 Componenti Chiave

### **1. GitHub Repo Processor**
```bash
# Singolo repo
python github_repo_processor.py --repo https://github.com/psf/requests

# Lista repo
python github_repo_processor.py --repos-file repo_list.txt --workers 4

# Per linguaggio
python github_repo_processor.py --language python --count 15

# Senza cloud
python github_repo_processor.py --repo URL --no-cloud
```

### **2. Bulk Processor**
```bash
# Completo
python bulk_processor.py --source github --repos repo_list.txt

# HuggingFace
python bulk_processor.py --source huggingface --dataset codeparrot/github-code

# Locale
python bulk_processor.py --source local --directory /path/to/code
```

### **3. Universal Parser New**
- Supporta 7 linguaggi: Python, JavaScript, Java, C++, Go, Ruby, Rust
- Usa tree-sitter moderno (API 0.20+)
- Estrazione automatica funzioni e classi

### **4. Duplicate Manager**
- Hash-based deduplication
- Cache persistente
- Normalizzazione codice

### **5. Quality Filter**
- Validazione sintassi
- Filtraggio complessità
- Rimozione boilerplate
- Quality scoring (0.0-1.0)

---

## 📝 File di Configurazione

### `.env`
```env
# Storage
STORAGE_PROVIDER=digitalocean
DO_BUCKET_NAME=mlcodedatasets
DO_ACCESS_KEY_ID=your_key
DO_SECRET_ACCESS_KEY=your_secret

# Training
DEFAULT_BATCH_SIZE=4
DEFAULT_EPOCHS=4
DEFAULT_LEARNING_RATE=5e-5

# Automation
AUTO_SYNC_ON_STARTUP=true
AUTO_BACKUP_AFTER_TRAINING=true
```

### `repo_list.txt`
```
# Python ML
https://github.com/tensorflow/tensorflow
https://github.com/pytorch/pytorch
https://github.com/scikit-learn/scikit-learn

# Web Frameworks
https://github.com/django/django
https://github.com/fastapi/fastapi
https://github.com/flask/flask

# JavaScript
https://github.com/facebook/react
https://github.com/vuejs/vue
https://github.com/angular/angular
```

---

## 🎯 Workflow Esempio Completo

```bash
# 1. Verifica dipendenze
python main.py --check-deps

# 2. Raccogli dati Python
python main.py --collect-data --language python --count 20

# 3. Verifica statistiche
python main.py --stats

# 4. Training
python main.py --train code_generation

# 5. Valida
python main.py --validate

# 6. Avvia UI
python main.py --ui

# 7. Test nel browser
# Apri http://localhost:8501
# Input: "Scrivi una funzione per calcolare fibonacci"
# Output: Codice generato
```

---

## 🆕 Comandi Principali

### Data Collection
| Comando | Descrizione |
|---------|-------------|
| `--collect-data` | Raccoglie dati da GitHub |
| `--bulk-process` | Processing bulk di massa |
| `--language LANG` | Specifica linguaggio |
| `--count N` | Numero repository |
| `--repo URL` | Repository singolo |
| `--repos-file FILE` | Lista repository |
| `--workers N` | Worker paralleli |

### Training
| Comando | Descrizione |
|---------|-------------|
| `--train TASK` | Avvia training |
| `--dataset PATH` | Dataset custom |
| `--model NAME` | Modello custom |

### Cloud & Sync
| Comando | Descrizione |
|---------|-------------|
| `--sync-cloud download` | Scarica da cloud |
| `--sync-cloud upload` | Carica su cloud |

### UI & Tools
| Comando | Descrizione |
|---------|-------------|
| `--ui` | Interfaccia web |
| `--pipeline` | CLI interattiva |
| `--validate` | Valida dataset |
| `--stats` | Statistiche sistema |
| `--check-deps` | Verifica dipendenze |

---

## 💡 Tips

### Performance
- Usa `--workers 8` per processing più veloce
- Configura SSD per temp directory
- Usa GPU per training (automatico se disponibile)

### Storage
- Configura sempre cloud storage per backup automatico
- Usa `AUTO_BACKUP_AFTER_TRAINING=true` in `.env`
- Periodicamente: `python main.py --sync-cloud upload`

### Dataset Quality
- I duplicati sono automaticamente filtrati
- Il quality filter rimuove codice di bassa qualità
- Verifica con: `python main.py --stats`

---

## 🔄 Migration dal Vecchio Sistema

### Prima (Obsoleto)
```bash
python main.py --crawl-git
python main.py --crawl-web
python main.py --crawl-text
```

### Ora (Nuovo)
```bash
python main.py --collect-data --language python --count 20
python main.py --bulk-process --repos-file repo_list.txt
```

**Vantaggi:**
- ✅ Nessun rate limiting API
- ✅ Repository completi (non solo alcuni file)
- ✅ Multi-linguaggio (7 lingue)
- ✅ Cloud storage integrato
- ✅ Quality filtering automatico
- ✅ Deduplicazione automatica

---

## 📚 Documentazione Completa

- **GUIDA_TRAINING.md** - Guida dettagliata training
- **QUICK_START.md** - Quick start guide
- **README.md** - Panoramica generale

---

## ❓ Troubleshooting

### "No module named 'boto3'"
```bash
pip install boto3
```

### "Failed to connect to cloud storage"
Verifica `.env`:
```env
STORAGE_PROVIDER=digitalocean
DO_BUCKET_NAME=your_bucket
DO_ACCESS_KEY_ID=your_key
DO_SECRET_ACCESS_KEY=your_secret
```

### "Language 'python' not supported"
```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-java
```

### "Git clone timeout"
Riduci `--count` o usa repository più piccoli.

---

**Buon Lavoro! 🚀**
