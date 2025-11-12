## Remote ML API - Guida Completa

Sistema client-server per eseguire training e inferenza ML su istanza remota Brev/Nvidia con GPU, controllata dal tuo PC locale.

---

## 🎯 Architettura

```
PC Locale                              Istanza Brev/Nvidia (GPU)
==========                             =========================
│                                      │
│ Python Client                        │ FastAPI Server
│  presentation/api/client.py          │  presentation/api/server.py
│                                      │
│  ┌──────────────────────┐           │  ┌──────────────────────┐
│  │ MLClient             │           │  │ /api/v1/inference    │
│  │  - generate_code()   │───HTTP───>│  │  - generate          │
│  │  - classify_code()   │           │  │  - classify          │
│  │  - start_training()  │           │  │ /api/v1/training     │
│  │  - get_status()      │<──JSON───│  │  - start             │
│  └──────────────────────┘           │  │  - status            │
│                                      │  └──────────────────────┘
│                                      │         │
│                                      │         ▼
│                                      │  ┌──────────────────────┐
│                                      │  │ ML Services          │
│                                      │  │  - InferenceService  │
│                                      │  │  - TrainModelUseCase │
│                                      │  │  - GPU/CUDA          │
│                                      │  └──────────────────────┘
```

---

## 📦 Setup

### Dipendenze

Aggiungi al `requirements.txt`:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.5.0
```

Installa:
```bash
pip install fastapi uvicorn requests pydantic
```

---

## 🚀 Avvio Server (su Istanza Brev/Nvidia)

### 1. Avvia Server

```bash
# Avvio semplice
python -m presentation.api.server

# Con opzioni
python -m presentation.api.server \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1

# Con auto-reload (development)
python -m presentation.api.server --reload
```

### 2. Verifica Avvio

Il server sarà disponibile su:
- **API**: `http://your-instance-ip:8000`
- **Docs**: `http://your-instance-ip:8000/docs` (Swagger UI interattivo)
- **Health**: `http://your-instance-ip:8000/health`

Log attesi:
```
INFO - Starting ML Code Intelligence API Server on 0.0.0.0:8000
INFO - GPU Available: True
INFO - GPU: NVIDIA A100-SXM4-40GB
INFO - Docs available at: http://0.0.0.0:8000/docs
INFO - Uvicorn running on http://0.0.0.0:8000
```

### 3. Configurazione Firewall (Brev)

Assicurati che la porta 8000 sia aperta:
```bash
# Su istanza Linux
sudo ufw allow 8000/tcp
sudo ufw status
```

---

## 💻 Uso Client (dal tuo PC Locale)

### Metodo 1: Client Python

```python
from presentation.api.client import MLClient

# Connetti al server remoto
client = MLClient("http://your-brev-instance-ip:8000")

# 1. Health check
health = client.health_check()
print(f"GPU: {health['gpu_name']}")

# 2. Genera codice
result = client.generate_code(
    prompt="def calculate_fibonacci(n):",
    max_length=150,
    temperature=0.7
)
print(result.generated_code[0])
print(f"Inference time: {result.inference_time_ms}ms")

# 3. Classifica codice per sicurezza
result = client.classify_code(
    code="import os; os.system('rm -rf /')",
    task="security"
)
print(f"Label: {result.label}, Confidence: {result.confidence:.2%}")

# 4. Avvia training (async)
job_id = client.start_training(
    dataset_path="data/dataset.json",  # Path sul server
    model_name="Salesforce/codet5-small",
    epochs=20,
    batch_size=16
)
print(f"Training started: {job_id}")

# 5. Monitora training
status = client.get_training_status(job_id)
print(f"Status: {status.status}, Progress: {status.progress}%")

# 6. Attendi completamento (blocking)
def on_progress(status):
    print(f"Epoch {status.current_epoch}/{status.total_epochs}")

result = client.wait_for_training(job_id, callback=on_progress)
print(f"Training completed!")
```

### Metodo 2: CLI

```bash
# Health check
python -m presentation.api.client \
    --url http://your-instance:8000 \
    --action health

# Generate code
python -m presentation.api.client \
    --url http://your-instance:8000 \
    --action generate \
    --prompt "def factorial(n):"

# Classify code
python -m presentation.api.client \
    --url http://your-instance:8000 \
    --action classify \
    --code "import os; os.system('ls')"

# Start training
python -m presentation.api.client \
    --url http://your-instance:8000 \
    --action train \
    --dataset data/dataset.json \
    --epochs 20

# Check training status
python -m presentation.api.client \
    --url http://your-instance:8000 \
    --action status \
    --job-id train_20250106_103000
```

### Metodo 3: curl (HTTP diretto)

