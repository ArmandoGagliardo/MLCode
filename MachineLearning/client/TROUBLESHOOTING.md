# Troubleshooting Guide - Brev Client

Soluzioni ai problemi comuni.

## 🔴 Import Errors

### Errore: `ImportError: attempted relative import with no known parent package`

**Causa**: Stai eseguendo il file direttamente invece che come modulo.

**Soluzione 1** - Usa lo script di avvio:
```bash
# Dalla root del progetto MachineLearning
python client/run_server.py
```

**Soluzione 2** - Usa uvicorn con path completo:
```bash
# Dalla root del progetto MachineLearning
python -m uvicorn client.backend.server:app --reload --port 5000
```

**Soluzione 3** - Aggiungi il path:
```bash
# Dalla root del progetto MachineLearning
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn client.backend.server:app --reload --port 5000
```

### Errore: `ModuleNotFoundError: No module named 'client'`

**Causa**: Stai eseguendo da directory sbagliata.

**Soluzione**:
```bash
# Assicurati di essere nella root del progetto
cd /path/to/MachineLearning

# Verifica struttura
ls client/
# Dovresti vedere: backend/ frontend/ config/ ...

# Avvia server
python client/run_server.py
```

### Errore: `ModuleNotFoundError: No module named 'fastapi'`

**Causa**: Dipendenze non installate.

**Soluzione**:
```bash
pip install -r client/requirements.txt
```

---

## 🔴 Server Errors

### Errore: `Address already in use`

**Causa**: Porta già occupata da altro processo.

**Soluzione 1** - Usa porta diversa:
```bash
python client/run_server.py --port 8000
```

**Soluzione 2** - Termina processo esistente:

**Windows**:
```bash
# Trova processo
netstat -ano | findstr :5000

# Termina processo (sostituisci PID)
taskkill /PID <PID> /F
```

**Linux/Mac**:
```bash
# Trova processo
lsof -i :5000

# Termina processo
kill -9 <PID>
```

### Server si avvia ma non risponde

**Causa**: Firewall o configurazione rete.

**Soluzione**:
```bash
# Test locale
curl http://localhost:5000/health

# Se non funziona, verifica firewall
# Windows: Pannello di Controllo → Firewall
# Linux: sudo ufw allow 5000
```

---

## 🔴 Authentication Errors

### Errore: `401 Unauthorized`

**Causa**: API key mancante o errata.

**Soluzione 1** - Verifica .env:
```bash
cat client/config/.env
# Deve contenere:
# SERVER_API_KEY=your_key_here
```

**Soluzione 2** - Configura UI:
1. Apri interfaccia web
2. Clicca ⚙️ Settings
3. Inserisci API Key (stessa di .env)
4. Salva

**Soluzione 3** - Verifica chiamata API:
```bash
# Deve includere header Authorization
curl -X POST http://localhost:5000/api/generate \
  -H "Authorization: Bearer your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","language":"python"}'
```

### Errore: `403 Forbidden`

**Causa**: Permessi insufficienti.

**Soluzione**: Verifica permessi API key in `client/backend/auth.py`

---

## 🔴 Frontend Errors

### Pagina bianca / non carica

**Causa**: JavaScript error o percorso file errato.

**Soluzione**:
```bash
# Apri console browser (F12)
# Controlla errori JavaScript

# Verifica percorso file
ls client/frontend/
# Deve contenere: index.html styles.css app.js

# Apri file correttamente
# File URI deve puntare a index.html
file:///path/to/MachineLearning/client/frontend/index.html
```

### Settings non si salvano

**Causa**: localStorage bloccato.

**Soluzione**:
1. Verifica permessi browser per localStorage
2. Prova in modalità incognito
3. Usa server HTTP invece di file://

```bash
# Avvia server HTTP
cd client/frontend
python -m http.server 8080

# Apri browser
http://localhost:8080
```

### CORS Error

**Causa**: Richieste cross-origin bloccate.

