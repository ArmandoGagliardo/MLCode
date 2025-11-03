# Brev NVIDIA Client - Sistema Completo

Sistema client-server per interagire con istanze Brev NVIDIA tramite interfaccia web moderna.

## Caratteristiche Principali

- **Backend FastAPI**: REST API robusta e scalabile
- **Frontend Web Moderno**: Interfaccia dark theme responsive
- **Autenticazione a Due Livelli**: Bearer token + rate limiting
- **Multiple Features**: Generazione codice, analisi security, batch processing
- **Multi-Instance Support**: Load balancing tra istanze Brev
- **API Documentation**: Swagger UI automatica
- **Testing Suite**: Test automatici per autenticazione

## Architettura

```
┌─────────────────┐
│  Web Browser    │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/REST + Bearer Token
         ▼
┌─────────────────┐
│  FastAPI Server │
│  (Backend)      │
│  - Auth         │
│  - Rate Limit   │
└────────┬────────┘
         │ HTTP/REST + API Key
         ▼
┌─────────────────┐
│  Brev Instance  │
│  (NVIDIA GPU)   │
└─────────────────┘
```

## Installazione

### 1. Requisiti

```bash
# Python 3.8+
python --version

# Installa dipendenze
pip install fastapi uvicorn requests pydantic python-dotenv
```

### 2. Configurazione

```bash
# Crea il file di configurazione
cp client/config/.env.example client/config/.env

# Genera una chiave API sicura
python client/generate_api_key.py

# Modifica .env con i tuoi dati
```

**File `.env` di esempio**:
```bash
# Istanza Brev NVIDIA
BREV_API_URL=http://your-brev-instance:8000
BREV_API_KEY=your_brev_api_key

# Server Backend
SERVER_API_KEY=brev_abc123xyz...  # generata con generate_api_key.py

# Opzionale
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=60
```

### 3. Avvio

```bash
# Dalla root del progetto
cd c:\Users\arman\Documents\GitHub\PythonRepo\MachineLearning

# Avvia il server
python -m uvicorn client.backend.server:app --host 0.0.0.0 --port 5000 --reload
```

Apri il browser su: **http://localhost:5000**

## Uso del Sistema

### Frontend Web UI

1. **Code Generation Tab**:
   - Inserisci una descrizione (es. "Create a sum function in Python")
   - Seleziona linguaggio e parametri
   - Ricevi il codice generato

2. **Security Analysis Tab**:
   - Incolla codice da analizzare
   - Seleziona tipo di scan (quick/deep)
   - Visualizza vulnerabilità trovate

3. **Batch Generation Tab**:
   - Inserisci multipli prompt (uno per riga)
   - Genera codice per tutti i prompt
   - Visualizza risultati

### API Endpoints

#### POST /api/generate
Genera codice da un prompt.

**Request**:
```json
{
  "prompt": "Create a sum function in Python",
  "language": "python",
  "max_length": 256,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "code": "def sum(a, b):\n    return a + b",
    "language": "python"
  },
  "timestamp": "2025-11-01T20:30:00",
  "request_id": "abc-123"
}
```

#### POST /api/security
Analizza codice per vulnerabilità.

**Request**:
```json
{
  "code": "def execute(cmd):\n    import os\n    os.system(cmd)",
  "language": "python",
  "scan_type": "quick"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "vulnerabilities": [
      {
        "type": "command_injection",
        "severity": "high",
        "line": 2,
        "description": "Uso di os.system senza sanitizzazione"
      }
    ],
    "safe": false
  }
}
```

#### POST /api/batch
Genera codice per multipli prompt.

**Request**:
```json
{
  "prompts": [
    "Create a sum function",
    "Create a multiply function"
  ],
  "language": "python"
}
```

#### GET /health
Verifica stato del sistema.

**Response**:
```json
{
  "status": "healthy",
  "brev_instance": true
}
```

#### GET /api/model/info
Informazioni sul modello caricato.

#### GET /api/stats
Statistiche di utilizzo.

## Sistema di Autenticazione

### SERVER_API_KEY

**Scopo**: Protegge il backend da accessi non autorizzati.

**Configurazione**:
1. Genera chiave: `python client/generate_api_key.py`
2. Aggiungi a `.env`: `SERVER_API_KEY=brev_...`
3. Usa nel frontend con header: `Authorization: Bearer brev_...`

**Features**:
- Rate limiting (60 req/min default)
- Permessi granulari (all, generate, security, classify)
- Statistiche utilizzo per chiave
- Supporto multiple chiavi

**Esempio codice**:
```python
# Backend (auth.py)
api_key_manager = APIKeyManager()

# Endpoint protetto
@app.post("/api/generate")
async def generate(api_key: str = Depends(verify_api_key)):
    # Solo con chiave valida
    pass

# Frontend (JavaScript)
fetch('/api/generate', {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
})
```

### BREV_API_KEY

**Scopo**: Autentica il backend verso l'istanza Brev.

