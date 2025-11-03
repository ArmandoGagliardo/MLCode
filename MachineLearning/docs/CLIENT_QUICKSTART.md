# Brev Client - Quick Start Guide

Guida rapida per iniziare a usare il client Brev in 5 minuti.

## 🚀 Setup in 3 Passi

### 1. Installa Dipendenze

```bash
cd client
pip install -r requirements.txt
```

### 2. Configura

```bash
cp config/.env.example config/.env
```

Modifica `config/.env`:
```bash
BREV_API_URL=https://your-instance.brev.dev
SERVER_API_KEY=your-secure-key
```

### 3. Avvia

```bash
python start_client.py
```

Il browser si aprirà automaticamente con l'interfaccia web!

## 💻 Utilizzo Rapido

### Code Generation

**Input:**
```
Crea una funzione somma in Python che accetta due numeri
```

**Output:**
```python
def sum_numbers(a, b):
    return a + b
```

### Security Analysis

**Input:**
```python
def execute(cmd):
    import os
    os.system(cmd)
```

**Output:**
```
❌ CRITICAL: Command Injection
Line 3: os.system(cmd)
Fix: Usa subprocess.run() con lista di argomenti
```

## 🔧 Configurazione UI

1. Clicca su ⚙️ Settings
2. Inserisci:
   - **API URL**: `http://localhost:5000`
   - **API Key**: (la stessa di `SERVER_API_KEY` in `.env`)
3. Salva

## 📱 Screenshot

### Code Generation
```
┌─────────────────────────────────────────┐
│ 🚀 Brev NVIDIA Client                   │
│ Code Generation & Security Analysis     │
│                                         │
│ ● Connected                             │
└─────────────────────────────────────────┘

┌─── Code Generation ───────────────────┐
│                                       │
│ Prompt:                               │
│ ┌───────────────────────────────────┐ │
│ │ Crea una funzione somma in Python │ │
│ │ che accetta due numeri            │ │
│ └───────────────────────────────────┘ │
│                                       │
│ Language: [Python ▼]  Max Length: 512 │
│ Temperature: ▮▯▯▯▯▯▯▯▯▯ 0.7          │
│                                       │
│ [ ⚡ Generate Code ]                  │
└───────────────────────────────────────┘
```

## 🛠️ Comandi Utili

### Avvio Manuale Backend

```bash
cd client/backend
uvicorn server:app --reload --port 5000
```

### Aprire Frontend

```bash
cd client/frontend
python -m http.server 8080
# Vai su http://localhost:8080
```

### Test API

```bash
# Health check
curl http://localhost:5000/health

# Generate code
curl -X POST http://localhost:5000/api/generate \
  -H "Authorization: Bearer dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a sum function",
    "language": "python"
  }'
```

## 🔥 Features

- ✅ Code Generation (Python, JavaScript, Java, C++, Go)
- ✅ Security Analysis (Pattern-based vulnerability detection)
- ✅ Batch Generation (Multiple prompts at once)
- ✅ Real-time Status Monitoring
- ✅ Copy to Clipboard
- ✅ Responsive UI
- ✅ Dark Mode
- ✅ API Authentication

## 🐛 Troubleshooting

### Backend non si avvia

```bash
# Verifica dipendenze
pip install -r client/requirements.txt

# Verifica porta libera
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows
```

### Frontend non si connette

1. Verifica backend attivo: `http://localhost:5000/health`
2. Controlla API key in Settings
3. Verifica CORS in `server.py`

### Istanza Brev non risponde

1. Verifica URL in `.env`
2. Controlla API key Brev
3. Verifica connessione internet

## 📚 Prossimi Passi

1. **Personalizza UI**: Modifica `frontend/styles.css`
2. **Aggiungi funzionalità**: Estendi `brev_client.py`
3. **Deploy**: Vedi `client/README.md` sezione Deployment
4. **Monitoring**: Aggiungi logging e metriche

## 🔐 Sicurezza

⚠️ **Importante in produzione:**

1. Cambia `SERVER_API_KEY` con una chiave sicura:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. Abilita HTTPS
3. Configura CORS correttamente
4. Abilita rate limiting
5. Non committare file `.env`

## 💡 Tips

- **Performance**: Usa multiple istanze Brev per load balancing
- **Cache**: Abilita cache per richieste ripetute
- **Logging**: Controlla `client.log` per debug
- **API Docs**: Vai su `http://localhost:5000/docs`

## 📞 Supporto

- **README completo**: `client/README.md`
- **Logs**: `client.log`
- **API Docs**: `http://localhost:5000/docs`

## 🎉 Pronto!

Hai completato il setup! Ora puoi:

1. Generare codice con prompt in linguaggio naturale
2. Analizzare codice per vulnerabilità
3. Processare batch di richieste

**Enjoy coding!** 🚀