**Soluzione** - Modifica `client/backend/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In dev accetta tutti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Per produzione, specifica domini:
```python
allow_origins=[
    "http://localhost:8080",
    "https://yourdomain.com"
]
```

---

## 🔴 Connection Errors

### Frontend non si connette al backend

**Checklist**:
```bash
# 1. Verifica server attivo
curl http://localhost:5000/health

# 2. Verifica porta corretta in Settings
#    API URL: http://localhost:5000

# 3. Verifica firewall non blocca

# 4. Controlla console browser (F12)
#    Cerca errori di rete
```

### Brev instance timeout

**Causa**: Istanza non raggiungibile o lenta.

**Soluzione**:
```bash
# Verifica URL in .env
cat client/config/.env
# BREV_API_URL=https://your-instance.brev.dev

# Test connessione
curl https://your-instance.brev.dev/health

# Aumenta timeout in brev_client.py
# timeout=60  # Aumenta da 30 a 60 secondi
```

---

## 🔴 Configuration Errors

### File .env non caricato

**Causa**: Path errato o sintassi errata.

**Soluzione**:
```bash
# Verifica file esiste
ls client/config/.env

# Verifica sintassi (no spazi attorno a =)
# ✓ Corretto:
SERVER_API_KEY=abc123

# ✗ Errato:
SERVER_API_KEY = abc123
```

### Variabili ambiente non impostate

**Soluzione manuale**:
```bash
# Windows
set SERVER_API_KEY=your_key
set BREV_API_URL=https://your-instance.brev.dev

# Linux/Mac
export SERVER_API_KEY=your_key
export BREV_API_URL=https://your-instance.brev.dev

# Poi avvia server
python client/run_server.py
```

---

## 🔴 Runtime Errors

### Errore: `KeyError: 'code'`

**Causa**: Risposta da Brev non ha formato atteso.

**Soluzione** - Modifica `client/frontend/app.js`:
```javascript
// Prima:
document.getElementById('generatedCode').textContent = result.data.code;

// Dopo (con fallback):
const code = result.data.code ||
             result.data.generated_text ||
             JSON.stringify(result.data, null, 2);
document.getElementById('generatedCode').textContent = code;
```

### Errore: `Connection refused`

**Causa**: Server non in ascolto o porta errata.

**Soluzione**:
```bash
# Verifica server running
ps aux | grep uvicorn  # Linux/Mac
tasklist | findstr python  # Windows

# Riavvia server
python client/run_server.py

# Verifica porta
netstat -tuln | grep 5000  # Linux
netstat -ano | findstr 5000  # Windows
```

---

## 🔧 Quick Fixes

### Reset completo

```bash
# 1. Stop tutti i processi
pkill -f uvicorn  # Linux/Mac
taskkill /F /IM python.exe  # Windows

# 2. Reinstalla dipendenze
pip install -r client/requirements.txt --force-reinstall

# 3. Reset configurazione
rm client/config/.env
cp client/config/.env.example client/config/.env
# Modifica .env con i tuoi valori

# 4. Avvia
python client/run_server.py
```

### Verifica installazione

```bash
# Test completo
python -c "
import fastapi
import uvicorn
import requests
print('✓ Tutte le dipendenze installate')
"
```

### Debug mode

Abilita logging dettagliato in `client/backend/server.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Cambia da INFO a DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 📞 Supporto

Se il problema persiste:

1. **Controlla logs**:
   ```bash
   tail -f client.log
   ```

2. **Testa con curl**:
   ```bash
   curl -v http://localhost:5000/health
   ```

3. **Verifica versioni**:
   ```bash
   python --version  # >= 3.8
   pip list | grep fastapi  # >= 0.104
   ```

4. **Controlla documentazione**:
   - `client/README.md`
   - `CLIENT_QUICKSTART.md`
   - API Docs: `http://localhost:5000/docs`

---

## 🐛 Report Bug

Se trovi un bug, include:
- Sistema operativo
- Versione Python
- Output comando esatto
- Stack trace completo
- File .env (senza chiavi sensibili)
