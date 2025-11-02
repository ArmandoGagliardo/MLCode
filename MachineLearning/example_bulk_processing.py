"""
Esempio Bulk Processing - Estrarre funzioni da multipli repository

Questo script mostra come processare una lista di repository GitHub
in modalità batch con configurazione avanzata.

Requisiti:
- File repo_list.txt con URL dei repository
- Virtual environment attivo
- Tutte le dipendenze installate

Uso:
    python example_bulk_processing.py
"""

from bulk_processor import BulkProcessor
from pathlib import Path
import json
from datetime import datetime


def main():
    print("=" * 60)
    print("🚀 BULK PROCESSING - MULTI-REPOSITORY EXTRACTION")
    print("=" * 60)
    print()

    # Configurazione
    repo_list_file = "repo_list.txt"
    output_dir = Path("datasets/local_backup/code_generation")
    
    print("📋 Configurazione:")
    print(f"   Repository list: {repo_list_file}")
    print(f"   Output directory: {output_dir}")
    print(f"   Cloud save: No (locale only)")
    print(f"   Batch size: 100 funzioni")
    print()

    # Verifica che esista il file repo_list.txt
    if not Path(repo_list_file).exists():
        print("⚠️  File 'repo_list.txt' non trovato!")
        print()
        print("Creo un esempio con 3 repository popolari...")
        
        example_repos = [
            "https://github.com/psf/requests",      # Python
            "https://github.com/axios/axios",       # JavaScript
            "https://github.com/spf13/cobra",       # Go
        ]
        
        with open(repo_list_file, 'w') as f:
            for repo in example_repos:
                f.write(f"{repo}\n")
        
        print(f"✅ Creato {repo_list_file} con {len(example_repos)} repository")
        print()

    # Leggi repository da processare
    with open(repo_list_file, 'r') as f:
        repos = [line.strip() for line in f if line.strip()]
    
    print(f"📦 Repository da processare: {len(repos)}")
    for i, repo in enumerate(repos, 1):
        print(f"   {i}. {repo}")
    print()

    # Crea bulk processor
    print("🔧 Inizializzazione bulk processor...")
    processor = BulkProcessor(
        source_type="github",
        source_path=repo_list_file,
        cloud_save=False,      # Cambia a True per upload automatico
        batch_size=100,        # Funzioni per batch
        language=None          # None = tutti i linguaggi
    )
    print("✅ Processor pronto!")
    print()

    # Stampa statistiche iniziali
    print("📊 Stato iniziale:")
    stats_before = get_output_stats(output_dir)
    print(f"   File esistenti: {stats_before['total_files']}")
    print(f"   Funzioni totali: {stats_before['total_functions']}")
    print()

    # Esegui processing
    print("🚀 INIZIO PROCESSING...")
    print("💡 Tip: Premi CTRL+C in qualsiasi momento per stop graceful")
    print("-" * 60)
    
    start_time = datetime.now()
    
    try:
        processor.run()
    except KeyboardInterrupt:
        print()
        print("⚠️  Interruzione richiesta dall'utente")
        print("💾 Salvataggio progresso in corso...")
    except Exception as e:
        print(f"❌ Errore durante processing: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("-" * 60)
    print("✅ PROCESSING COMPLETATO!")
    print()

    # Stampa statistiche finali
    print("📊 Risultati Finali:")
    stats_after = get_output_stats(output_dir)
    
    files_created = stats_after['total_files'] - stats_before['total_files']
    functions_extracted = stats_after['total_functions'] - stats_before['total_functions']
    
    print(f"   ⏱️  Tempo totale: {duration:.1f} secondi ({duration/60:.1f} minuti)")
    print(f"   📁 Nuovi file creati: {files_created}")
    print(f"   ✨ Funzioni estratte: {functions_extracted}")
    print(f"   📦 File totali ora: {stats_after['total_files']}")
    print(f"   🎯 Funzioni totali: {stats_after['total_functions']}")
    
    if functions_extracted > 0:
        print(f"   ⚡ Velocità: {functions_extracted / duration:.1f} funzioni/secondo")
    print()

    # Mostra breakdown per linguaggio
    print("📈 Breakdown per Linguaggio:")
    for lang, count in stats_after['by_language'].items():
        percentage = (count / stats_after['total_functions'] * 100) if stats_after['total_functions'] > 0 else 0
        print(f"   {lang:12s}: {count:4d} funzioni ({percentage:5.1f}%)")
    print()

    # Mostra file più recenti
    print("📄 Ultimi 5 file creati:")
    recent_files = sorted(
        output_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:5]
    
    for f in recent_files:
        size_kb = f.stat().st_size / 1024
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"   {f.name} ({size_kb:.1f} KB) - {mtime.strftime('%H:%M:%S')}")
    print()

    print("=" * 60)
    print("🎉 BULK PROCESSING COMPLETATO CON SUCCESSO!")
    print("=" * 60)


def get_output_stats(output_dir: Path) -> dict:
    """Calcola statistiche sui file di output"""
    stats = {
        'total_files': 0,
        'total_functions': 0,
        'by_language': {}
    }
    
    if not output_dir.exists():
        return stats
    
    for json_file in output_dir.glob("*.json"):
        stats['total_files'] += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats['total_functions'] += len(data)
                
                # Conta per linguaggio
                for func in data:
                    lang = func.get('language', 'unknown')
                    stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
        except:
            pass  # Skip file corrotti
    
    return stats


if __name__ == "__main__":
    main()
