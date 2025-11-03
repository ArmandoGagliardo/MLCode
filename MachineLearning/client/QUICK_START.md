# Guida Rapida - Client Brev NVIDIA

## Avvio Rapido

### 1. Configurazione Iniziale

Crea il file di configurazione:
```bash
# Copia il template
cp client/config/.env.example client/config/.env

# Modifica con i tuoi dati
# BREV_API_URL=http://your-brev-instance:8000
# SERVER_API_KEY=your-secure-key
```

### 2. Genera una API Key Sicura

```bash
python client/generate_api_key.py
```

Copia la chiave generata nel file `.env` come `SERVER_API_KEY`.

### 3. Avvia il Server

**Opzione A - Comando Diretto (Raccomandato)**:
```bash
cd c:\Users\arman\Documents\GitHub\PythonRepo\MachineLearning
python -m uvicorn client.backend.server:app --host 0.0.0.0 --port 5000 --reload
```

**Opzione B - Script Launcher**:
```bash
python client/run_server.py
```

**Opzione C - Launcher Completo**:
```bash
python client/start_client.py
```

### 4. Apri il Browser

Vai su: **http://localhost:5000**

## Test Senza Istanza Brev

Se non hai ancora un'istanza Brev attiva, puoi comunque:

1. **Verificare il server funzioni**:
```bash
curl http://localhost:5000/health
```

2. **Testare l'autenticazione**:
```bash
cd client
python test_auth.py
```

Il server risponderà con un errore di connessione all'istanza Brev, ma questo è normale.

## Struttura del Sistema

```
client/
├── backend/               # FastAPI server
│   ├── server.py         # REST API endpoints
│   ├── brev_client.py    # Client per Brev
│   └── auth.py           # Sistema autenticazione
├── frontend/             # Web UI
│   ├── index.html        # Interfaccia utente
│   ├── styles.css        # Stili
│   └── app.js            # Logica frontend
├── config/
│   └── .env              # Configurazione (da creare)
├── generate_api_key.py   # Generatore chiavi
├── test_auth.py          # Test autenticazione
├── run_server.py         # Launcher semplice
└── start_client.py       # Launcher completo
```

## Autenticazione a Due Livelli

### 1. SERVER_API_KEY
- **Scopo**: Protegge il backend da client non autorizzati
- **Dove**: Nel file `client/config/.env`
- **Usato da**: Frontend per autenticarsi al backend

### 2. BREV_API_KEY
- **Scopo**: Autentica il backend verso l'istanza Brev
- **Dove**: Nel file `client/config/.env`
- **Usato da**: Backend per comunicare con Brev

## Uso dell'API

### Esempio con curl

**1. Generazione Codice**:
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-server-api-key" \
  -d '{
    "prompt": "Create a sum function in Python",
    "language": "python",
    "max_length": 256
  }'
```

**2. Analisi Security**:
```bash
curl -X POST http://localhost:5000/api/security \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-server-api-key" \
  -d '{
    "code": "def execute(cmd):\n    import os\n    os.system(cmd)",
    "language": "python",
    "scan_type": "quick"
  }'
```

**3. Batch Generation**:
```bash
curl -X POST http://localhost:5000/api/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-server-api-key" \
  -d '{
    "prompts": ["Create sum function", "Create multiply function"],
    "language": "python"
  }'
```

## Risoluzione Problemi Comuni

### Server non si avvia
```bash
# Verifica che la porta 5000 sia libera
netstat -ano | findstr :5000

# Se occupata, usa un'altra porta
python -m uvicorn client.backend.server:app --port 5001
```

### Errore di connessione a Brev
Normale se non hai un'istanza Brev attiva. Il server funziona comunque.

Per configurare Brev:
1. Avvia un'istanza Brev NVIDIA
2. Aggiorna `BREV_API_URL` nel file `.env`
3. Riavvia il server

### Errore di autenticazione
Verifica che:
1. Il file `.env` esista in `client/config/`
2. `SERVER_API_KEY` sia configurato correttamente
3. Il frontend usi la stessa chiave (salvata in localStorage)

### ImportError
Esegui sempre dalla root del progetto:
```bash
cd c:\Users\arman\Documents\GitHub\PythonRepo\MachineLearning
python -m uvicorn client.backend.server:app --port 5000
```

## Features del Sistema

### Rate Limiting
- 60 richieste/minuto per chiave API (default)
- 100 richieste/minuto per chiave admin
- Configurabile in `auth.py`

### Permissions
- `all`: Accesso completo
- `generate`: Solo generazione codice
- `security`: Solo analisi security
- `classify`: Solo classificazione testo

### Statistics
Endpoint per statistiche d'uso:
```bash
curl http://localhost:5000/api/stats \
  -H "Authorization: Bearer your-api-key"
```

## Prossimi Passi

1. **Configura l'istanza Brev**: Aggiorna `BREV_API_URL` con l'URL reale
2. **Personalizza il frontend**: Modifica `client/frontend/` per le tue esigenze
3. **Aggiungi nuove features**: Estendi `server.py` con nuovi endpoint
4. **Deploy in produzione**: Usa `gunicorn` o `docker` per il deployment

## Link Utili

- **API Docs**: http://localhost:5000/docs (Swagger UI automatico)
- **Health Check**: http://localhost:5000/health
- **Alternative API Docs**: http://localhost:5000/redoc

## Supporto

Per problemi, consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
