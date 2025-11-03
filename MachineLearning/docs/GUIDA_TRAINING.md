# 🚀 Guida Completa al Training

## 📋 Prerequisiti

### 1. Verifica Git
```bash
git --version
```

### 2. Verifica Python Environment
```bash
python --version  # Deve essere >= 3.8
```

### 3. Verifica Dipendenze
```bash
pip list | grep -E "(boto3|tree-sitter|datasets)"
```

Se mancanti:
```bash
pip install boto3 datasets tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-java
```

---

## 🔄 Processo di Training Completo

### FASE 1: Raccolta Dati

#### Opzione A: Repository Singolo
```bash
python github_repo_processor.py --repo https://github.com/user/repo
```

#### Opzione B: Lista di Repository
```bash
# Modifica repo_list.txt con i tuoi repository
python github_repo_processor.py --repos-file repo_list.txt --workers 4
```

#### Opzione C: Repository Popolari per Linguaggio
```bash
# Python
python github_repo_processor.py --language python --count 15

# JavaScript
python github_repo_processor.py --language javascript --count 10

# Java
python github_repo_processor.py --language java --count 10

# C++
python github_repo_processor.py --language cpp --count 5
```

**Output Atteso:**
```
Cloning https://github.com/tensorflow/tensorflow...
Found 1523 code files
Processing: 100%|████████| 1523/1523 [15:30<00:00]
Saved 4827 functions to cloud: datasets/code_generation/tensorflow_20251102_143022_4827.json

PROCESSING STATISTICS
==================================================
Repositories processed: 15
Files processed: 18,234
Functions extracted: 67,891
Duration: 3847.23 seconds
Functions/second: 17.65
==================================================
```

---

### FASE 2: Verifica Dataset

#### Verifica Cloud Storage
```bash
# Se hai configurato DigitalOcean Spaces
python -c "from module.storage.storage_manager import StorageManager; s = StorageManager(); s.connect(); print(s.list_files('datasets/code_generation'))"
```

#### Verifica Locale (Backup)
```bash
dir datasets\local_backup\code_generation\*.json
```

---

### FASE 3: Training

#### Training Code Generation
```bash
python main.py --train code_generation
```

**Output Atteso:**
```
📍 Device di training: cuda:0 (oppure cpu)
📚 Caricamento dataset da cloud storage...
✅ Scaricati 67,891 esempi

🚀 Inizio training...

Epoch 1/4
Training: 100%|████████| 4243/4243 [24:15<00:00]
Train Loss: 0.456 | Val Loss: 0.389 | Perplexity: 52.3

Epoch 2/4
Training: 100%|████████| 4243/4243 [23:58<00:00]
Train Loss: 0.234 | Val Loss: 0.198 | Perplexity: 21.8

💾 Nuovo miglior modello salvato!

Epoch 3/4
Training: 100%|████████| 4243/4243 [24:05<00:00]
Train Loss: 0.187 | Val Loss: 0.156 | Perplexity: 16.9

💾 Nuovo miglior modello salvato!

Epoch 4/4
Training: 100%|████████| 4243/4243 [24:12<00:00]
Train Loss: 0.145 | Val Loss: 0.134 | Perplexity: 14.3

💾 Nuovo miglior modello salvato!

✅ Training completato!
📊 Best Val Loss: 0.134
💾 Modello salvato in: models/saved/code_generation_best
☁️  Backup su cloud completato
```

#### Training Text Classification
```bash
python main.py --train text_classification
```

#### Training Security Classification
```bash
python main.py --train security_classification
```

---

### FASE 4: Validazione

```bash
python main.py --validate
```

**Output Atteso:**
```
🔍 Validazione modelli...

📦 Caricamento dataset di test...
✅ 5,000 esempi di test caricati

🧪 Testing code_generation model...
Inference: 100%|████████| 5000/5000 [03:24<00:00]
Accuracy: 87.3%
BLEU Score: 0.823
Exact Match: 34.2%

✅ Validazione completata!
📊 Report salvato in: reports/validation_20251102_153045.json
```

---

### FASE 5: Avvio UI

```bash
python main.py --ui
```

