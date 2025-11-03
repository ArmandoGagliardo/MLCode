# GPU Instance Setup Guide

Complete guide for deploying the Machine Learning project on GPU instances (Brev, AWS, GCP, Azure, etc.) with automated training and inference.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Manual Setup](#manual-setup)
5. [Training Models](#training-models)
6. [Running Inference Server](#running-inference-server)
7. [API Usage](#api-usage)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

---

## Overview

### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT WORKFLOW                      │
└─────────────────────────────────────────────────────────────┘

LOCAL MACHINE
  ├── Develop code
  ├── Push to GitHub
  └── git push origin main

         ↓

GITHUB REPOSITORY
  └── https://github.com/your-username/MachineLearning

         ↓

GPU INSTANCE (Brev/AWS/GCP/Azure)
  ├── 1. git clone https://github.com/.../MachineLearning
  ├── 2. bash deploy_to_gpu.sh
  │      ├── Install dependencies
  │      ├── Download datasets (optional)
  │      ├── Train models on GPU:
  │      │   ├── code_generation
  │      │   ├── text_classification
  │      │   └── security_classification
  │      └── Save to models/ directory
  ├── 3. uvicorn gpu_server:app --host 0.0.0.0 --port 8000
  │      ├── Load trained models
  │      ├── GPU acceleration enabled
  │      └── Expose REST API endpoints
  └── 4. Ready for inference!

         ↓

CLIENT (Laptop/Server/Web App)
  └── HTTP requests to GPU instance API
```

---

## Prerequisites

### Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA support (recommended: 16GB+ VRAM)
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free disk space
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements

- **Python**: 3.8 or higher
- **CUDA**: 11.8 or higher (for GPU support)
- **Git**: For cloning the repository
- **pip**: Python package manager

### Supported GPU Platforms

- ✅ **Brev** - Recommended for ease of use
- ✅ **AWS EC2** (g4dn, g5, p3, p4 instances)
- ✅ **Google Cloud Platform** (with GPU)
- ✅ **Azure** (NC, ND series)
- ✅ **Paperspace**
- ✅ **Lambda Labs**
- ✅ **RunPod**

---

## Quick Start

### 1. SSH into Your GPU Instance

```bash
# Brev example
brev open your-instance-name

# Or standard SSH
ssh user@your-gpu-instance-ip
```

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/MachineLearning.git
cd MachineLearning
```

### 3. Run Deployment Script

```bash
bash deploy_to_gpu.sh
```

That's it! The script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup configuration
- ✅ Train all models on GPU
- ✅ Start inference API server

The server will be available at `http://your-instance-ip:8000`

---

## Manual Setup

If you prefer manual setup or the automated script fails:

### Step 1: Verify GPU Availability

```bash
# Check NVIDIA GPU
nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.XX       Driver Version: 525.XX       CUDA Version: 12.0    |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA A10          Off  | 00000000:00:1E.0 Off |                    0 |
# |  0%   30C    P0    55W / 150W |      0MiB / 24576MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy GPU configuration template
cp gpu_instance.env .env

# Edit configuration
nano .env

# REQUIRED: Add your GitHub token
# GITHUB_TOKEN=ghp_your_token_here
```

### Step 5: Build Tree-Sitter Grammars

```bash
python build_languages.py
```

### Step 6: Download Datasets (Optional)

If datasets are not in the repo:

```bash
# Option A: Download from cloud storage
python main.py --storage-download

# Option B: Use existing datasets in datasets/ folder
# (Nothing to do if datasets are already in repo)
```

---

## Training Models

### Train All Models

```bash
# Code generation model
python main.py --train code_generation

# Text classification model
python main.py --train text_classification

# Security classification model
python main.py --train security_classification
```

### Training Options

Edit [config.py](config.py) or set environment variables:

```bash
# Increase batch size for larger GPU
export DEFAULT_BATCH_SIZE=16

# More epochs for better accuracy
export DEFAULT_EPOCHS=15

# Adjust learning rate
export DEFAULT_LEARNING_RATE=3e-5
```

### Monitor Training

Training progress is logged to console:

```
[INFO] Using device: cuda
[INFO] GPU: NVIDIA A10, 24GB
[INFO] Training code_generation model...
Epoch 1/10: 100%|████████████| 1000/1000 [05:23<00:00, 3.09it/s, loss=0.342]
Validation Loss: 0.298
[INFO] Model saved to models/code_generation
```

### Expected Training Times

| Model                  | GPU (A10)  | GPU (V100) | CPU     |
|------------------------|------------|------------|---------|
| code_generation        | ~30 min    | ~20 min    | ~4 hours|
| text_classification    | ~15 min    | ~10 min    | ~2 hours|
| security_classification| ~20 min    | ~15 min    | ~3 hours|

### Verify Trained Models

```bash
ls -lh models/

# Expected output:
# models/
# ├── code_generation/
# │   ├── config.json
# │   ├── model.safetensors
# │   ├── tokenizer_config.json
# │   └── ...
# ├── text_classification/
# │   └── ...
# └── security_classification/
#     └── ...
```

---

## Running Inference Server

### Start Server

```bash
# Basic usage
uvicorn gpu_server:app --host 0.0.0.0 --port 8000

# With auto-reload (development)
uvicorn gpu_server:app --host 0.0.0.0 --port 8000 --reload

# With multiple workers (production)
uvicorn gpu_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify Server is Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "gpu_available": true,
#   "cuda_version": "12.0",
#   "models_loaded": {
#     "code_generation": true,
#     "text_classification": true,
#     "security_classification": true
#   }
# }
```

### Check Loaded Models

```bash
curl http://localhost:8000/models

# Expected response:
# {
#   "models": {
#     "code_generation": {
#       "loaded": true,
#       "device": "cuda:0",
#       "path": "models/code_generation"
#     },
#     "text_classification": {
#       "loaded": true,
#       "device": "cuda:0",
#       "path": "models/text_classification"
#     },
#     "security_classification": {
#       "loaded": true,
#       "device": "cuda:0",
#       "path": "models/security_classification"
#     }
#   }
# }
```

### Server Logs

Server logs show:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     [INFO] Starting GPU Inference Server...
INFO:     [INFO] CUDA available: True
INFO:     [INFO] CUDA version: 12.0
INFO:     [INFO] GPU device: NVIDIA A10
INFO:     [INFO] GPU count: 1
INFO:     [INFO] Loading code generation model from models/code_generation...
INFO:     [INFO] Code generation model loaded successfully!
INFO:     [INFO] Loading text classification model from models/text_classification...
INFO:     [INFO] Text classification model loaded successfully!
INFO:     [INFO] Loading security classification model from models/security_classification...
INFO:     [INFO] Security classification model loaded successfully!
INFO:     [INFO] Models loaded: 3/3
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## API Usage

### Interactive API Documentation

Open in your browser:

- **Swagger UI**: `http://your-instance-ip:8000/docs`
- **ReDoc**: `http://your-instance-ip:8000/redoc`

### Code Generation

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate fibonacci numbers",
    "max_tokens": 128,
    "temperature": 0.8
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
#     "prompt": "Create a function to calculate fibonacci numbers"
#   }
# }
```

### Text Classification

```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is amazing! I love it."
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "prediction": 1,
#     "label": "positive",
#     "text": "This product is amazing! I love it."
#   }
# }
```

### Security Analysis

```bash
curl -X POST http://localhost:8000/api/security \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import os\nos.system(user_input)"
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "prediction": 2,
#     "level": "critical",
#     "code": "import os\nos.system(user_input)"
#   }
# }
```

### Python Client Example

```python
import requests

# Configure API endpoint
API_URL = "http://your-instance-ip:8000"

# Generate code
response = requests.post(
    f"{API_URL}/api/generate",
    json={
        "prompt": "Write a function to sort a list",
        "temperature": 0.7
    }
)

result = response.json()
print(result["data"]["code"])
```

---

## Troubleshooting

### Issue: "CUDA out of memory"

**Solution**: Reduce batch size in [config.py](config.py)

```python
DEFAULT_BATCH_SIZE = 4  # Reduce from 8 to 4
```

Or set environment variable:

```bash
export DEFAULT_BATCH_SIZE=4
python main.py --train code_generation
```

### Issue: "No module named 'tree_sitter'"

**Solution**: Build tree-sitter grammars

```bash
python build_languages.py
```

### Issue: "Models not found" when starting server

**Solution**: Train models first

```bash
# Train all models
python main.py --train code_generation
python main.py --train text_classification
python main.py --train security_classification

# Verify models exist
ls -la models/
```

### Issue: "Connection refused" when accessing API

**Solution**: Check firewall and port configuration

```bash
# Check if server is running
ps aux | grep uvicorn

# Check if port is open
netstat -tulpn | grep 8000

# Allow port through firewall (Ubuntu/Debian)
sudo ufw allow 8000

# Test locally first
curl http://localhost:8000/health
```

### Issue: "GitHub authentication failed"

**Solution**: Add GitHub token to .env

```bash
# Create token at: https://github.com/settings/tokens
# Required scopes: repo

# Edit .env
nano .env

# Add:
GITHUB_TOKEN=ghp_your_token_here
```

### Issue: Server crashes with "Segmentation fault"

**Solution**: Update PyTorch and CUDA drivers

```bash
# Check CUDA version
nvidia-smi

# Reinstall PyTorch with correct CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Training is very slow

**Checklist**:

1. Verify GPU is being used:
   ```bash
   nvidia-smi  # Should show Python process using GPU
   ```

2. Check [main.py:81](main.py#L81) - Should be `use_gpu=True`

3. Monitor GPU utilization:
   ```bash
   watch -n 1 nvidia-smi
   ```

4. Increase batch size if GPU memory allows

### Check Logs

```bash
# View detailed logs
tail -f logs/gpu_instance.log

# Check for errors
grep ERROR logs/gpu_instance.log
```

---

## Production Deployment

### Running as Background Service

#### Option 1: Using systemd (Recommended)

Create service file:

```bash
sudo nano /etc/systemd/system/ml-gpu-server.service
```

Add content:

```ini
[Unit]
Description=ML GPU Inference Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/MachineLearning
Environment="PATH=/home/ubuntu/MachineLearning/.venv/bin"
ExecStart=/home/ubuntu/MachineLearning/.venv/bin/uvicorn gpu_server:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ml-gpu-server
sudo systemctl start ml-gpu-server

# Check status
sudo systemctl status ml-gpu-server

# View logs
sudo journalctl -u ml-gpu-server -f
```

#### Option 2: Using screen

```bash
# Start new screen session
screen -S ml-server

# Run server
uvicorn gpu_server:app --host 0.0.0.0 --port 8000

# Detach: Ctrl+A, then D

# Reattach
screen -r ml-server
```

#### Option 3: Using tmux

```bash
# Start new tmux session
tmux new -s ml-server

# Run server
uvicorn gpu_server:app --host 0.0.0.0 --port 8000

# Detach: Ctrl+B, then D

# Reattach
tmux attach -t ml-server
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Monitoring

```bash
# GPU monitoring
nvidia-smi -l 1

# Server monitoring
htop

# Network monitoring
iftop
```

### Auto-restart on Failure

Systemd automatically restarts the service if it crashes (see `Restart=always` in service file).

### Backup Models to Cloud

```bash
# Configure cloud storage in .env
STORAGE_PROVIDER=backblaze  # or wasabi, s3, etc.

# Backup all models
python main.py --storage-backup
```

---

## Security Best Practices

1. **API Authentication**: Enable in [gpu_instance.env](gpu_instance.env)
   ```bash
   ENABLE_AUTH=true
   API_KEY=your-secure-random-key
   ```

2. **Firewall**: Only allow necessary ports
   ```bash
   sudo ufw enable
   sudo ufw allow 22    # SSH
   sudo ufw allow 8000  # API
   ```

3. **SSL**: Always use HTTPS in production

4. **Rate Limiting**: Configure in [gpu_instance.env](gpu_instance.env)
   ```bash
   RATE_LIMIT=60  # requests per minute
   ```

5. **Regular Updates**:
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```

---

## Cost Optimization

### GPU Instance Costs (Approximate)

| Provider  | Instance Type | GPU       | RAM   | $/hour | $/month |
|-----------|---------------|-----------|-------|--------|---------|
| Brev      | GPU-M         | A10       | 32GB  | $0.69  | ~$500   |
| AWS       | g4dn.xlarge   | T4        | 16GB  | $0.526 | ~$380   |
| AWS       | g5.xlarge     | A10G      | 16GB  | $1.006 | ~$730   |
| Paperspace| P4000         | P4000     | 8GB   | $0.51  | ~$370   |
| RunPod    | RTX 4090      | RTX 4090  | 24GB  | $0.69  | ~$500   |

### Tips to Reduce Costs

1. **Train locally, deploy for inference**: Train on powerful GPU, deploy on cheaper instance
2. **Spot instances**: Use AWS/GCP spot instances (50-70% cheaper)
3. **Auto-shutdown**: Shutdown when not in use
4. **Smaller models**: Use quantization/distillation for smaller models
5. **Batch processing**: Process multiple requests in batches

---

## Next Steps

1. ✅ Train your models on GPU
2. ✅ Start inference server
3. ✅ Test API endpoints
4. 📱 Integrate with your application
5. 🚀 Deploy to production with systemd
6. 📊 Monitor performance
7. 🔄 Setup CI/CD for automatic deployment

---

## Support

- 📖 **Documentation**: See [README.md](README.md)
- 🐛 **Issues**: Report on GitHub Issues
- 💬 **Discussions**: GitHub Discussions

---

## Appendix

### Deployment Script Options

```bash
# Skip training (use existing models)
bash deploy_to_gpu.sh --skip-training

# Skip dataset download
bash deploy_to_gpu.sh --skip-datasets

# Custom port
bash deploy_to_gpu.sh --port 9000

# Combined options
bash deploy_to_gpu.sh --skip-training --port 9000
```

### Environment Variables Reference

See [gpu_instance.env](gpu_instance.env) for complete list of configuration options.

### API Endpoints Reference

| Endpoint         | Method | Description               |
|------------------|--------|---------------------------|
| `/`              | GET    | Root endpoint             |
| `/health`        | GET    | Health check              |
| `/models`        | GET    | List loaded models        |
| `/api/generate`  | POST   | Code generation           |
| `/api/classify`  | POST   | Text classification       |
| `/api/security`  | POST   | Security analysis         |
| `/docs`          | GET    | Swagger UI docs           |
| `/redoc`         | GET    | ReDoc documentation       |

---

**Last Updated**: 2025-01-02
**Version**: 1.0.0
