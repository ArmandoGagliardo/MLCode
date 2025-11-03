# 🎓 QUICK START TRAINING - 10 MINUTI

Guida rapida per addestrare un modello con i dati estratti.

---

## ✅ PREREQUISITI

```powershell
# 1. Dati estratti (almeno 500+ funzioni consigliato)
dir datasets\local_backup\code_generation\*.json

# 2. PyTorch e Transformers
pip install torch transformers datasets accelerate

# 3. GPU consigliata (ma funziona anche CPU)
python -c "import torch; print('GPU:', torch.cuda.is_available())"
```

---

## 🚀 METODO 1: Training Demo (Più Veloce)

### Step 1: Esegui Training Demo

```powershell
# Training base con 3 epoch
python example_training.py

# Custom configurazione
python example_training.py --epochs 5 --batch-size 8
```

**Cosa fa:**
- Carica tutti i dati estratti
- Prepara train/validation split (80/20)
- Addestra modello Codegen-350M
- Salva modello in `models/demo_trained/`
- Test inference automatico

**Output Atteso:**
```
🔍 Verifica ambiente di training...
✅ PyTorch versione: 2.1.0
✅ GPU disponibile: NVIDIA RTX 3080
📍 Device di training: cuda

📂 Caricamento dati da: dataset_storage/local_backup/code_generation
✅ Caricati 6674 esempi totali

🔧 Preparazione dataset...
   Esempi validi: 6672/6674
   Breakdown per linguaggio:
      javascript  :  2195 (32.9%)
      python      :  1172 (17.6%)
      rust        :  1011 (15.1%)

📊 Split dataset (train: 80%, val: 20%)...
   Training: 5337 esempi
   Validation: 1335 esempi

🚀 INIZIO TRAINING (Versione Demo)
----------------------------------------------------------------------
📚 Epoch 1/3
   Batch 10/1334 (0.7%) - Loss: 2.8456
   Batch 20/1334 (1.5%) - Loss: 2.6234
   ...
   
📊 Risultati Epoch 1:
   Train Loss: 2.1234
   Val Loss: 1.9876
   💾 Nuovo miglior modello!
   ✅ Salvato in: models/demo_trained

🎉 TRAINING COMPLETATO!
Best Validation Loss: 1.5432
```

**Tempo stimato:**
- CPU: ~2-3 ore (3 epoch)
- GPU: ~20-30 minuti (3 epoch)

---

## 🔥 METODO 2: Training Production (Completo)

### Step 1: Verifica Dati Cloud (Opzionale)

```powershell
# Se hai configurato cloud storage
python -c "from module.storage.storage_manager import StorageManager; s = StorageManager(); print(s.list_files('datasets/'))"
```

### Step 2: Training Production

```powershell
# Code Generation
python main.py --train code_generation

# Text Classification
python main.py --train text_classification

# Security Classification
python main.py --train security_classification
```

**Cosa fa:**
- Carica dati da cloud o locale
- Training multi-GPU automatico (se disponibile)
- Checkpointing automatico
- Early stopping
- TensorBoard logging
- Best model selection

**Output Atteso:**
```
📍 Device di training: cuda:0
📚 Caricamento dataset...
✅ Caricati 67,891 esempi

🚀 Inizio training...

Epoch 1/4
Training: 100%|████████| 4243/4243 [24:15<00:00]
Train Loss: 0.456 | Val Loss: 0.389 | Perplexity: 52.3

Epoch 2/4
Training: 100%|████████| 4243/4243 [23:58<00:00]
Train Loss: 0.234 | Val Loss: 0.198 | Perplexity: 21.8
💾 Nuovo miglior modello salvato!

✅ Training completato!
📊 Best Val Loss: 0.134
💾 Modello salvato in: models/saved/code_generation_best
☁️  Backup su cloud completato
```

**Tempo stimato:**
- GPU singola (RTX 3080): ~4-6 ore (4 epoch, 70k esempi)
- Multi-GPU (2x RTX 3090): ~2-3 ore

---

## 📊 STEP 3: Monitoraggio Training

### Opzione A: TensorBoard (Production)

```powershell
# Avvia TensorBoard
tensorboard --logdir logs/

# Apri browser su http://localhost:6006
```

Visualizzi:
- Loss curves (train/val)
- Learning rate schedule
- Gradient norms
- Sample predictions

### Opzione B: Log Files

```powershell
# Tail dei log in tempo reale
Get-Content logs\training.log -Tail 50 -Wait

# Grep per errori
Select-String -Path logs\training.log -Pattern "error|warning"
```

---

## 🧪 STEP 4: Test del Modello

### Test Manuale

```powershell
python main.py --test models/demo_trained/
```

**Esempio Interactive:**
```
Enter prompt: Write a python function named calculate_average
Generated:
def calculate_average(numbers):
    """Calculate the average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
```

### Test Script

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_path = "models/demo_trained"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