**Configurazione**:
1. Ottieni chiave dall'istanza Brev
2. Aggiungi a `.env`: `BREV_API_KEY=your_key`
3. Il backend la usa automaticamente

## Testing

### Test Autenticazione

```bash
cd client
python test_auth.py
```

Verifica:
- ✓ Richiesta senza auth → 401
- ✓ Richiesta con auth errata → 401
- ✓ Richiesta con auth corretta → 200
- ✓ Health check pubblico → 200

### Test Manuale con curl

```bash
# Senza autenticazione (fallisce)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Con autenticazione (funziona)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"prompt": "Create a sum function", "language": "python"}'
```

## Configurazione Avanzata

### Multiple API Keys

Modifica `client/backend/auth.py`:

```python
additional_keys = {
    'client-key-123': {
        'name': 'web_client',
        'permissions': ['generate', 'security'],
        'rate_limit': 60
    },
    'admin-key-456': {
        'name': 'admin',
        'permissions': ['all'],
        'rate_limit': 200
    }
}
```

### Multiple Brev Instances

Load balancing round-robin:

```bash
# Nel .env
BREV_INSTANCES=http://instance1:8000,http://instance2:8000,http://instance3:8000
```

Il sistema distribuisce automaticamente le richieste.

### Rate Limiting Personalizzato

```python
# In auth.py
self.keys[main_key] = {
    'name': 'main',
    'permissions': ['all'],
    'rate_limit': 100  # richieste per minuto
}
```

### CORS Configuration

Per produzione, limita i domini:

```python
# In server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # invece di ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Deployment in Produzione

### Con Gunicorn (Linux)

```bash
pip install gunicorn

gunicorn client.backend.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:5000 \
  --timeout 60
```

### Con Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY client/ ./client/
COPY main.py .

CMD ["uvicorn", "client.backend.server:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Con systemd (Linux)

```ini
# /etc/systemd/system/brev-client.service
[Unit]
Description=Brev Client API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/MachineLearning
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn client.backend.server:app --host 0.0.0.0 --port 5000

[Install]
WantedBy=multi-user.target
```

## Struttura File

```
client/
├── backend/
│   ├── __init__.py
│   ├── server.py              # FastAPI REST API
│   ├── brev_client.py         # Client Brev wrapper
│   └── auth.py                # Sistema autenticazione
├── frontend/
│   ├── index.html             # UI principale
│   ├── styles.css             # Stili dark theme
│   └── app.js                 # Logica frontend
├── config/
│   ├── .env                   # Configurazione (NON committare!)
│   └── .env.example           # Template
├── generate_api_key.py        # Generatore chiavi
├── test_auth.py               # Test autenticazione
├── run_server.py              # Launcher semplice
├── start_client.py            # Launcher completo
├── README.md                  # Questo file
├── QUICK_START.md             # Guida rapida
└── TROUBLESHOOTING.md         # Risoluzione problemi
```

## Sicurezza

### Best Practices

1. **Non committare chiavi API su Git**:
   - File `.env` è già in `.gitignore`
   - Usa variabili d'ambiente in produzione

2. **Usa HTTPS in produzione**:
   - Configura reverse proxy (nginx/caddy)
   - Certificati SSL/TLS

3. **Limita CORS**:
   - Specifica domini consentiti
   - Non usare `allow_origins=["*"]` in produzione

4. **Abilita rate limiting**:
   - Protegge da abusi
   - Configurabile per chiave

5. **Ruota le chiavi regolarmente**:
   - Genera nuove chiavi periodicamente
   - Revoca chiavi compromesse

## FAQ

**Q: Come ottengo un'istanza Brev NVIDIA?**
A: Consulta la documentazione Brev su come avviare un'istanza GPU.

**Q: Posso usare il sistema senza istanza Brev?**
A: Sì per testare il frontend/backend, ma le richieste AI falliranno.

**Q: Come aggiungo nuovi endpoint?**
A: Modifica `client/backend/server.py` e aggiungi nuove route FastAPI.

**Q: Posso usare un altro frontend?**
A: Sì, l'API è completamente indipendente. Usa React, Vue, o qualsiasi framework.

**Q: Come debuggo errori?**
A: Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md) e controlla i log del server.

## Changelog

### v1.0.0 (2025-11-01)
- ✨ Sistema completo client-server
- ✨ Frontend web moderno
- ✨ Autenticazione Bearer token
- ✨ Rate limiting
- ✨ Multiple Brev instances support
- ✨ Swagger UI automatica
- ✨ Test suite completa
- 🐛 Fix Pydantic V2 warnings
- 📝 Documentazione completa

## Contribuire

Per segnalare bug o richiedere feature, apri una issue nel repository.

## Licenza

Questo progetto è parte del sistema MachineLearning.

## Link Utili

- [QUICK_START.md](QUICK_START.md) - Guida rapida
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Risoluzione problemi
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Brev Documentation](https://www.brev.dev/)