**Output:**
```
🚀 Avvio dell'interfaccia web...
ℹ️ L'interfaccia sarà disponibile su: http://localhost:8501

You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Apri http://localhost:8501 nel browser.

---

## 🔧 Risoluzione Problemi

### Problema: "No module named 'boto3'"
**Soluzione:**
```bash
pip install boto3
```

### Problema: "Failed to connect to cloud storage"
**Soluzione:**
Verifica configurazione in `.env`:
```env
STORAGE_PROVIDER=digitalocean
DO_BUCKET_NAME=mlcodedatasets
DO_ACCESS_KEY_ID=your_key
DO_SECRET_ACCESS_KEY=your_secret
DO_REGION=sfo3
```

### Problema: "Language 'python' not supported"
**Soluzione:**
```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-java
```

### Problema: "Git clone timeout"
**Soluzione:**
Aumenta il timeout nel codice o usa repository più piccoli.

### Problema: "CUDA out of memory"
**Soluzione:**
Riduci batch size in `.env`:
```env
DEFAULT_BATCH_SIZE=2  # invece di 4
```

---

## 📊 Monitoraggio Progress

### Log Files
```bash
# Vedi log bulk processing
type bulk_processing.log

# Vedi log training
type training.log
```

### Cloud Storage
Controlla il bucket per vedere i dataset salvati:
- `datasets/code_generation/` - Dataset processati
- `models/` - Modelli trainati

---

## 🎯 Best Practices

### 1. **Inizia con Repository Piccoli**
```bash
# Test con 1 repository
python github_repo_processor.py --repo https://github.com/psf/requests

# Se funziona, scala a lista
python github_repo_processor.py --repos-file repo_list.txt
```

### 2. **Usa Cloud Storage**
Configura sempre cloud storage per:
- Non perdere dati in caso di crash
- Condividere dataset tra macchine
- Backup automatico modelli

### 3. **Verifica Qualità Dataset**
Prima di trainare, controlla che i dataset siano validi:
```bash
python -c "import json; data = json.load(open('datasets/local_backup/code_generation/tensorflow_*.json')); print(f'Esempi: {len(data)}'); print(f'Sample: {data[0]}')"
```

### 4. **Training Incrementale**
Non rifare tutto da zero:
- I duplicati sono automaticamente evitati
- Puoi aggiungere repository e ritrainare

### 5. **Monitora GPU**
Se hai GPU:
```bash
nvidia-smi --loop=1
```

---

## 🔄 Workflow Completo (Esempio)

```bash
# 1. Raccogli dati Python
python github_repo_processor.py --language python --count 20

# 2. Verifica output
dir datasets\local_backup\code_generation\*.json

# 3. Training
python main.py --train code_generation

# 4. Validazione
python main.py --validate

# 5. Avvio UI
python main.py --ui

# 6. Testa nel browser
# Apri http://localhost:8501
# Input: "Scrivi una funzione per calcolare fibonacci"
# Output: Codice generato dal modello
```

---

## 📈 Performance Tips

### Training più veloce:
1. Usa GPU (se disponibile)
2. Aumenta batch size (se hai memoria)
3. Riduci num_epochs per test rapidi
4. Usa mixed precision training (automatico su GPU)

### Processamento più veloce:
1. Aumenta workers: `--workers 8`
2. Usa SSD per temp directory
3. Filtra repository troppo grandi
4. Usa connessione veloce

---

## 🎓 Prossimi Passi

Dopo il training base:
1. ✅ Fine-tuning su task specifici
2. ✅ Hyperparameter tuning
3. ✅ Ensemble di modelli
4. ✅ Deploy production
5. ✅ API REST per inferenza
6. ✅ Monitoring e metrics

---

## 💡 Tips Avanzati

### Bulk Processing Completo
```bash
# Processa TUTTO
python bulk_processor.py --all --workers 8
```

### Custom Repository List
Crea `my_repos.txt`:
```
https://github.com/django/django
https://github.com/fastapi/fastapi
https://github.com/flask/flask
```

Poi:
```bash
python github_repo_processor.py --repos-file my_repos.txt
```

### Training su Specifico Dataset
```bash
python main.py --train code_generation --dataset datasets/my_custom_dataset.json
```

---

**Buon Training! 🚀**
