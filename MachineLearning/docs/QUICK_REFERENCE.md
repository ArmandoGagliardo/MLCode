# Quick Reference Guide

Guida rapida ai comandi più comuni del sistema.

## 🚀 Comandi Principali

### Estrazione da Repository Singolo
```bash
python main.py
# Poi seleziona: Process GitHub Repository
# Inserisci URL: https://github.com/user/repo
```

### Estrazione Massiva (Bulk)
```bash
# Da lista di repository
python bulk_processor.py --source github --repos repo_list.txt

# Con lingua specifica
python bulk_processor.py --source github --repos repo_list.txt --language python

# Da directory locale
python bulk_processor.py --source local --path /path/to/code
```

### Test e Verifica
```bash
# Test completo tutti i linguaggi
cd debug
python test_all_languages_final.py

# Test linguaggio specifico
python test_java_extraction.py
python test_rust_extraction.py

# Verifica sistema
python verify_system.py
```

## 📁 File Importanti

### Configurazione
- `.env` - Credenziali e configurazione
- `config.py` - Configurazione Python
- `repo_list.txt` - Lista repository da processare

### Output
- `dataset_storage/local_backup/code_generation/` - Funzioni estratte (JSON)
- `logs/` - Log di esecuzione
- `datasets/duplicates_cache.json` - Cache duplicati

### Documentazione
- `README.md` - Documentazione principale
- `docs/README.md` - Indice documentazione tecnica
- `debug/README.md` - Documentazione test e debug

## 🔧 Manutenzione

### Pulizia Cache
```bash
# Windows
Remove-Item datasets\duplicates_cache.json -ErrorAction SilentlyContinue

# Linux/Mac
rm -f datasets/duplicates_cache.json
```

### Reset Checkpoint
```bash
# Windows
Remove-Item bulk_processor_checkpoint.json -ErrorAction SilentlyContinue

# Linux/Mac
rm -f bulk_processor_checkpoint.json
```

### View Logs
```bash
# Ultimi log
Get-Content logs\processing.log -Tail 50  # Windows
tail -n 50 logs/processing.log             # Linux/Mac
```

## 📊 Monitoraggio

### Contare Funzioni Estratte
```bash
# Windows PowerShell
Get-ChildItem -Path datasets\local_backup\code_generation\ -Filter *.json -Recurse | 
    ForEach-Object { (Get-Content $_.FullName | ConvertFrom-Json).Count } | 
    Measure-Object -Sum

# Linux/Mac (con jq)
find dataset_storage/local_backup/code_generation/ -name "*.json" -exec jq 'length' {} \; | 
    awk '{s+=$1} END {print s}'
```

### Verificare Storage Cloud
```bash
# Verifica configurazione
cd debug
python test_storage_connection.py
```

## 🐛 Troubleshooting

### Parser Non Funziona
```bash
cd debug
python debug_<language>_ast.py  # es: debug_rust_ast.py
```

### Quality Filter Troppo Restrittivo
Modifica in `module/preprocessing/code_quality_filter.py`:
- `min_length` - Lunghezza minima
- `min_lines` - Linee minime
- `has_sufficient_complexity()` - Complessità

### Problemi GitHub Rate Limit
1. Aggiungi `GITHUB_TOKEN` nel `.env`
2. Ottieni token da: https://github.com/settings/tokens

## 📚 Linguaggi Supportati

| Linguaggio | File Extension | Test Command |
|------------|---------------|--------------|
| Python     | .py          | `python debug/test_simple_extraction.py` |
| JavaScript | .js          | `python debug/test_js_parser.py` |
| Go         | .go          | `python debug/test_go_simple.py` |
| Rust       | .rs          | `python debug/test_rust_extraction.py` |
| Java       | .java        | `python debug/test_java_extraction.py` |
| C++        | .cpp, .h     | `python debug/test_components.py` |
| Ruby       | .rb          | `python debug/test_components.py` |

## 🎯 Workflow Tipico

1. **Setup**
   ```bash
   # Installa dipendenze
   pip install -r requirements.txt
   
   # Configura .env
   cp .env.example .env
   # Edita .env con le tue credenziali
   ```

2. **Prepara Lista Repository**
   ```bash
   # Edita repo_list.txt
   nano repo_list.txt  # o notepad repo_list.txt su Windows
   ```

3. **Esegui Estrazione**
   ```bash
   python bulk_processor.py --source github --repos repo_list.txt
   ```

4. **Verifica Risultati**
   ```bash
   # Controlla file generati
   ls dataset_storage/local_backup/code_generation/
   
   # Conta funzioni estratte
   # (vedi sezione Monitoraggio sopra)
   ```

5. **Upload Cloud** (opzionale)
   ```bash
   # Se cloud_save=True in config, upload è automatico
   # Altrimenti usa lo script manuale in debug/
   ```

## 🔐 Sicurezza

- ❌ Non committare `.env`
- ❌ Non condividere token GitHub
- ✅ Usa `.gitignore` per file sensibili
- ✅ Ruota le credenziali regolarmente

## 💡 Tips

- Usa `--batch_size` per gestire la memoria
- CTRL+C per stop graceful (salva progresso)
- Controlla `logs/` per debug dettagliato
- Testa su repo piccoli prima di bulk processing

---

**Ultimo aggiornamento**: 2 Novembre 2025
**Version**: 1.0 - Production Ready
