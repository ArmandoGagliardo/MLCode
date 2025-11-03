# 🚀 GUIDA COMPLETA - Crawling → Training → Inference

Guida end-to-end per il workflow completo: raccolta dati, training modello, e inferenza.

---

## 📋 INDICE

1. [Setup Iniziale](#1-setup-iniziale)
2. [Fase 1: Crawling Repository](#2-fase-1-crawling-repository)
3. [Fase 2: Training Modello](#3-fase-2-training-modello)
4. [Fase 3: Inferenza](#4-fase-3-inferenza)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. SETUP INIZIALE

### 1.1 Installazione

```powershell
# Clone repository
git clone <your-repo-url>
cd MachineLearning

# Crea virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt
```

### 1.2 Configurazione Environment (.env)

```powershell
# Copia template
copy .env.example .env

# Modifica .env con i tuoi valori
notepad .env
```

**Variabili ESSENZIALI:**

```env
# GitHub Token (per repository privati e rate limit)
GITHUB_TOKEN=ghp_your_token_here

# Cloud Storage (scegli uno)
STORAGE_PROVIDER=digitalocean

# DigitalOcean Spaces
DO_SPACES_KEY=your_key
DO_SPACES_SECRET=your_secret
DO_SPACES_NAME=your-space-name
DO_SPACES_REGION=nyc3
```

**Come ottenere GitHub Token:**
1. Vai su https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Seleziona scopes: `repo` (o `public_repo` per solo pubblici)
4. Copia il token in `.env`

**Come ottenere DigitalOcean Spaces:**
1. Vai su https://cloud.digitalocean.com/spaces
2. Create Space (o usa esistente)
3. Vai su API → Spaces Keys
4. Generate New Key
5. Copia Key e Secret in `.env`

### 1.3 Verifica Setup

```powershell
# Test GitHub token
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GitHub Token:', 'OK' if os.getenv('GITHUB_TOKEN') else 'MISSING')"

# Test cloud storage
python debug/test_storage_quick.py
```

**Output atteso:**
```
✓ GITHUB_TOKEN trovato
✓ Storage provider configurato: digitalocean
✓ Connessione al cloud storage: OK
```

---

## 2. FASE 1: CRAWLING REPOSITORY

### 2.1 Crawling Singolo Repository

**Metodo più semplice per iniziare:**

```powershell
python main.py
```

Poi:
1. Scegli opzione `1` (Process GitHub Repository)
2. Inserisci URL: `https://github.com/psf/requests`
3. Aspetta l'estrazione

**Con script dedicato:**

```powershell
python example_single_repo.py
```

**Output:**
```
🔧 Inizializzazione processor...
✅ Parser caricati: 7 linguaggi

🔍 Clonando repository: https://github.com/psf/requests
✅ Repository clonato: 2.5 MB

📊 Trovati 21 file di codice
Processing: 100%|██████████| 21/21 [00:30<00:00]

✅ Estratte 225 funzioni
💾 Salvato: dataset_storage/local_backup/code_generation/requests_20251102_143022_225.json
☁️  Backup cloud: OK
```

**File salvato:**
- Locale: `dataset_storage/local_backup/code_generation/requests_*.json`
- Cloud: `s3://your-space/datasets/code_generation/requests_*.json`

### 2.2 Crawling Multipli Repository (Batch)

**Step 1: Crea lista repository**

```powershell
# Crea repo_list.txt
@"
https://github.com/psf/requests
https://github.com/axios/axios
https://github.com/spf13/cobra
https://github.com/clap-rs/clap
https://github.com/google/gson
"@ | Out-File -Encoding UTF8 repo_list.txt
```

**Step 2: Esegui batch processing**

```powershell
python example_bulk_processing.py
```

**Con opzioni avanzate:**

```powershell
# Solo Python
python bulk_processor.py --source github --repos repo_list.txt --language python

# Con 8 worker paralleli
python bulk_processor.py --source github --repos repo_list.txt --workers 8

# Batch size custom (funzioni per file)
python bulk_processor.py --source github --repos repo_list.txt --batch-size 200
```

**Output:**
```
📦 Repository da processare: 5
   1. https://github.com/psf/requests
   2. https://github.com/axios/axios
   3. https://github.com/spf13/cobra
   4. https://github.com/clap-rs/clap
   5. https://github.com/google/gson

🚀 INIZIO PROCESSING...
Processing repos: 100%|██████████| 5/5 [05:23<00:00]

✅ COMPLETATO!
   ⏱️  Tempo totale: 323.5 secondi
   📁 File creati: 5
   ✨ Funzioni estratte: 2,938
   ⚡ Velocità: 9.1 funzioni/secondo
```

### 2.3 Crawling da Directory Locale

```powershell
# Analizza codice sul tuo computer
python bulk_processor.py --source local --path "C:\MyProjects\AwesomeApp"
```

### 2.4 Verifica Dati Estratti

```powershell
# Analisi completa
python example_analyze_output.py
```

**Output:**
```
📊 STATISTICHE GENERALI
Totale funzioni: 2,938
Totale file JSON: 5
Dimensione totale: 2.45 MB

📈 STATISTICHE PER LINGUAGGIO
javascript  :   856 ( 29.1%) ██████████████
python      :   732 ( 24.9%) ████████████
rust        :   506 ( 17.2%) ████████
go          :   445 ( 15.1%) ███████
java        :   399 ( 13.6%) ██████

✅ QUALITÀ DATI
Funzioni complete: 2,938/2,938 (100.0%)
Lunghezza valida: 2,938/2,938 (100.0%)
```

---

## 3. FASE 2: TRAINING MODELLO

### 3.1 Training Demo (Quick Test - 30 minuti)

**Per test veloce del workflow:**

```powershell
python example_training.py
```

**Con configurazione custom:**

```powershell
python example_training.py --epochs 5 --batch-size 8
```

**Cosa fa:**
- Carica tutti i dati estratti
- Split 80/20 train/validation
- Addestra Codegen-350M
- Salva in `models/demo_trained/`

**Output:**
```
🔍 Verifica ambiente...
✅ PyTorch 2.1.0
✅ GPU: NVIDIA RTX 3080

📂 Caricamento dati...
✅ Caricati 2,938 esempi

📊 Split dataset...
   Training: 2,350 esempi
   Validation: 588 esempi

🚀 INIZIO TRAINING

Epoch 1/3
   Batch 10/587 (1.7%) - Loss: 2.1234
   ...
📊 Risultati Epoch 1:
   Train Loss: 1.8456
   Val Loss: 1.7234
   💾 Miglior modello salvato!

...

🎉 TRAINING COMPLETATO!
Best Validation Loss: 1.2345
Modello: models/demo_trained/
```

**Tempo:** ~25-30 minuti con GPU, ~3 ore con CPU

### 3.2 Training Production (Completo)

**Per modello production-ready:**

```powershell
python main.py --train code_generation
```

**Con monitoring:**

```powershell
# Terminal 1: Training
python main.py --train code_generation

# Terminal 2: TensorBoard
tensorboard --logdir logs/
# Apri http://localhost:6006
```

**Features production:**
- Multi-GPU automatico
- Checkpointing ogni epoch
- Early stopping
- Best model selection
- Cloud backup automatico
- Metriche dettagliate

**Output:**
```
📍 Device: cuda:0
🔥 Multi-GPU: True (2 GPUs)

📚 Caricamento dataset...
   Locale: 2,938 esempi
   Cloud: 12,456 esempi
   Totale: 15,394 esempi

🚀 Inizio training...

Epoch 1/4
Training: 100%|████████| 1924/1924 [24:15<00:00]
   Train Loss: 0.456
   Val Loss: 0.389
   Perplexity: 52.3

Epoch 2/4
Training: 100%|████████| 1924/1924 [23:58<00:00]
   Train Loss: 0.234
   Val Loss: 0.198
   Perplexity: 21.8
💾 Nuovo miglior modello!

...

✅ Training completato!
📊 Best Val Loss: 0.134
💾 Modello: models/saved/code_generation_best/
☁️  Backup cloud: OK
```

**Tempo:** ~4-6 ore con GPU singola

**File salvati:**
```
models/saved/
├── code_generation_best/       # Best model
│   ├── pytorch_model.bin
│   ├── config.json
│   └── tokenizer/
├── checkpoints/                # Checkpoints per epoch
│   ├── epoch_1/
│   ├── epoch_2/
│   └── epoch_3/
└── logs/                       # TensorBoard logs
```

### 3.3 Opzioni Training Avanzate

**Hyperparameters in config.py:**

```python
# Learning rate
LEARNING_RATE = 5e-5  # Diminuisci se loss instabile

# Batch size (adatta alla GPU RAM)
BATCH_SIZE = 8        # RTX 3080: 4-8
                      # RTX 3090: 16-32
                      # A100: 32-64

# Epochs
NUM_EPOCHS = 4        # 3-5 di solito sufficiente

# Max sequence length
MAX_LENGTH = 512      # 256=veloce, 512=bilanciato, 1024=lento
```

**Training con GPU Server remoto:**

```bash
# Su server GPU (Linux)
bash deploy_to_gpu.sh

# Poi esegui training
python main.py --train code_generation
```

---

## 4. FASE 3: INFERENZA

### 4.1 Test CLI Interattivo

**Metodo più semplice per testare:**

```powershell
python example_use_trained_model.py --interactive
```

**Sessione interattiva:**
```
💬 MODALITÀ INTERATTIVA

🔹 Prompt: Write a python function to calculate average

🤖 Generazione...

📝 Generated Code:
def calculate_average(numbers):
    """Calculate average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

🔹 Prompt: Create a javascript async function to fetch data

🤖 Generazione...

📝 Generated Code:
async function fetchData(url) {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}
```

### 4.2 Test Demo Mode

```powershell
python example_use_trained_model.py
```

Esegue 5 esempi predefiniti per diversi linguaggi.

### 4.3 Test con main.py

```powershell
python main.py --test models/demo_trained/
```

### 4.4 Inferenza Programmatica

**Script Python:**

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Carica modello
model_path = "models/demo_trained"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Move to GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

# Genera codice
prompt = "# Task: Write a python function to sort a list\n"
inputs = tokenizer(prompt, return_tensors='pt').to(device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=150,
        temperature=0.7,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(generated)
```

### 4.5 REST API Server (Production)

**Avvia server:**

```powershell
python gpu_server.py
```

**Output:**
```
🚀 ML Inference Server
   URL: http://0.0.0.0:8000
   Docs: http://0.0.0.0:8000/docs

📦 Loading models...
   ✓ code_generation loaded
   ✓ text_classification loaded

🎉 Server ready!
```

**Endpoint disponibili:**

1. **Generate Code** - `POST /generate`

```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prompt": "Write a function to calculate factorial",
        "max_length": 150,
        "temperature": 0.7
    }
)

print(response.json()["generated_text"])
```

2. **Classify Text** - `POST /classify`

```python
response = requests.post(
    "http://localhost:8000/classify",
    json={
        "text": "This function validates user input"
    }
)

print(response.json()["label"])
```

3. **Health Check** - `GET /health`

```python
response = requests.get("http://localhost:8000/health")
print(response.json())  # {"status": "healthy"}
```

4. **List Models** - `GET /models`

```python
response = requests.get("http://localhost:8000/models")
print(response.json())
# {"models": ["code_generation", "text_classification"]}
```

**API Documentation:**
Apri browser su: `http://localhost:8000/docs`

### 4.6 Batch Inference

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = "models/demo_trained"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Lista prompts
prompts = [
    "Write a function to calculate sum",
    "Create a class for user management",
    "Implement a binary search algorithm",
]

results = []
for prompt in prompts:
    inputs = tokenizer(f"# Task: {prompt}\n", return_tensors='pt').to(device)
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=150)
    
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    results.append({
        "prompt": prompt,
        "generated": generated
    })

# Salva risultati
import json
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## 5. TROUBLESHOOTING

### 5.1 Problema: "Repository not found" o "Authentication required"

**Causa:** Repository privato o token mancante.

**Soluzione:**

```powershell
# 1. Verifica token in .env
notepad .env

# 2. Verifica token sia corretto
python -c "import os; from dotenv import load_dotenv; load_dotenv(); token = os.getenv('GITHUB_TOKEN'); print('Token:', token[:10] + '...' if token else 'MISSING')"

# 3. Test con token
$env:GITHUB_TOKEN = "ghp_your_token"
python example_single_repo.py
```

### 5.2 Problema: "Storage connection failed"

**Causa:** Credenziali cloud storage mancanti o errate.

**Soluzione:**

```powershell
# 1. Test connessione
python debug/test_storage_quick.py

# 2. Verifica credenziali in .env
notepad .env

# 3. Test manuale
python -c "from module.storage.storage_manager import StorageManager; s = StorageManager(); print('Connected:', s.connect())"
```

**Output se funziona:**
```
✓ Storage provider: digitalocean
✓ Bucket: your-space-name
✓ Connected: True
```

### 5.3 Problema: "CUDA out of memory"

**Causa:** Batch size troppo grande per GPU RAM.

**Soluzione:**

```powershell
# Riduci batch size
python example_training.py --batch-size 2

# O in config.py
BATCH_SIZE = 2  # invece di 8
```

**Batch size consigliati:**
- RTX 3060 (12GB): 2-4
- RTX 3080 (10GB): 4-8
- RTX 3090 (24GB): 8-16
- A100 (40GB): 16-32

### 5.4 Problema: "Loss not decreasing"

**Diagnostica:**

```python
# 1. Verifica learning rate
LEARNING_RATE = 5e-5  # Prova 1e-4 o 2e-5

# 2. Verifica dati
python example_analyze_output.py
# Controlla qualità e diversità

# 3. Verifica overfitting
# Se train loss << val loss → overfitting
# Soluzione: più dati, dropout, meno epoch
```

### 5.5 Problema: "Import Error" o "Module not found"

**Soluzione:**

```powershell
# Reinstalla dipendenze
pip install -r requirements.txt --upgrade

# O specificamente
pip install torch transformers datasets
```

### 5.6 Problema: "Cloud storage not saving"

**Causa:** `cloud_save=False` o connessione fallita.

**Soluzione:**

```python
# In script, verifica cloud_save=True
processor = GitHubRepoProcessor(cloud_save=True)

# Verifica connessione
python debug/test_storage_quick.py
```

### 5.7 Problema: "Training molto lento su CPU"

**Soluzione:**

```powershell
# 1. Usa demo training con meno epoch
python example_training.py --epochs 2 --batch-size 2

# 2. O usa GPU cloud (Brev, Vast.ai, Lambda Labs)
bash deploy_to_gpu.sh

# 3. Oppure riduci dataset
# Modifica example_training.py per usare meno dati
```

---

## 6. WORKFLOW COMPLETO ESEMPIO

**Scenario: Training da zero a deployment in 2 ore (con GPU)**

```powershell
# 1. Setup (5 min)
copy .env.example .env
notepad .env  # Compila GITHUB_TOKEN e storage
pip install -r requirements.txt

# 2. Crawling (15 min)
@"
https://github.com/psf/requests
https://github.com/axios/axios
https://github.com/spf13/cobra
"@ | Out-File -Encoding UTF8 repo_list.txt

python example_bulk_processing.py

# 3. Verifica dati (2 min)
python example_analyze_output.py

# 4. Training (30 min)
python example_training.py --epochs 3

# 5. Test (2 min)
python example_use_trained_model.py --interactive

# 6. Deploy API (1 min)
python gpu_server.py

# 7. Test API
# In altro terminal:
python -c "import requests; r = requests.post('http://localhost:8000/generate', json={'prompt': 'Write a function'}); print(r.json())"
```

**Totale: ~55 minuti effettivi**

---

## 7. BEST PRACTICES

### 7.1 Crawling
- ✅ Usa `GITHUB_TOKEN` sempre (anche per repo pubblici = rate limit x10)
- ✅ Inizia con 5-10 repository per test
- ✅ Verifica dati con `example_analyze_output.py` prima di training
- ✅ Mantieni diversità linguaggi (min 3 linguaggi)
- ✅ Obiettivo: 5,000+ funzioni per training production

### 7.2 Training
- ✅ Test con `example_training.py` prima di production
- ✅ Monitora con TensorBoard (`tensorboard --logdir logs/`)
- ✅ Se loss non scende: riduci learning rate
- ✅ Se overfitting: più dati o meno epoch
- ✅ Salva checkpoint regolarmente

### 7.3 Inferenza
- ✅ Test locale con `example_use_trained_model.py` prima di deploy
- ✅ Temperature 0.7 = bilanciato (0.3=deterministico, 1.0=creativo)
- ✅ max_length 150 per funzioni normali, 300 per complesse
- ✅ Use top_p=0.95 per risultati migliori

### 7.4 Sicurezza
- ❌ Non committare `.env` su git
- ✅ `.env` è già in `.gitignore`
- ✅ Ruota token/keys regolarmente
- ✅ Usa API key per server production (`ENABLE_AUTH=true`)

---

## 8. METRICHE DI SUCCESSO

### Crawling
- ✅ > 5,000 funzioni estratte
- ✅ 100% qualità (syntax valida)
- ✅ Almeno 3 linguaggi diversi

### Training
- ✅ Validation loss < 1.0 (demo) o < 0.5 (production)
- ✅ Perplexity < 20
- ✅ Loss converge (decresce)

### Inferenza
- ✅ Generated code syntax valid > 85%
- ✅ Inference time < 1 secondo
- ✅ API response < 2 secondi

---

## 9. RISORSE

### Documentazione
- `QUICK_START_GUIDE.md` - Data extraction 5 min
- `QUICK_START_TRAINING.md` - Training 10 min
- `SISTEMA_COMPLETO.md` - Overview completo
- `WORKFLOW_GUIDE.md` - Visual workflow

### Scripts
- `example_single_repo.py` - Singolo repository
- `example_bulk_processing.py` - Batch processing
- `example_analyze_output.py` - Analisi dati
- `example_training.py` - Demo training
- `example_use_trained_model.py` - Inferenza
- `gpu_server.py` - REST API server

### Support
- Issues: GitHub Issues
- Logs: `logs/processing.log`, `logs/training.log`

---

**Sistema production-ready! Inizia subito con:**

```powershell
python example_single_repo.py  # Crawling
python example_training.py      # Training
python example_use_trained_model.py --interactive  # Inferenza
```

🚀 **Buon Machine Learning!**
