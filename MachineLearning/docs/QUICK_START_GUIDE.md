# 🚀 QUICK START - 5 MINUTI

Inizia subito ad estrarre funzioni da repository GitHub in 5 minuti!

---

## ✅ STEP 1: Verifica Setup (30 secondi)

```powershell
# Attiva virtual environment
.\.venv\Scripts\activate

# Verifica Python e dipendenze
python --version                           # Deve essere 3.8+
pip show tree-sitter boto3 GitPython      # Devono essere installati
```

**Se manca qualcosa:**
```powershell
pip install -r requirements.txt
```

---

## 🎯 STEP 2: Prima Estrazione (2 minuti)

### Opzione A: Interface Interattiva (PIÙ SEMPLICE)

```powershell
python main.py
```

Poi:
1. Scegli `1` (Process GitHub Repository)
2. Inserisci URL: `https://github.com/psf/requests`
3. Aspetta... ✅ Fatto!

### Opzione B: Script Rapido

```powershell
python example_single_repo.py
```

Modifica lo script per cambiare repository:
```python
# In example_single_repo.py, linea ~35
repo_url = "https://github.com/axios/axios"  # Cambia qui
```

---

## 📊 STEP 3: Vedi Risultati (1 minuto)

```powershell
# Vai alla cartella output
cd datasets\local_backup\code_generation

# Lista file creati
dir *.json

# Apri un file per vedere le funzioni
notepad requests_*.json
```

**Formato output:**
```json
[
  {
    "func_name": "get",
    "language": "python",
    "signature": "def get(url, params=None):",
    "body": "return request('get', url, params=params)",
    "input": "Write a function...",
    "output": "def get..."
  }
]
```

---

## 🚀 STEP 4: Batch Processing (1 minuto setup)

```powershell
# 1. Crea lista repository
"https://github.com/psf/requests" > repo_list.txt
"https://github.com/axios/axios" >> repo_list.txt
"https://github.com/spf13/cobra" >> repo_list.txt

# 2. Esegui batch
python bulk_processor.py --source github --repos repo_list.txt
```

---

## 📈 STEP 5: Analizza Dati (30 secondi)

```powershell
python example_analyze_output.py
```

Vedrai:
- ✅ Quante funzioni estratte
- ✅ Per ogni linguaggio
- ✅ Statistiche di qualità
- ✅ Esempi di funzioni
- ✅ Consigli per migliorare

---

## 💡 COMANDI ESSENZIALI

```powershell
# Estrazione singola
python main.py

# Batch processing
python bulk_processor.py --source github --repos repo_list.txt

# Solo un linguaggio
python bulk_processor.py --source github --repos repo_list.txt --language python

# Analisi risultati
python example_analyze_output.py

# Test parser specifico
cd debug
python test_python_extraction.py
```

---

## 🎯 ESEMPI RAPIDI

### Esempio 1: Repository Python
```powershell
python main.py
# URL: https://github.com/django/django
# Risultato: ~1000+ funzioni Python
```

### Esempio 2: Repository JavaScript
```powershell
python main.py
# URL: https://github.com/lodash/lodash
# Risultato: ~500+ funzioni JavaScript
```

### Esempio 3: Multi-Linguaggio
```powershell
python main.py
# URL: https://github.com/microsoft/vscode
# Risultato: Mix di TypeScript, JavaScript, Python
```

---

## 🐛 PROBLEMI COMUNI

### "No functions extracted"
```powershell
# Debug il linguaggio specifico
cd debug
python test_<language>_extraction.py
```

### "Repository not found"
```powershell
# Verifica URL sia corretto
# Deve essere: https://github.com/owner/repo
```

### "Rate limit exceeded"
```powershell
# Aggiungi token in .env
echo "GITHUB_TOKEN=ghp_your_token_here" > .env
```

---

## 📚 PROSSIMI PASSI

1. **Leggi la guida completa**
   ```powershell
   notepad USAGE_GUIDE.md
   ```

2. **Esplora gli esempi**
   - `example_single_repo.py` - Singolo repository
   - `example_bulk_processing.py` - Batch processing
   - `example_analyze_output.py` - Analisi risultati

3. **Configura cloud storage** (opzionale)
   ```powershell
   # Aggiungi in .env
   DO_SPACES_KEY=your_key
   DO_SPACES_SECRET=your_secret
   ```

4. **Personalizza estrazione**
   ```python
   # In config.py
   MIN_FUNCTION_LENGTH = 20    # Lunghezza minima
   BATCH_SIZE = 200            # Funzioni per batch
   ```

---

## 🎉 FATTO!

Ora hai estratto le tue prime funzioni!

**Risultati in:** `datasets/local_backup/code_generation/`

**Logs in:** `logs/`

**Prossimo comando:**
```powershell
python example_analyze_output.py  # Vedi statistiche
```

---

**Supporto:** Vedi `USAGE_GUIDE.md` per dettagli completi  
**Troubleshooting:** Vedi `debug/README.md`  
**Examples:** Esplora `example_*.py` files