```bash
# Health check
curl http://your-instance:8000/health

# Generate code
curl -X POST http://your-instance:8000/api/v1/inference/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n):",
    "max_length": 150,
    "temperature": 0.7
  }'

# Start training
curl -X POST http://your-instance:8000/api/v1/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_path": "data/dataset.json",
    "model_name": "Salesforce/codet5-small",
    "num_epochs": 20,
    "batch_size": 16
  }'

# Check status
curl http://your-instance:8000/api/v1/training/status/train_20250106_103000
```

---

## 📚 API Endpoints

### Health & Status

#### `GET /health`
Check server health and GPU info

**Response**:
```json
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "cuda_version": "12.1",
  "memory_allocated_gb": 2.45,
  "timestamp": "2025-01-06T10:30:00"
}
```

### Inference

#### `POST /api/v1/inference/generate`
Generate code from prompt

**Request**:
```json
{
  "prompt": "def calculate_fibonacci(n):",
  "max_length": 150,
  "temperature": 0.7,
  "top_p": 0.9,
  "num_return_sequences": 2
}
```

**Response**:
```json
{
  "generated_code": [
    "def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
    "def calculate_fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
  ],
  "prompt": "def calculate_fibonacci(n):",
  "inference_time_ms": 245.3,
  "model_name": "code_generator",
  "device": "cuda:0"
}
```

#### `POST /api/v1/inference/classify`
Classify code (e.g., security analysis)

**Request**:
```json
{
  "code": "import os; os.system('rm -rf /')",
  "task": "security"
}
```

**Response**:
```json
{
  "label": "vulnerable",
  "confidence": 0.95,
  "all_scores": {
    "vulnerable": 0.95,
    "safe": 0.05
  },
  "code": "import os; os.system('rm -rf /')",
  "inference_time_ms": 123.5
}
```

### Training

#### `POST /api/v1/training/start`
Start training job (async)

**Request**:
```json
{
  "dataset_path": "data/dataset.json",
  "model_name": "Salesforce/codet5-small",
  "num_epochs": 20,
  "batch_size": 16,
  "learning_rate": 5e-5,
  "output_dir": "models/my_model"
}
```

**Response**:
```json
{
  "job_id": "train_20250106_103000",
  "status": "pending",
  "message": "Training job started",
  "started_at": "2025-01-06T10:30:00"
}
```

#### `GET /api/v1/training/status/{job_id}`
Get training job status

**Response**:
```json
{
  "job_id": "train_20250106_103000",
  "status": "running",
  "progress": 45.5,
  "current_epoch": 9,
  "total_epochs": 20,
  "loss": 0.234,
  "started_at": "2025-01-06T10:30:00",
  "completed_at": null,
  "error": null
}
```

**Status values**:
- `pending`: Job queued
- `running`: Training in progress
- `completed`: Training finished successfully
- `failed`: Training failed (see `error`)

#### `GET /api/v1/training/jobs`
List all training jobs

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "train_20250106_103000",
      "status": "completed",
      "started_at": "2025-01-06T10:30:00"
    },
    {
      "job_id": "train_20250106_140000",
      "status": "running",
      "started_at": "2025-01-06T14:00:00"
    }
  ],
  "total": 2
}
```

---

## 🔧 Esempi Avanzati

### Esempio 1: Training con Monitoring

```python
from presentation.api.client import MLClient
import time

client = MLClient("http://your-instance:8000")

# Start training
job_id = client.start_training(
    dataset_path="data/large_dataset.json",
    model_name="Salesforce/codet5-base",
    epochs=50,
    batch_size=32
)

print(f"Training started: {job_id}")

# Monitor with custom callback
def on_progress(status):
    if status.status == "running":
        print(f"Epoch {status.current_epoch}/{status.total_epochs} - "
              f"Progress: {status.progress:.1f}% - Loss: {status.loss:.4f}")
    elif status.status == "completed":
        print("Training completed successfully!")
    elif status.status == "failed":
        print(f"Training failed: {status.error}")

# Wait for completion
try:
    result = client.wait_for_training(
        job_id,
        poll_interval=30,  # Check every 30 seconds
        callback=on_progress
    )
    print(f"Final status: {result.status}")
except KeyboardInterrupt:
    print("\nMonitoring interrupted. Job still running on server.")
    print(f"Check status with: client.get_training_status('{job_id}')")
```

### Esempio 2: Batch Code Generation

```python
from presentation.api.client import MLClient
from concurrent.futures import ThreadPoolExecutor
import time

client = MLClient("http://your-instance:8000")

