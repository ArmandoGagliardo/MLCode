# Controllo Dipendenze

Sistema automatico per verificare che tutti i pacchetti Python necessari siano installati e aggiornati.

## Utilizzo

### Controllo Rapido

Verifica le dipendenze con un report sintetico:

```bash
python check_dependencies.py
```

oppure tramite main.py:

```bash
python main.py --check-deps
```

### Controllo Dettagliato

Mostra tutte le dipendenze installate (anche quelle OK):

```bash
python check_dependencies.py --verbose
```

oppure:

```bash
python main.py --check-deps --verbose
```

### Installazione Automatica

Installa automaticamente i pacchetti critici mancanti:

```bash
python check_dependencies.py --auto-install
```

oppure:

```bash
python main.py --check-deps --auto-install
```

## Tipi di Dipendenze

### Dipendenze Critiche

Pacchetti essenziali per il funzionamento base del sistema:

- **torch** (>= 2.0.0) - Framework PyTorch per deep learning
- **transformers** (>= 4.30.0) - Libreria HuggingFace per modelli pre-addestrati
- **datasets** (>= 2.0.0) - Gestione dataset HuggingFace
- **numpy** (>= 1.20.0) - Calcoli numerici
- **pandas** (>= 1.3.0) - Analisi dati
- **requests** (>= 2.25.0) - HTTP requests
- **python-dotenv** (>= 0.19.0) - Gestione variabili ambiente

Se mancano queste dipendenze, il sistema **non funzionerà correttamente**.

### Dipendenze Opzionali

Pacchetti per funzionalità specifiche:

| Pacchetto | Funzionalità | Comando |
|-----------|--------------|---------|
| **boto3** | Cloud Storage (Backblaze, Wasabi, S3, etc.) | `pip install boto3` |
| **streamlit** | Interfaccia Web UI | `pip install streamlit` |
| **beautifulsoup4** | Web Crawling statico | `pip install beautifulsoup4` |
| **selenium** | Web Crawling dinamico | `pip install selenium` |
| **PyYAML** | Parsing YAML (security scanning) | `pip install PyYAML` |
| **scikit-learn** | Algoritmi ML aggiuntivi | `pip install scikit-learn` |

Se mancano queste dipendenze, alcune funzionalità potrebbero **non essere disponibili**.

## Output del Controllo

### Simboli di Stato

- `[OK]` - Pacchetto installato e aggiornato ✓
- `[X]` - Pacchetto mancante (critico) ✗
- `[!]` - Pacchetto mancante o obsoleto (opzionale) ⚠
- `[?]` - Stato sconosciuto

### Esempio Output

```
================================================================================
CONTROLLO DIPENDENZE
================================================================================

Versione Python: Python 3.13 (OK)

[CRITICHE] DIPENDENZE CRITICHE:
--------------------------------------------------------------------------------
[OK] torch                v2.6.0           (>= 2.0.0)
[OK] transformers         v4.51.3          (>= 4.30.0)
[X] datasets             Non installato   (richiesto: >= 2.0.0)
[OK] numpy                v2.2.3           (>= 1.20.0)

[OPZIONALI] DIPENDENZE OPZIONALI:
--------------------------------------------------------------------------------
[!] boto3                Non installato
   Feature: Cloud Storage (Backblaze, Wasabi, S3, DigitalOcean, Cloudflare R2)
   Install: pip install boto3
[OK] streamlit            v1.51.0          - Web UI Interface

================================================================================
RIEPILOGO
================================================================================

[X] AZIONE RICHIESTA - Dipendenze critiche mancanti o obsolete!

[INSTALLA] Installa i pacchetti mancanti:
   pip install datasets

Oppure installa tutte le dipendenze:
   pip install -r requirements.txt

================================================================================
```

## Controllo Automatico all'Avvio

Il sistema controlla automaticamente le dipendenze critiche ogni volta che viene avviato `main.py`.

Se mancano dipendenze critiche, viene mostrato un avviso:

```
⚠️  ATTENZIONE: Alcune dipendenze critiche mancano o sono obsolete
   Esegui: python check_dependencies.py --auto-install
   Oppure: pip install -r requirements.txt
```

