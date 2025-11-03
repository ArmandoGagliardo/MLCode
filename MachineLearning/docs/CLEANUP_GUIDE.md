# 🧹 Sistema di Cleanup Automatico

Sistema completo per gestire la pulizia dei repository temporanei e liberare spazio disco.

## 📋 File Disponibili

### 1. `cleanup_temp_repos.py` - Pulizia Manuale
Script per pulizia manuale dei repository temporanei.

```bash
# Modalità interattiva (chiede conferma)
python cleanup_temp_repos.py

# Mostra cosa verrebbe eliminato senza eliminare
python cleanup_temp_repos.py --dry-run

# Elimina solo file più vecchi di 24 ore
python cleanup_temp_repos.py --old-only --auto

# Pulizia completa senza conferma
python cleanup_temp_repos.py --force

# Modalità silenziosa
python cleanup_temp_repos.py --force --quiet
```

**Funzionalità:**
- ✅ Trova repository clonati in `temp/`, `repos/`, `cloned_repos/`, `temp_repos/`
- ✅ Trova file temporanei (*.tmp, *.temp, *.cache)
- ✅ Mostra dimensione e età di ogni elemento
- ✅ Calcola spazio totale da liberare
- ✅ Filtro per età (--old-only)
- ✅ Modalità dry-run per test sicuro

### 2. `auto_cleanup.py` - Pulizia Automatica Integrata
Sistema di pulizia automatica da integrare nel workflow.

**Integrato automaticamente in `github_repo_processor.py`:**
- 🔄 Pulizia automatica dopo estrazione
- ✅ Mantiene repository in caso di errore (per debug)
- ✅ Verifica upload cloud prima di eliminare
- 📊 Logging dettagliato

**Comportamento:**
```python
# Elimina SE:
- Upload cloud riuscito ✅
- Funzioni estratte > 0 ✅

# Mantiene SE:
- Upload fallito ❌ (per debug)
- 0 funzioni estratte ❌ (per debug)
- Errore durante estrazione ❌ (per debug)
```

## 🚀 Uso nel Workflow

### Scenario 1: Processing Normale con Auto-Cleanup
```python
# Auto-cleanup abilitato per default
processor = GitHubRepoProcessor(
    cloud_save=True,
    auto_cleanup=True  # Default
)

# Processa repository
processor.process_repository("https://github.com/user/repo")

# Il repository viene automaticamente eliminato dopo upload cloud ✅
```

### Scenario 2: Debug Mode (Mantieni Repository)
```python
# Disabilita auto-cleanup per debug
processor = GitHubRepoProcessor(
    cloud_save=True,
    auto_cleanup=False  # Mantieni per debug
)

# Processa repository
processor.process_repository("https://github.com/user/repo")

# Repository rimane in temp/ per ispezione manuale
```

### Scenario 3: Pulizia Manuale Periodica
```bash
# Cron job giornaliero (Linux/Mac)
0 2 * * * cd /path/to/project && python cleanup_temp_repos.py --old-only --force --quiet

# Task Scheduler (Windows)
# Crea task che esegue ogni notte alle 2:00:
# python cleanup_temp_repos.py --old-only --force --quiet
```

## 📊 Esempi di Output

### Cleanup Manuale - Dry Run
```
================================================================
🗑️  ELEMENTI DA ELIMINARE
================================================================

📁 Repository Clonati: 5

  • pytorch
    Dimensione: 1.23 GB
    Età: 2d 5h
    Path: C:\...\temp\pytorch

  • tensorflow
    Dimensione: 856.34 MB
    Età: 1d 12h
    Path: C:\...\temp\tensorflow

================================================================
Totale da liberare: 2.08 GB
================================================================
```

### Auto-Cleanup Log
```
2025-11-02 10:30:15 - AutoCleanup - INFO - Cleanup pytorch: upload=✅, functions=245
2025-11-02 10:30:15 - AutoCleanup - INFO - ✅ Eliminato repository: pytorch (1.23 GB)

2025-11-02 10:32:20 - AutoCleanup - INFO - Cleanup empty-repo: upload=✅, functions=0
2025-11-02 10:32:20 - AutoCleanup - INFO - ⚠️  Mantengo empty-repo per debug (0 funzioni estratte)

2025-11-02 10:35:10 - AutoCleanup - INFO - Cleanup failed-repo: upload=❌, functions=10
2025-11-02 10:35:10 - AutoCleanup - INFO - ⚠️  Mantengo failed-repo per debug (upload fallito)
```

## 🔧 Configurazione

### File `.env`
Controlla comportamento auto-cleanup (opzionale):

```bash
# Comportamento cleanup
AUTO_CLEANUP=true           # Abilita auto-cleanup (default: true)
CLEANUP_KEEP_ON_ERROR=true  # Mantieni repo su errore (default: true)
CLEANUP_KEEP_DAYS=0         # Giorni da mantenere (0 = elimina subito)
```

## 🛠️ Integrazione Custom