# List of prompts to process
prompts = [
    "def sort_list(items):",
    "class Calculator:",
    "def read_file(path):",
    "async def fetch_data(url):",
    "def validate_email(email):"
]

def generate_single(prompt):
    """Generate code for single prompt"""
    try:
        result = client.generate_code(prompt, max_length=100)
        return {
            "prompt": prompt,
            "code": result.generated_code[0],
            "time_ms": result.inference_time_ms,
            "status": "success"
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "error": str(e),
            "status": "failed"
        }

# Process in parallel (max 5 concurrent)
print(f"Processing {len(prompts)} prompts...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(generate_single, prompts))

total_time = time.time() - start_time

# Print results
for i, result in enumerate(results, 1):
    print(f"\n[{i}] {result['prompt']}")
    if result['status'] == 'success':
        print(f"    → {result['code'][:60]}...")
        print(f"    Time: {result['time_ms']:.0f}ms")
    else:
        print(f"    Error: {result['error']}")

print(f"\nTotal time: {total_time:.1f}s")
print(f"Average time per prompt: {total_time/len(prompts):.2f}s")
```

### Esempio 3: Security Scanning

```python
from presentation.api.client import MLClient
from pathlib import Path

client = MLClient("http://your-instance:8000")

# Scan directory for security issues
code_dir = Path("src/")
vulnerable_files = []

print(f"Scanning {code_dir} for security issues...\n")

for py_file in code_dir.rglob("*.py"):
    with open(py_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # Classify
    result = client.classify_code(code, task="security")

    if result.label == "vulnerable" and result.confidence > 0.7:
        vulnerable_files.append({
            "file": str(py_file),
            "confidence": result.confidence
        })
        print(f"⚠️  {py_file} - Confidence: {result.confidence:.2%}")

print(f"\nFound {len(vulnerable_files)} potentially vulnerable files")
```

---

## 🔒 Sicurezza

### Autenticazione (TODO - implementare se necessario)

```python
# Con API key
client = MLClient(
    "http://your-instance:8000",
    api_key="your-secret-key"
)
```

Lato server, aggiungi middleware in `server.py`:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="Authorization")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != f"Bearer {API_KEY}":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Aggiungi dependency a endpoints
@app.post("/api/v1/inference/generate", dependencies=[Depends(verify_api_key)])
async def generate_code(request: InferenceRequest):
    ...
```

### HTTPS (Produzione)

Usa reverse proxy (nginx) con SSL:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Monitoring

### Logs

Server logs includono:
- Richieste ricevute
- Tempi di inferenza
- Errori
- Training progress

```bash
# Tail logs in tempo reale
tail -f server.log

# Filtra solo training
grep "Training" server.log
```

### Metriche

Aggiungi endpoint metriche:

```python
@app.get("/metrics")
async def metrics():
    return {
        "active_jobs": len([j for j in training_jobs.values() if j["status"] == "running"]),
        "completed_jobs": len([j for j in training_jobs.values() if j["status"] == "completed"]),
        "gpu_memory_allocated_gb": torch.cuda.memory_allocated(0) / (1024**3) if torch.cuda.is_available() else 0
    }
```

---

## 🐛 Troubleshooting

### Connection Error

**Problema**: `ConnectionError: Cannot connect to ML server`

**Soluzioni**:
1. Verifica server running: `ps aux | grep uvicorn`
2. Check firewall: `sudo ufw status`
3. Test connessione: `curl http://instance-ip:8000/health`
4. Verifica IP corretto dell'istanza Brev

### GPU Not Available

**Problema**: `gpu_available: false` nel health check

**Soluzioni**:
1. Verifica CUDA: `nvidia-smi`
2. Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
3. Reinstalla PyTorch con CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

### Training Job Stuck

**Problema**: Training status sempre "running"

**Soluzioni**:
1. Check server logs: `tail -f server.log`
2. Verifica memoria GPU: `nvidia-smi`
3. Check job error: `client.get_training_status(job_id).error`

---

## ✅ Checklist Deploy su Brev

- [ ] Installa dipendenze: `pip install -r requirements.txt`
- [ ] Verifica GPU disponibile: `nvidia-smi`
- [ ] Apri porta 8000: `sudo ufw allow 8000/tcp`
- [ ] Avvia server: `python -m presentation.api.server --host 0.0.0.0`
- [ ] Ottieni IP istanza: `curl ifconfig.me`
- [ ] Test dal PC: `curl http://instance-ip:8000/health`
- [ ] Salva URL in variabile: `export ML_SERVER=http://instance-ip:8000`
- [ ] Test inferenza dal PC: `python examples/remote_client_example.py`

---

**Documentazione completa disponibile su**: `http://your-instance:8000/docs` (Swagger UI interattivo)