Il programma continuerà comunque l'esecuzione, ma potrebbero verificarsi errori.

## Installazione Dipendenze

### Tutte le Dipendenze

Installa tutte le dipendenze dal file requirements.txt:

```bash
pip install -r requirements.txt
```

### Solo Dipendenze Critiche

```bash
pip install torch transformers datasets numpy pandas requests python-dotenv
```

### Solo Dipendenze per Cloud Storage

```bash
pip install boto3 botocore
```

### Solo Dipendenze per Web UI

```bash
pip install streamlit
```

### Solo Dipendenze per Web Crawling

```bash
pip install beautifulsoup4 selenium
```

## Aggiornamento Dipendenze

### Aggiorna Tutte le Dipendenze

```bash
pip install --upgrade -r requirements.txt
```

### Aggiorna un Pacchetto Specifico

```bash
pip install --upgrade torch
```

## Risoluzione Problemi

### Dipendenza Non Trovata

Se un pacchetto risulta "Non installato" ma è presente:

1. Verifica il nome del pacchetto: `pip list | grep nome_pacchetto`
2. Potrebbe avere un nome diverso nel sistema
3. Aggiorna pip: `python -m pip install --upgrade pip`

### Versione Obsoleta

Se un pacchetto risulta obsoleto:

```bash
pip install --upgrade nome_pacchetto
```

### Conflitti di Versione

Se ci sono conflitti tra le versioni:

1. Crea un ambiente virtuale:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Installa le dipendenze nell'ambiente:
   ```bash
   pip install -r requirements.txt
   ```

### Errore di Import

Se una dipendenza risulta installata ma dà errore di import:

1. Riavvia Python/IDE
2. Verifica il percorso di installazione: `pip show nome_pacchetto`
3. Reinstalla il pacchetto: `pip uninstall nome_pacchetto && pip install nome_pacchetto`

## Requisiti di Sistema

- **Python**: >= 3.8 (consigliato 3.10+)
- **pip**: versione recente (>= 21.0)
- **Sistema Operativo**: Windows, Linux, macOS

### Verifica Versione Python

```bash
python --version
```

### Verifica Versione pip

```bash
pip --version
```

### Aggiorna pip

```bash
python -m pip install --upgrade pip
```

## Integrazione nel Codice

Puoi usare il controllo dipendenze programmaticamente:

```python
from check_dependencies import check_dependencies

# Controllo semplice
if not check_dependencies():
    print("Alcune dipendenze mancano!")
    exit(1)

# Controllo con auto-install
check_dependencies(verbose=True, auto_install=True)
```

## Best Practices

1. **Controlla prima di iniziare**: Esegui `--check-deps` prima di training o operazioni lunghe
2. **Usa ambiente virtuale**: Crea un venv dedicato per il progetto
3. **Aggiorna regolarmente**: Mantieni le dipendenze aggiornate per sicurezza e performance
4. **Installa solo necessarie**: Non installare tutto se usi solo alcune funzionalità
5. **Leggi i warning**: Se vedi `[!]` per dipendenze opzionali, installa solo quelle che ti servono

## FAQ

**Q: Il controllo è troppo lento?**
A: Il controllo impiega 2-3 secondi. Se ti sembra troppo, puoi disabilitarlo temporaneamente passando `--help` a main.py

**Q: Posso aggiungere altre dipendenze?**
A: Sì, modifica il dizionario `CRITICAL_DEPENDENCIES` o `OPTIONAL_DEPENDENCIES` in `check_dependencies.py`

**Q: Il controllo blocca l'avvio?**
A: No, il controllo automatico all'avvio mostra solo un warning ma non blocca l'esecuzione

**Q: Posso disabilitare il controllo automatico?**
A: Sì, rimuovi le righe 23-37 da `main.py` (sezione "Controllo dipendenze")

## Supporto

Per problemi o domande:
1. Controlla questo documento
2. Esegui `python check_dependencies.py --verbose`
3. Controlla i log in `ml_system.log`
4. Verifica requirements.txt