### Usa AutoCleanup nel tuo codice
```python
from auto_cleanup import AutoCleanup

# Inizializza cleaner
cleaner = AutoCleanup(
    keep_on_error=True,  # Mantieni su errore
    keep_days=0,         # Elimina subito
    log_file='cleanup.log'  # Log su file (opzionale)
)

# Scenario 1: Cleanup semplice
cleaner.cleanup_repo("temp/my_repo")

# Scenario 2: Cleanup condizionale
cleaner.cleanup_after_upload(
    repo_path="temp/pytorch",
    upload_success=True,
    extracted_count=245
)

# Scenario 3: Pulizia periodica
cleaner.cleanup_old_repos(base_dir="temp")
```

### Helper Functions
```python
from auto_cleanup import cleanup_after_success, cleanup_if_uploaded

# Pulizia dopo successo
cleanup_after_success("temp/repo")

# Pulizia condizionale
cleanup_if_uploaded(
    repo_path="temp/repo",
    upload_ok=True,
    functions=100
)
```

## 📈 Monitoraggio Spazio Disco

### Script Rapido
```bash
# Mostra dimensione cartelle temp
python -c "from cleanup_temp_repos import RepoCleanup; c = RepoCleanup(); repos = c.find_repo_dirs(); print(f'Repository: {len(repos)}'); print(f'Spazio: {c.format_size(sum(r[1] for r in repos))}')"
```

### Verifica Pre-Processing
```bash
# Prima di processing batch
python cleanup_temp_repos.py --dry-run

# Output:
# Totale da liberare: 2.08 GB
```

## 🚨 Troubleshooting

### Repository Non Eliminato
**Problema:** Repository rimane dopo processing

**Soluzioni:**
```bash
# 1. Verifica auto_cleanup abilitato
python -c "from github_repo_processor import GitHubRepoProcessor; p = GitHubRepoProcessor(); print(f'Auto cleanup: {p.auto_cleanup}')"

# 2. Controlla log per errori
tail -f logs/processing.log | grep cleanup

# 3. Elimina manualmente
python cleanup_temp_repos.py --force
```

### Permessi Negati (Windows)
**Problema:** `PermissionError` durante eliminazione

**Soluzione:**
```python
# Il sistema retry automatico gestisce questo caso
# Se persiste, chiudi processi che bloccano i file:
# - IDE/Editor aperti sui file
# - Git GUI tools
# - Antivirus scan

# Forza eliminazione con retry
python cleanup_temp_repos.py --force
```

### Spazio Insufficiente Durante Processing
**Problema:** Disco pieno durante batch processing

**Soluzione:**
```bash
# 1. Pulizia emergenza
python cleanup_temp_repos.py --force --quiet

# 2. Abilita cleanup più aggressivo
# In .env:
AUTO_CLEANUP=true
CLEANUP_KEEP_ON_ERROR=false  # Elimina anche su errore
```

## 📊 Best Practices

### 1. Monitoraggio Spazio
```bash
# Controlla spazio prima di batch processing
df -h  # Linux/Mac
wmic logicaldisk get size,freespace,caption  # Windows

# Esegui cleanup preventivo
python cleanup_temp_repos.py --old-only --auto
```

### 2. Backup Repository Importanti
```python
# Prima di cleanup, backup repository interessanti
import shutil
shutil.copytree("temp/important_repo", "backup/important_repo")

# Poi cleanup
python cleanup_temp_repos.py --force
```

### 3. Cleanup Schedulato
```bash
# Linux/Mac - Cron
crontab -e
# Aggiungi:
0 2 * * * cd /path/to/project && python cleanup_temp_repos.py --old-only --force --quiet

# Windows - Task Scheduler
# Crea task con trigger giornaliero
# Action: python cleanup_temp_repos.py --old-only --force --quiet
```

### 4. Debug Mode
```python
# Quando debug problemi di estrazione
processor = GitHubRepoProcessor(
    auto_cleanup=False  # Mantieni per ispezione
)

# Dopo debug, cleanup manuale
python cleanup_temp_repos.py --dry-run  # Preview
python cleanup_temp_repos.py --force    # Esegui
```

## 📝 Summary

| Scenario | Script | Comando |
|----------|--------|---------|
| Preview pulizia | `cleanup_temp_repos.py` | `--dry-run` |
| Pulizia interattiva | `cleanup_temp_repos.py` | (default) |
| Pulizia automatica | `cleanup_temp_repos.py` | `--force` |
| Solo file vecchi | `cleanup_temp_repos.py` | `--old-only --auto` |
| Processing normale | `github_repo_processor.py` | Auto-cleanup ✅ |
| Debug mode | `github_repo_processor.py` | `auto_cleanup=False` |

## 🎯 Quick Start

```bash
# 1. Preview cosa verrebbe eliminato
python cleanup_temp_repos.py --dry-run

# 2. Conferma ed esegui
python cleanup_temp_repos.py

# 3. O forza pulizia completa
python cleanup_temp_repos.py --force

# 4. Verifica spazio liberato
python cleanup_temp_repos.py --dry-run  # Dovrebbe mostrare 0 B
```

**Sistema pronto! 🎉**

L'auto-cleanup è integrato e funziona automaticamente durante il processing dei repository.
