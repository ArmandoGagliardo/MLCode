# 🎯 GUIDA ALL'USO DEL SOFTWARE

Guida completa passo-passo per usare il sistema di estrazione codice multi-linguaggio.

---

## 📋 PREREQUISITI

✅ Python 3.8+ installato
✅ Virtual environment attivo (.venv)
✅ Dipendenze installate (`pip install -r requirements.txt`)

---

## 🚀 METODI DI UTILIZZO

### Metodo 1: Interface Interattiva (Più Semplice)

```bash
# Attiva ambiente virtuale
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Linux/Mac

# Avvia il programma
python main.py
```

**Cosa fa:**
- Mostra un menu interattivo
- Scegli l'opzione "Process GitHub Repository"
- Inserisci l'URL del repository
- Il sistema scarica, analizza ed estrae automaticamente

**Esempio:**
```
1. Process GitHub Repository
2. Exit

Scelta: 1
Repository URL: https://github.com/axios/axios
```

---

### Metodo 2: Bulk Processing (Per Molti Repository)

```bash
# 1. Crea un file con lista di repository
# File: repo_list.txt
https://github.com/psf/requests
https://github.com/axios/axios
https://github.com/spf13/cobra

# 2. Esegui bulk processor
python bulk_processor.py --source github --repos repo_list.txt
```

**Opzioni avanzate:**
```bash
# Con linguaggio specifico
python bulk_processor.py --source github --repos repo_list.txt --language python

# Con batch size custom
python bulk_processor.py --source github --repos repo_list.txt --batch_size 200

# Da directory locale
python bulk_processor.py --source local --path C:\path\to\code
```

---

### Metodo 3: Script Python Custom

```python
from github_repo_processor import GitHubRepoProcessor

# Crea processor
processor = GitHubRepoProcessor(
    cloud_save=False,    # True per upload automatico al cloud
    batch_size=100       # Funzioni per batch
)

# Processa singolo repository
result = processor.process_repository("https://github.com/user/repo")

print(f"Estratte {result['functions_extracted']} funzioni!")
```

---

## 📁 DOVE TROVARE I RISULTATI

### Output Locale
```
datasets/local_backup/code_generation/
├── requests_20251102_165542_141.json    # 141 funzioni
├── axios_20251102_154320_256.json       # 256 funzioni
└── ...
```

### Formato File JSON
Ogni file contiene array di funzioni:
```json
[
  {
    "task_type": "code_generation",
    "language": "python",
    "func_name": "get",
    "signature": "def get(url, params=None, **kwargs):",
    "body": "{\n    return request('get', url, params=params, **kwargs)\n}",
    "input": "Write a python function called 'get'...",
    "output": "def get(url, params=None, **kwargs):\n    return request('get', url, params=params, **kwargs)"
  }
]
```

### Log Files
```
logs/
├── processing.log           # Log principale
└── github_processor.log     # Log specifico GitHub
```

---

## 🎛️ CONFIGURAZIONE

### File .env (Opzionale)
```env
# GitHub Token (per rate limit più alto)
GITHUB_TOKEN=ghp_your_token_here

# Cloud Storage (se vuoi upload automatico)
DO_SPACES_KEY=your_key
DO_SPACES_SECRET=your_secret
DO_SPACES_REGION=nyc3
DO_SPACES_BUCKET=your-bucket
```

### Configurazione Python (config.py)
```python
# Modifica parametri in config.py
MAX_FILE_SIZE_MB = 10
MIN_FUNCTION_LENGTH = 10
BATCH_SIZE = 100
```

---

## 🔍 LINGUAGGI SUPPORTATI

| Linguaggio | Estensioni | Esempio Repository |
|------------|-----------|-------------------|
| Python     | .py       | psf/requests |
| JavaScript | .js       | axios/axios |
| Go         | .go       | spf13/cobra |
| Rust       | .rs       | clap-rs/clap |
| Java       | .java     | google/gson |
| C++        | .cpp, .h  | nlohmann/json |
| Ruby       | .rb       | rails/rails |

---

## 📊 ESEMPI PRATICI

### Esempio 1: Estrarre da Repository Popolare
```bash
python main.py
# Scegli opzione 1
# URL: https://github.com/django/django
# Aspetta... Estrazione in corso...
# Risultato: 1000+ funzioni estratte!
```

### Esempio 2: Batch Processing di Progetti
```bash
# Crea repo_list.txt con i tuoi progetti
echo "https://github.com/myorg/project1" > repo_list.txt
echo "https://github.com/myorg/project2" >> repo_list.txt
echo "https://github.com/myorg/project3" >> repo_list.txt

# Esegui batch
python bulk_processor.py --source github --repos repo_list.txt
```

### Esempio 3: Estrarre Solo Python
```bash
python bulk_processor.py \
  --source github \
  --repos repo_list.txt \
  --language python
```

