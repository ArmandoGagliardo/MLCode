# Quick Start - Remote ML API

Sistema client-server per eseguire ML su GPU remota (Brev/Nvidia) controllato dal tuo PC.

---

## ⚡ Setup Rapido

### 1. Su Istanza Brev/Nvidia (Server)

```bash
# Install dependencies
pip install fastapi uvicorn requests pydantic

# Start server
python -m presentation.api.server --host 0.0.0.0 --port 8000

# Output atteso:
# INFO - GPU Available: True
# INFO - GPU: NVIDIA A100-SXM4-40GB
# INFO - Uvicorn running on http://0.0.0.0:8000
```

Apri porta firewall:
```bash
sudo ufw allow 8000/tcp
```

Ottieni IP istanza:
```bash
curl ifconfig.me
# Output: 123.45.67.89
```

### 2. Dal Tuo PC (Client)

```python
from presentation.api.client import MLClient

# Connetti al server (sostituisci IP)
client = MLClient("http://123.45.67.89:8000")

# Test connessione
health = client.health_check()
print(f"GPU: {health['gpu_name']}")

# Genera codice
result = client.generate_code("def fibonacci(n):")
print(result.generated_code[0])

# Classifica codice
result = client.classify_code("import os; os.system('rm -rf /')")
print(f"{result.label}: {result.confidence:.0%}")

# Avvia training
job_id = client.start_training("data/dataset.json", epochs=20)
print(f"Training: {job_id}")

# Check status
status = client.get_training_status(job_id)
print(f"Progress: {status.progress}%")
```

### 3. Oppure usa CLI

```bash
# Health check
python -m presentation.api.client \
    --url http://123.45.67.89:8000 \
    --action health

# Generate code
python -m presentation.api.client \
    --url http://123.45.67.89:8000 \
    --action generate \
    --prompt "def factorial(n):"

# Start training
python -m presentation.api.client \
    --url http://123.45.67.89:8000 \
    --action train \
    --dataset data/dataset.json \
    --epochs 20
```

---

## 📚 Endpoints Disponibili

### Inferenza

- **POST** `/api/v1/inference/generate` - Genera codice
- **POST** `/api/v1/inference/classify` - Classifica codice

### Training

- **POST** `/api/v1/training/start` - Avvia training (async)
- **GET** `/api/v1/training/status/{job_id}` - Status training
- **GET** `/api/v1/training/jobs` - Lista tutti i job

### Monitoring

- **GET** `/health` - Health check + GPU info
- **GET** `/docs` - Documentazione interattiva (Swagger UI)

---

## 🎯 Esempi Completi

Vedi:
- **[examples/remote_client_example.py](examples/remote_client_example.py)** - 6 esempi pratici
- **[docs/REMOTE_API_GUIDE.md](docs/REMOTE_API_GUIDE.md)** - Documentazione completa

Run esempi:
```bash
python examples/remote_client_example.py --example 1  # Health check
python examples/remote_client_example.py --example 2  # Code generation
python examples/remote_client_example.py --example 3  # Security classification
python examples/remote_client_example.py              # Tutti
```

---

## 🔧 File Creati

```
presentation/api/
├── server.py          # FastAPI server (deploy su Brev)
├── client.py          # Python client (usa dal PC)
└── __init__.py

examples/
└── remote_client_example.py  # 6 esempi pratici

docs/
└── REMOTE_API_GUIDE.md       # Documentazione completa

requirements-api.txt           # Dipendenze API
```

---

## 🚀 Deploy Produzione

### Server (Brev/Nvidia)

```bash
# Con più workers per produzione
python -m presentation.api.server \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4

# Oppure con uvicorn direttamente
uvicorn presentation.api.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

### Client (Tuo PC)

Salva URL in variabile ambiente:
```bash
# Linux/Mac
export ML_SERVER="http://your-instance:8000"

# Windows
set ML_SERVER=http://your-instance:8000
```

Usa nel codice:
```python
import os
client = MLClient(os.environ["ML_SERVER"])
```

---

## ✅ Checklist

**Su Server Brev**:
- [ ] `pip install -r requirements-api.txt`
- [ ] `python -m presentation.api.server --host 0.0.0.0`
- [ ] Verifica `nvidia-smi` mostra GPU
- [ ] Apri porta 8000
- [ ] Ottieni IP: `curl ifconfig.me`

**Dal Tuo PC**:
- [ ] Salva IP server
- [ ] Test: `curl http://server-ip:8000/health`
- [ ] Run: `python examples/remote_client_example.py`
- [ ] Conferma output "✓ Examples completed successfully!"

---

## 📊 Performance Attesa

Con GPU A100:
- **Inferenza**: 50-200ms per generazione codice
- **Training**: 2-5 sec/epoch (dataset medio ~10k samples)
- **Latency rete**: +20-50ms (dipende da connessione)

---

## 🐛 Problemi Comuni

**"Connection refused"**
→ Verifica firewall: `sudo ufw allow 8000/tcp`

**"GPU not available"**
→ Check: `nvidia-smi` e reinstalla torch con CUDA

**"Dataset not found"**
→ Dataset deve esistere sul SERVER, non sul PC

---

**Documentazione completa**: [docs/REMOTE_API_GUIDE.md](docs/REMOTE_API_GUIDE.md)

**Swagger UI**: `http://your-server:8000/docs` (interattivo)
