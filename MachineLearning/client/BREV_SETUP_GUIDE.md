# Guida Completa Setup Brev NVIDIA

Questa guida spiega come configurare e connettere un'istanza Brev NVIDIA al sistema client.

## Indice

1. [Prerequisiti](#prerequisiti)
2. [Setup Iniziale Brev](#setup-iniziale-brev)
3. [Deploy NIM su Brev](#deploy-nim-su-brev)
4. [Connessione SSH](#connessione-ssh)
5. [Accesso API HTTP](#accesso-api-http)
6. [Configurazione Client](#configurazione-client)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisiti

### Account e Tool Necessari

1. **Account Brev**: Registrati su [https://console.brev.dev](https://console.brev.dev)
2. **NGC Account**: Ottieni API Key da [NGC Catalog](https://catalog.ngc.nvidia.com/)
3. **Brev CLI**: Installato localmente

### Installazione Brev CLI

```bash
# Linux/macOS
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/brevdev/brev-cli/main/bin/install-latest.sh)"

# Login
brev login
```

Il comando `brev login`:
- Crea la directory `~/.brev/`
- Genera le chiavi SSH in `~/.brev/brev.pem`
- Configura `~/.brev/ssh_config`
- Apre il browser per l'autenticazione

---

## Setup Iniziale Brev

### 1. Crea Istanza GPU

**Via Web Console**:
1. Vai su [https://console.brev.dev](https://console.brev.dev)
2. Clicca su **Instances** → **New +**
3. Seleziona **VM Mode**
4. Scegli GPU:
   - **L40S 48GB** (raccomandato per NIMs)
   - **A100 80GB** (per modelli più grandi)
5. Attendi status **"Running"**

**Via CLI**:
```bash
# Lista istanze disponibili
brev list

# Crea nuova istanza (esempio)
brev create --name my-nim-instance --gpu l40s
```

### 2. Verifica Istanza Attiva

```bash
# Lista istanze
brev list

# Output esempio:
# NAME              STATUS    GPU      IP
# my-nim-instance   Running   L40S     203.0.113.45
```

---

## Deploy NIM su Brev

### 1. Connetti all'Istanza via SSH

```bash
brev shell my-nim-instance
```

### 2. Verifica Docker e GPU

```bash
# Verifica accesso GPU
nvidia-smi

# Verifica Docker
docker --version
```

### 3. Configura NGC API Key

**Ottieni NGC API Key**:
1. Vai su [NGC](https://ngc.nvidia.com/)
2. Login → Setup → Keys/Secrets
3. Genera Personal API Key

**Configura sulla VM**:
```bash
# Imposta come variabile d'ambiente
export NGC_API_KEY="your_ngc_api_key_here"

# Rendi permanente (opzionale)
echo 'export NGC_API_KEY="your_ngc_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Autentica Docker con NGC

```bash
echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
```

### 5. Installa NGC CLI (Opzionale)

```bash
# Download NGC CLI
wget --content-disposition https://ngc.nvidia.com/downloads/ngccli_linux.zip && unzip ngccli_linux.zip

# Rendi eseguibile
chmod u+x ngc-cli/ngc

# Aggiungi al PATH
export PATH="$PATH:$(pwd)/ngc-cli"

# Configura
ngc config set
```

### 6. Deploy NIM Container

**Lista modelli disponibili**:
```bash
ngc registry image list --format_type csv nvcr.io/nim/*
```

**Deploy Llama3-8B-Instruct (esempio)**:
```bash
docker run -d \
  --name llama3-nim \
  --gpus all \
  --shm-size=16GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v "$HOME/.cache/nim:/opt/nim/.cache" \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama3-8b-instruct:latest
```

**Parametri spiegati**:
- `-d`: Esegui in background
- `--gpus all`: Accesso a tutte le GPU
- `--shm-size=16GB`: Memoria condivisa (importante!)
- `-e NGC_API_KEY`: Passa la chiave API
- `-v`: Volume per cache modelli (evita re-download)
- `-p 8000:8000`: Espone porta 8000

### 7. Verifica Container Attivo

```bash
# Controlla status
docker ps

# Visualizza log
docker logs llama3-nim

# Segui log in tempo reale
docker logs -f llama3-nim
```

Attendi che il modello sia completamente caricato (può richiedere 5-10 minuti al primo avvio).

---

## Connessione SSH

### Metodo 1: Brev CLI (Raccomandato)

```bash
# Connessione semplice
brev shell my-nim-instance

# Apri in VS Code
brev open my-nim-instance
```

### Metodo 2: SSH Diretto

```bash
# Trova IP istanza
brev list

# Connetti manualmente
ssh -i ~/.brev/brev.pem ubuntu@203.0.113.45

# O usa la config generata
ssh ubuntu@my-nim-instance
```

### Aggiorna IP dopo Restart

Se l'istanza viene fermata e riavviata, l'IP cambia:

```bash
# Aggiorna configurazione SSH
brev refresh

# Riconnetti
brev shell my-nim-instance
```

---

## Accesso API HTTP

### Opzione 1: Tunnel Brev (Accesso Pubblico)

**Setup Tunnel**:
1. Vai su [Brev Console](https://console.brev.dev)
2. Seleziona la tua istanza
3. Tab **"Access"** → **"Using Tunnels"**
4. Esponi porta **8000**
5. Copia il **Brev Tunnel Link**

Esempio URL tunnel:
```
https://abc123xyz.brev.sh
```

**Test Tunnel**:
```bash
# Health check
curl https://abc123xyz.brev.sh/v1/health/ready

# Lista modelli
curl https://abc123xyz.brev.sh/v1/models

# Genera testo
curl -X POST https://abc123xyz.brev.sh/v1/completions \
  -H 'Content-Type: application/json' \
  -H 'accept: application/json' \
  -d '{
    "model": "meta-llama3-8b-instruct",
    "prompt": "Once upon a time",
    "max_tokens": 225
  }'
```

**Nota**: Il tunnel richiede autenticazione browser al primo accesso (Cloudflare).

### Opzione 2: Port Forwarding (Accesso Locale)

**Setup Port Forward**:
```bash
# Forward porta 8000 remota → 8000 locale
brev port-forward my-nim-instance --port 8000:8000

# O modalità interattiva
brev port-forward my-nim-instance
```

**Test Local**:
```bash
# Health check
curl http://localhost:8000/v1/health/ready

# Genera testo
curl -X POST http://localhost:8000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "meta-llama3-8b-instruct",
    "prompt": "Create a sum function in Python",
    "max_tokens": 256
  }'
```

### Opzione 3: Accesso Diretto via IP

**Se hai IP pubblico statico**:
```bash
# Trova IP
brev list

# Testa
curl http://203.0.113.45:8000/v1/health/ready
```

**Nota**: Richiede che la porta 8000 sia aperta nel firewall.

---

## Configurazione Client

### 1. Determina URL di Accesso

Scegli uno dei metodi:

**A. Tunnel Pubblico**:
```
BREV_API_URL=https://abc123xyz.brev.sh
```

**B. Port Forwarding Locale**:
```
BREV_API_URL=http://localhost:8000
```

**C. IP Diretto**:
```
BREV_API_URL=http://203.0.113.45:8000
```

### 2. Configura File .env

```bash
# Naviga alla directory config
cd client/config

# Crea file .env (se non esiste)
cp .env.example .env

# Modifica con i tuoi dati
nano .env
```

**Contenuto `.env`**:
```bash
# URL dell'istanza Brev (scegli uno dei metodi sopra)
BREV_API_URL=https://your-tunnel-link.brev.sh

# NGC API Key (usata dal NIM container, opzionale per il client)
BREV_API_KEY=your_ngc_api_key

# Server API Key (protegge il backend)
SERVER_API_KEY=brev_abc123xyz  # genera con: python client/generate_api_key.py

# Opzionale
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=60
REQUEST_TIMEOUT=30
```

### 3. Genera Server API Key

```bash
# Dalla root del progetto
python client/generate_api_key.py

# Output:
# [OK] Generated API Key: brev_abc123xyz...
```

Copia la chiave generata nel file `.env` come `SERVER_API_KEY`.

### 4. Testa Configurazione

```bash
# Test connessione a Brev
curl $BREV_API_URL/v1/health/ready

# Se risponde con "healthy" → tutto OK!
```

---

## Testing

### 1. Test Backend Locale

```bash
# Avvia il server
cd c:\Users\arman\Documents\GitHub\PythonRepo\MachineLearning
python -m uvicorn client.backend.server:app --host 0.0.0.0 --port 5000 --reload
```

**In un altro terminale**:
```bash
# Health check backend
curl http://localhost:5000/health

# Test generazione codice (con autenticazione)
curl -X POST http://localhost:5000/api/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_SERVER_API_KEY' \
  -d '{
    "prompt": "Create a sum function in Python",
    "language": "python",
    "max_length": 256
  }'
```

### 2. Test Autenticazione

```bash
cd client
python test_auth.py
```

Output atteso:
```
[OK] Test senza autenticazione: 401 Unauthorized
[OK] Test con autenticazione: 200 OK
[OK] Test health check: 200 OK
```

### 3. Test Frontend

1. Avvia server: `python -m uvicorn client.backend.server:app --port 5000`
2. Apri browser: `http://localhost:5000`
3. Clicca su **Settings** (icona ingranaggio)
4. Configura:
   - **API URL**: `http://localhost:5000`
   - **API Key**: La tua `SERVER_API_KEY`
5. Salva e testa generazione codice

---

## Endpoints API Disponibili

### NIM Endpoints (Brev Instance)

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/v1/health/ready` | GET | Health check |
| `/v1/models` | GET | Lista modelli caricati |
| `/v1/completions` | POST | Generazione testo |
| `/v1/chat/completions` | POST | Chat completion |
| `/v1/metrics` | GET | Metriche Prometheus |

### Client Backend Endpoints

| Endpoint | Metodo | Auth | Descrizione |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/api/generate` | POST | Sì | Genera codice |
| `/api/security` | POST | Sì | Analisi security |
| `/api/batch` | POST | Sì | Batch generation |
| `/api/classify` | POST | Sì | Classificazione testo |
| `/api/model/info` | GET | Sì | Info modello |
| `/api/stats` | GET | Sì | Statistiche |
| `/docs` | GET | No | Swagger UI |

---

## Troubleshooting

### Problema: Container NIM non si avvia

**Verifica log**:
```bash
docker logs llama3-nim
```

**Soluzioni comuni**:
```bash
# 1. NGC API Key non valida
docker rm llama3-nim
export NGC_API_KEY="your_correct_key"
# Rilancia container

# 2. Memoria insufficiente
docker run ... --shm-size=16GB ...  # Assicurati di specificare!

# 3. GPU non accessibile
nvidia-smi  # Verifica GPU disponibile
docker run --gpus all ...  # Assicurati del flag --gpus
```

### Problema: Tunnel non risponde

**Verifica**:
1. Container NIM è in esecuzione: `docker ps`
2. Porta 8000 esposta correttamente
3. Autenticazione browser completata (visita URL in browser prima)

**Alternativa**: Usa port forwarding invece del tunnel.

### Problema: Port Forwarding fallisce

```bash
# Uccidi processi sulla porta 8000
lsof -ti:8000 | xargs kill -9  # Linux/Mac
netstat -ano | findstr :8000   # Windows

# Riavvia port forwarding
brev port-forward my-nim-instance --port 8000:8000
```

### Problema: IP cambiato dopo restart

```bash
# Aggiorna configurazione
brev refresh

# Verifica nuovo IP
brev list

# Aggiorna .env con nuovo IP (se usi accesso diretto)
```

### Problema: Backend non connette a Brev

**Verifica**:
```bash
# Test manuale connessione
curl $BREV_API_URL/v1/health/ready

# Se fallisce, problema di rete/configurazione
# Se funziona, problema nel backend
```

**Controlla `.env`**:
- URL corretto senza slash finale
- Porta corretta (8000 per NIM)
- Protocollo corretto (http/https)

### Problema: Autenticazione fallisce

```bash
# Rigenera chiave
python client/generate_api_key.py

# Aggiorna .env
nano client/config/.env

# Aggiorna localStorage nel browser
# Settings → Inserisci nuova chiave → Save
```

---

## Best Practices

### 1. Sicurezza

- **Mai committare `.env`** su Git (già in `.gitignore`)
- **Ruota NGC API Key** periodicamente
- **Usa HTTPS** per tunnel pubblici
- **Limita accesso** con rate limiting

### 2. Performance

- **Usa cache volume** per modelli: `-v "$HOME/.cache/nim:/opt/nim/.cache"`
- **Monitora GPU**: `nvidia-smi -l 1`
- **Scala istanze** per carico elevato

### 3. Costi

- **Stoppa istanze** quando non in uso: `brev stop my-nim-instance`
- **Riavvia** quando serve: `brev start my-nim-instance`
- **Elimina** istanze inutilizzate

### 4. Monitoring

```bash
# Log container in tempo reale
docker logs -f llama3-nim

# Metriche GPU
nvidia-smi dmon

# Metriche NIM (Prometheus)
curl http://localhost:8000/v1/metrics
```

---

## Esempi Completi

### Esempio 1: Setup Completo da Zero

```bash
# 1. Login Brev
brev login

# 2. Crea istanza
# (via console web)

# 3. Connetti
brev shell my-nim-instance

# 4. Setup NGC e Docker
export NGC_API_KEY="nvapi-xxx"
echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin

# 5. Deploy NIM
docker run -d --name llama3-nim --gpus all --shm-size=16GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v "$HOME/.cache/nim:/opt/nim/.cache" \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama3-8b-instruct:latest

# 6. Attendi caricamento (5-10 min)
docker logs -f llama3-nim

# 7. Setup tunnel (via console)
# Copia tunnel URL

# 8. Exit da SSH
exit

# 9. Configura client locale
cd client/config
cp .env.example .env
# Modifica .env con tunnel URL

# 10. Test
python ../test_auth.py

# 11. Avvia backend
cd ../..
python -m uvicorn client.backend.server:app --port 5000
```

### Esempio 2: Deploy Multipli Modelli

```bash
# Llama3 8B (porta 8000)
docker run -d --name llama3-8b --gpus '"device=0"' --shm-size=16GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v "$HOME/.cache/llama3-8b:/opt/nim/.cache" \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama3-8b-instruct:latest

# Llama3 70B (porta 8001, richiede più GPU)
docker run -d --name llama3-70b --gpus '"device=1,2,3"' --shm-size=32GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v "$HOME/.cache/llama3-70b:/opt/nim/.cache" \
  -p 8001:8000 \
  nvcr.io/nim/meta/llama3-70b-instruct:latest
```

**Configura client per multiple istanze**:
```bash
# In .env
BREV_INSTANCES=https://instance1.brev.sh,https://instance2.brev.sh
```

Il client distribuisce automaticamente le richieste (round-robin).

---

## Link Utili

- **Brev Console**: https://console.brev.dev
- **Brev Docs**: https://docs.nvidia.com/brev/
- **NGC Catalog**: https://catalog.ngc.nvidia.com/
- **NIM Documentation**: https://docs.nvidia.com/nim/
- **Docker Hub (NGC)**: https://ngc.nvidia.com/catalog/containers

---

## Supporto

Per problemi:
1. Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Verifica [Brev Docs](https://docs.nvidia.com/brev/)
3. Controlla log container: `docker logs llama3-nim`
4. Verifica GPU: `nvidia-smi`

---

**Versione**: 1.0.0
**Ultimo Aggiornamento**: 2025-11-01
**Autore**: Sistema MachineLearning Client
