# 🔄 WORKFLOW COMPLETO - Data Extraction → Training → Deploy

Questo documento spiega il workflow completo del sistema, dall'estrazione dei dati al deploy del modello.

---

## 📊 OVERVIEW DEL PROCESSO

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: DATA EXTRACTION                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                              │
           ┌────────▼─────────┐         ┌─────────▼────────┐
           │  GitHub Repos    │         │  Local Code      │
           │  (Single/Batch)  │         │  Directories     │
           └────────┬─────────┘         └─────────┬────────┘
                    │                              │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Tree-Sitter AST Parsing    │
                    │  (7 Languages)              │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Quality Filtering          │
                    │  - Syntax validation        │
                    │  - Complexity check         │
                    │  - Duplicate detection      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  JSON Dataset Output        │
                    │  datasets/local_backup/     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ✅ 6,674+ Functions Extracted
                    
                    
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 2: DATA ANALYSIS                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  example_analyze_output.py  │
                    │  - Statistics per language  │
                    │  - Quality metrics          │
                    │  - Distribution analysis    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    📊 Analysis Summary Generated
                    
                    
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 3: MODEL TRAINING                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                              │
           ┌────────▼─────────┐         ┌─────────▼────────┐
           │  Demo Training   │         │  Production      │
           │  (Quick Test)    │         │  Training        │
           └────────┬─────────┘         └─────────┬────────┘
                    │                              │
     ┌──────────────▼──────────────┐  ┌───────────▼───────────┐
     │ example_training.py         │  │ main.py --train       │
     │ - Codegen-350M             │  │ - Custom config       │
     │ - 3 epochs                 │  │ - Multi-GPU           │
     │ - Basic fine-tuning        │  │ - Advanced features   │
     └──────────────┬──────────────┘  └───────────┬───────────┘
                    │                              │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Trained Model Output       │
                    │  models/demo_trained/       │
                    │  models/saved/              │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    🤖 Model Ready for Inference
                    
                    
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 4: EVALUATION                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Model Testing              │
                    │  - Test prompts             │
                    │  - Metrics calculation      │
                    │  - Quality assessment       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ✅ Validation Complete
                    
                    
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 5: DEPLOYMENT                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                              │
           ┌────────▼─────────┐         ┌─────────▼────────┐
           │  Local Inference │         │  GPU Server      │
           │  (Development)   │         │  (Production)    │
           └────────┬─────────┘         └─────────┬────────┘
                    │                              │
     ┌──────────────▼──────────────┐  ┌───────────▼───────────┐
     │ python main.py --test       │  │ gpu_server.py         │
     │ - CLI testing               │  │ - REST API            │
     │ - Interactive mode          │  │ - Multi-model         │
     └─────────────────────────────┘  │ - FastAPI             │
                                      └───────────┬───────────┘
                                                  │
                                      ┌───────────▼───────────┐
                                      │ Client Applications   │
                                      │ - Web interface       │
                                      │ - API calls           │
                                      │ - Integration         │
                                      └───────────────────────┘
```

---

## 🎯 ESEMPI PRATICI PER OGNI FASE

### FASE 1: Estrazione Dati

#### Esempio 1: Single Repository
```powershell
# Estrai da un singolo repository
python example_single_repo.py

# Oppure con main.py
python main.py
# Scegli opzione 1, inserisci URL
```

**Input:** `https://github.com/psf/requests`  
**Output:** `datasets/local_backup/code_generation/requests_*.json` (225 funzioni)  
**Tempo:** ~2-3 minuti

#### Esempio 2: Bulk Processing
```powershell
# Crea lista repository
"https://github.com/psf/requests" > repo_list.txt
"https://github.com/axios/axios" >> repo_list.txt
"https://github.com/spf13/cobra" >> repo_list.txt

# Processa tutti
python example_bulk_processing.py
```

**Input:** `repo_list.txt` (3 repository)  
**Output:** Multiple JSON files (~1,000 funzioni)  
**Tempo:** ~10-15 minuti

---

### FASE 2: Analisi Dati

```powershell
# Analizza tutti i dati estratti
python example_analyze_output.py
```

**Cosa mostra:**
- ✅ Totale funzioni: 6,674
- ✅ Per linguaggio: JS 33%, Python 18%, Rust 15%, etc.
- ✅ Lunghezza media: 441 caratteri
- ✅ Qualità: 100% funzioni complete

**Output:** `datasets/local_backup/code_generation/analysis_summary.json`

---

### FASE 3: Training

#### Opzione A: Demo Training (Quick Test)
```powershell
# Training veloce per test
python example_training.py --epochs 3 --batch-size 4
```

**Configurazione:**
- Modello: Codegen-350M (piccolo, veloce)
- Dati: Tutti i JSON in local_backup/
- Split: 80% train, 20% validation
- Device: Auto-detect (GPU o CPU)