### Esempio 4: Codice Locale
```bash
# Analizza codice sul tuo computer
python bulk_processor.py \
  --source local \
  --path "C:\MyProjects\AwesomeApp"
```

---

## ⚡ FUNZIONALITÀ AVANZATE

### Stop Graceful
- Premi **CTRL+C** durante l'esecuzione
- Il sistema completa il file corrente e salva il progresso
- Riprendi più tardi senza perdere dati

### Quality Filtering
Il sistema filtra automaticamente:
- ✅ Funzioni valide con firma completa
- ✅ Codice con complessità sufficiente
- ✅ Syntax corretto per ogni linguaggio
- ❌ Boilerplate e codice triviale
- ❌ Duplicati (hash-based)

### Progress Monitoring
```
Processing requests: 57%|#####7| 12/21 [00:32<00:28, 3.2s/file]
```
- Barra di progresso in tempo reale
- Tempo stimato rimanente
- Conteggio funzioni estratte

---

## 🐛 TROUBLESHOOTING

### Problema: "No functions extracted"
**Soluzione:**
```bash
# Test il parser specifico
cd debug
python test_<language>_extraction.py  # es: test_java_extraction.py
```

### Problema: Rate limit GitHub
**Soluzione:**
```bash
# Aggiungi token nel .env
GITHUB_TOKEN=ghp_your_token_here
```

### Problema: Memory error
**Soluzione:**
```bash
# Riduci batch size
python bulk_processor.py --source github --repos repo_list.txt --batch_size 50
```

### Problema: Parser error
**Soluzione:**
```bash
# Debug AST
cd debug
python debug_<language>_ast.py  # es: debug_rust_ast.py
```

---

## 📈 MONITORAGGIO

### Contare Funzioni Estratte
```powershell
# Windows
Get-ChildItem datasets\local_backup\code_generation\*.json | 
  ForEach-Object { 
    $content = Get-Content $_.FullName | ConvertFrom-Json
    $content.Count 
  } | Measure-Object -Sum | Select-Object Sum
```

### Vedere Statistiche
```bash
# Guarda i log
Get-Content logs\processing.log -Tail 50
```

### Verificare Duplicati
```bash
# Cache duplicati
Get-Content datasets\duplicates_cache.json | ConvertFrom-Json
```

---

## 🎓 WORKFLOW CONSIGLIATO

1. **Test su Repository Piccolo**
   ```bash
   python main.py
   # URL: https://github.com/psf/black (piccolo e veloce)
   ```

2. **Verifica Output**
   ```bash
   # Controlla datasets/local_backup/code_generation/
   # Apri un JSON e verifica la qualità
   ```

3. **Setup Batch List**
   ```bash
   # Crea repo_list.txt con i tuoi repository target
   ```

4. **Esegui Batch Processing**
   ```bash
   python bulk_processor.py --source github --repos repo_list.txt
   ```

5. **Monitora Progress**
   - Guarda la progress bar
   - Controlla i log in tempo reale
   - CTRL+C per stop se necessario

6. **Analizza Risultati**
   ```bash
   # Conta funzioni
   # Verifica qualità
   # Upload al cloud (se configurato)
   ```

---

## 🔐 BEST PRACTICES

1. **Usa Virtual Environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Non Committare .env**
   ```bash
   # Verifica .gitignore contiene:
   .env
   *.log
   datasets/
   ```

3. **Backup Regolare**
   ```bash
   # Copia datasets/ periodicamente
   # O usa cloud_save=True
   ```

4. **Test Prima di Batch**
   ```bash
   # Sempre test su 1 repo prima di processare 100
   ```

5. **Monitora Memoria**
   ```bash
   # Usa batch_size appropriato per la tua RAM
   # Batch size più basso = meno memoria, più lento
   ```

---

## 💡 TIPS & TRICKS

- 🚀 Usa `--language` per filtrare linguaggio specifico
- 📊 Controlla `logs/` per debug dettagliato
- ⚡ Premi CTRL+C per stop graceful
- 🔄 Il checkpoint riprende da dove hai lasciato
- 📦 Batch size di 100 è ottimale per la maggior parte dei casi
- 🌐 cloud_save=True per backup automatico
- 🔍 debug/ folder ha test per ogni linguaggio

---

## 📞 SUPPORTO

- 📖 Leggi `README.md` per info dettagliate
- 🐛 Vedi `debug/README.md` per troubleshooting
- 📚 Consulta `docs/` per documentazione tecnica
- ❓ Apri issue su GitHub per problemi

---

**Versione:** 1.0 Production Ready  
**Ultimo Aggiornamento:** 2 Novembre 2025  
**Linguaggi Supportati:** 7/7 (100%)  
**Status:** ✅ Completamente Funzionante