prompt = "# Write a function to sort a list\n"
inputs = tokenizer(prompt, return_tensors='pt')
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

---

## ⚡ CONFIGURAZIONE AVANZATA

### Hyper-parameters (config.py o argomenti)

```python
# Learning Rate
learning_rate = 5e-5  # Default, buono per fine-tuning

# Batch Size
batch_size = 8        # Aumenta se hai molta GPU RAM
                      # RTX 3080 (10GB): 4-8
                      # RTX 3090 (24GB): 16-32
                      # A100 (40GB): 32-64

# Epochs
num_epochs = 4        # 3-5 di solito sufficiente per fine-tuning

# Max Length
max_length = 512      # Lunghezza massima sequenze
                      # 256: veloce ma tronca codice lungo
                      # 512: bilanciato
                      # 1024: lento ma gestisce funzioni grandi
```

### Multi-GPU Training

```powershell
# Automatico se hai multiple GPU
python main.py --train code_generation

# DataParallel (automatico se CUDA_VISIBLE_DEVICES non settato)
# Usa tutte le GPU disponibili

# Verifica GPU usate
python -c "import torch; print(f'GPU count: {torch.cuda.device_count()}')"
```

---

## 🐛 TROUBLESHOOTING

### "CUDA out of memory"

**Soluzione 1: Riduci Batch Size**
```powershell
python example_training.py --batch-size 2
```

**Soluzione 2: Riduci Max Length**
```python
# In example_training.py, linea ~180
max_length=128  # invece di 256
```

**Soluzione 3: Gradient Accumulation**
```python
# Accumula gradient per 4 step = simula batch size x4
gradient_accumulation_steps = 4
```

### "Loss non scende"

**Diagnostica:**
```python
# Verifica learning rate
lr = 5e-5  # Prova 1e-4 o 2e-5

# Verifica dati
python example_analyze_output.py
# Controlla qualità e varietà dati

# Verifica overfitting
# Se train loss << val loss → overfitting
# Soluzione: dropout, meno epoch, più dati
```

### "Training troppo lento"

**Ottimizzazioni:**
```python
# 1. Mixed Precision Training (FP16)
fp16 = True

# 2. Gradient Checkpointing (meno RAM)
gradient_checkpointing = True

# 3. Dataloader workers
num_workers = 4

# 4. Pin memory
pin_memory = True
```

---

## 📈 METRICHE DI SUCCESSO

### Code Generation

**Buone Metriche:**
- Validation Loss < 1.0
- Perplexity < 20
- Generated code è sintatticamente corretto > 80%

**Excellent Metriche:**
- Validation Loss < 0.5
- Perplexity < 10
- Generated code è sintatticamente corretto > 90%

### Come Valutare

```powershell
# Test su set di esempi
python main.py --evaluate

# Metrics mostrati:
# - BLEU score (similarità con reference)
# - CodeBLEU (specifico per codice)
# - Exact Match (% output identici)
# - Syntax Validity (% codice valido)
```

---

## 🚀 PROSSIMI PASSI

### 1. Fine-tuning Avanzato

```powershell
# Vedi GUIDA_TRAINING.md per:
# - LoRA (Parameter-Efficient Fine-Tuning)
# - Quantization (4-bit, 8-bit)
# - Custom architectures
notepad GUIDA_TRAINING.md
```

### 2. Deploy

```bash
# Deploy su GPU server (Linux)
bash deploy_to_gpu.sh

# Avvia inference server
python gpu_server.py
```

### 3. Production Pipeline

```powershell
# 1. Raccogli più dati
python example_bulk_processing.py

# 2. Training production
python main.py --train code_generation

# 3. Valuta
python main.py --evaluate

# 4. Deploy
# Usa gpu_server.py per API REST
```

---

## 💾 CHECKPOINTING

Il training salva automaticamente:

```
models/
├── demo_trained/           # Da example_training.py
│   ├── pytorch_model.bin
│   ├── config.json
│   └── tokenizer files
│
└── saved/                  # Da main.py --train
    ├── code_generation_best/
    ├── checkpoints/
    │   ├── epoch_1/
    │   ├── epoch_2/
    │   └── epoch_3/
    └── logs/
```

**Resume Training:**
```powershell
# Se interrotto, riprende dall'ultimo checkpoint
python main.py --train code_generation --resume
```

---

## 📚 RISORSE

- **Guida Completa**: `GUIDA_TRAINING.md`
- **Configurazione**: `config.py`
- **Training Scripts**: `module/model/train_generic.py`
- **GPU Deploy**: `deploy_to_gpu.sh`
- **Server API**: `gpu_server.py`

---

**Tempo Totale Workflow Completo:**
- Raccolta dati: 1-2 ore (10-20 repository)
- Training demo: 20-30 minuti (GPU)
- Training production: 4-6 ore (GPU)
- Testing e deploy: 30 minuti

**Total: ~6-9 ore per modello production-ready** ✨