**Output:**
- Modello: `models/demo_trained/`
- Loss finale: ~1.5-2.0
- Tempo: 20-30 min (GPU), 2-3 ore (CPU)

#### Opzione B: Production Training
```powershell
# Training completo production
python main.py --train code_generation
```

**Configurazione:**
- Modello: Configurabile (CodeGen, CodeT5, etc.)
- Dati: Cloud + local
- Features: Multi-GPU, checkpointing, early stopping
- Monitoring: TensorBoard

**Output:**
- Modello: `models/saved/code_generation_best/`
- Checkpoints: `models/saved/checkpoints/`
- Loss finale: ~0.5-1.0
- Tempo: 4-6 ore (GPU singola), 2-3 ore (multi-GPU)

---

### FASE 4: Evaluation

```powershell
# Test interattivo
python main.py --test models/demo_trained/
```

**Esempio Session:**
```
> Enter prompt: Write a python function named add_numbers
> Generated:
def add_numbers(a, b):
    """Add two numbers and return the result"""
    return a + b

> Enter prompt: Create a javascript async function
> Generated:
async function fetchData(url) {
    const response = await fetch(url);
    return await response.json();
}
```

**Metriche:**
- Syntax validity: 85-95%
- BLEU score: 40-60
- Inference time: 0.1-0.5s per generation

---

### FASE 5: Deployment

#### Opzione A: Local Testing
```powershell
# Test locale con CLI
python main.py --test models/demo_trained/
```

#### Opzione B: REST API Server
```powershell
# Avvia server FastAPI
python gpu_server.py
```

**API Endpoints:**
- `POST /generate` - Generate code
- `POST /classify` - Classify text
- `GET /models` - List models
- `GET /health` - Health check

**Esempio API Call:**
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prompt": "Write a function to calculate factorial",
        "max_length": 100,
        "temperature": 0.7
    }
)

print(response.json()["generated_text"])
```

---

## ⏱️ TEMPO TOTALE WORKFLOW

| Fase | Tempo (GPU) | Tempo (CPU) |
|------|-------------|-------------|
| 1. Estrazione (10 repos) | 15 min | 15 min |
| 2. Analisi | 1 min | 1 min |
| 3. Training Demo | 25 min | 3 ore |
| 3. Training Production | 5 ore | 20+ ore |
| 4. Evaluation | 5 min | 10 min |
| 5. Deploy Setup | 10 min | 10 min |
| **TOTAL (Demo)** | **~1 ora** | **~4 ore** |
| **TOTAL (Production)** | **~6 ore** | **~24+ ore** |

---

## 🔧 CONFIGURAZIONE PER SCENARIO

### Scenario 1: Quick Test (1 ora)
```powershell
# 1. Estrai dati (piccolo dataset)
python example_single_repo.py

# 2. Training demo
python example_training.py --epochs 2

# 3. Test
python main.py --test models/demo_trained/
```

### Scenario 2: Development (1 giorno)
```powershell
# 1. Estrai più dati
python example_bulk_processing.py  # 5-10 repos

# 2. Analizza
python example_analyze_output.py

# 3. Training demo esteso
python example_training.py --epochs 5 --batch-size 8

# 4. Test e iterate
python main.py --test models/demo_trained/
```

### Scenario 3: Production (3-5 giorni)
```powershell
# 1. Estrai dataset grande
python bulk_processor.py --source github --repos large_repo_list.txt

# 2. Analizza e verifica qualità
python example_analyze_output.py

# 3. Training production
python main.py --train code_generation
# Monitora con: tensorboard --logdir logs/

# 4. Evaluation completa
python main.py --evaluate

# 5. Deploy su GPU server
bash deploy_to_gpu.sh
python gpu_server.py
```

---

## 📊 METRICHE DI SUCCESSO

### Estrazione Dati
- ✅ > 5,000 funzioni estratte
- ✅ Qualità 100% (syntax valida)
- ✅ Diversità: almeno 3 linguaggi
- ✅ No duplicati

### Training
- ✅ Validation loss < 1.0 (demo) o < 0.5 (production)
- ✅ Perplexity < 20
- ✅ Training converge (loss decresce)
- ✅ No overfitting (train loss ≈ val loss)

### Deployment
- ✅ Inference time < 1s
- ✅ Generated code syntax valid > 85%
- ✅ API response time < 2s
- ✅ Server uptime > 99%

---

## 🎓 NEXT STEPS

1. **Segui Quick Starts:**
   - `QUICK_START_GUIDE.md` per estrazione
   - `QUICK_START_TRAINING.md` per training

2. **Guide Complete:**
   - `USAGE_GUIDE.md` per data extraction
   - `GUIDA_TRAINING.md` per training avanzato

3. **Examples:**
   - Esegui tutti gli example_*.py per familiarizzare

4. **Production:**
   - Leggi deploy_to_gpu.sh per deploy
   - Testa gpu_server.py per API

---

**Il sistema è production-ready e completamente funzionante!** 🚀
