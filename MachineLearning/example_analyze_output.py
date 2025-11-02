"""
Esempio Analisi Output - Analizzare i risultati dell'estrazione

Questo script mostra come leggere, analizzare e ottenere insights
dai file JSON generati dall'estrazione.

Uso:
    python example_analyze_output.py
"""

from pathlib import Path
import json
from collections import Counter, defaultdict
from datetime import datetime


def main():
    print("=" * 70)
    print("📊 ANALISI OUTPUT - INSIGHTS SUI DATI ESTRATTI")
    print("=" * 70)
    print()

    # Directory con i risultati
    output_dir = Path("datasets/local_backup/code_generation")
    
    if not output_dir.exists() or not list(output_dir.glob("*.json")):
        print("⚠️  Nessun file di output trovato!")
        print(f"   Verifica che esista: {output_dir}")
        print()
        print("💡 Esegui prima:")
        print("   python example_single_repo.py")
        print("   oppure")
        print("   python example_bulk_processing.py")
        return

    # Carica tutti i file JSON
    print("📁 Caricamento dati...")
    all_functions = []
    files_processed = 0
    
    for json_file in output_dir.glob("*.json"):
        # Skip analysis_summary.json
        if json_file.name == "analysis_summary.json":
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_functions.extend(data)
                files_processed += 1
        except Exception as e:
            print(f"⚠️  Errore leggendo {json_file.name}: {e}")
    
    print(f"✅ Caricati {len(all_functions)} funzioni da {files_processed} file")
    print()

    # === STATISTICHE GENERALI ===
    print("=" * 70)
    print("📊 STATISTICHE GENERALI")
    print("=" * 70)
    
    print(f"Totale funzioni: {len(all_functions)}")
    print(f"Totale file JSON: {files_processed}")
    
    total_size = sum(f.stat().st_size for f in output_dir.glob("*.json"))
    print(f"Dimensione totale: {total_size / (1024*1024):.2f} MB")
    print()

    # === PER LINGUAGGIO ===
    print("=" * 70)
    print("📈 STATISTICHE PER LINGUAGGIO")
    print("=" * 70)
    
    lang_stats = Counter(f['language'] for f in all_functions)
    
    for lang, count in lang_stats.most_common():
        percentage = (count / len(all_functions) * 100)
        bar = "█" * int(percentage / 2)
        print(f"{lang:12s}: {count:5d} ({percentage:5.1f}%) {bar}")
    print()

    # === LUNGHEZZA FUNZIONI ===
    print("=" * 70)
    print("📏 ANALISI LUNGHEZZA FUNZIONI")
    print("=" * 70)
    
    # Gestisce sia 'body' che 'output' come campo del codice
    lengths = [len(f.get('body', f.get('output', ''))) for f in all_functions]
    
    print(f"Lunghezza media: {sum(lengths) / len(lengths):.0f} caratteri")
    print(f"Lunghezza minima: {min(lengths)} caratteri")
    print(f"Lunghezza massima: {max(lengths)} caratteri")
    print(f"Mediana: {sorted(lengths)[len(lengths)//2]} caratteri")
    print()

    # === NOMI FUNZIONI PIÙ COMUNI ===
    print("=" * 70)
    print("🏆 TOP 10 NOMI FUNZIONI PIÙ COMUNI")
    print("=" * 70)
    
    func_names = Counter(f.get('func_name', 'unknown') for f in all_functions)
    
    for name, count in func_names.most_common(10):
        print(f"{count:3d}x  {name}")
    print()

    # === PER TASK TYPE ===
    print("=" * 70)
    print("🎯 TASK TYPES")
    print("=" * 70)
    
    task_types = Counter(f.get('task_type', 'unknown') for f in all_functions)
    
    for task, count in task_types.items():
        print(f"{task}: {count}")
    print()

    # === REPOSITORY SOURCES ===
    print("=" * 70)
    print("📦 REPOSITORY SOURCES")
    print("=" * 70)
    
    # Estrai nome repo dal filename
    repo_counts = defaultdict(int)
    for json_file in output_dir.glob("*.json"):
        # Format: reponame_timestamp_count.json
        repo_name = json_file.stem.split('_')[0]
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            repo_counts[repo_name] += len(data)
    
    for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{repo:20s}: {count:4d} funzioni")
    print()

    # === ESEMPI DI FUNZIONI ===
    print("=" * 70)
    print("🔍 ESEMPI DI FUNZIONI ESTRATTE")
    print("=" * 70)
    
    # Mostra 1 esempio per ogni linguaggio
    shown_langs = set()
    for func in all_functions:
        lang = func.get('language', 'unknown')
        if lang not in shown_langs:
            print(f"\n[{lang.upper()}] {func.get('func_name', 'unknown')}")
            print("-" * 70)
            
            # Gestisce sia 'signature' che 'input'
            signature = func.get('signature', func.get('input', ''))
            if signature:
                print(f"Input: {signature[:80]}...")
            
            # Gestisce sia 'body' che 'output'
            body = func.get('body', func.get('output', ''))
            if body:
                print(f"Output preview:")
                body_lines = body.split('\n')[:5]
                for line in body_lines:
                    print(f"  {line[:70]}")
                if len(body.split('\n')) > 5:
                    print(f"  ... ({len(body.split('\n')) - 5} more lines)")
            
            shown_langs.add(lang)
            
            if len(shown_langs) >= 5:  # Mostra max 5 esempi
                break
    print()

    # === QUALITÀ DATI ===
    print("=" * 70)
    print("✅ QUALITÀ DATI")
    print("=" * 70)
    
    # Verifica campi richiesti (gestisce sia body/signature che output/input)
    complete_functions = sum(
        1 for f in all_functions 
        if all(k in f for k in ['func_name', 'language']) and 
           (f.get('body') or f.get('output'))
    )
    
    print(f"Funzioni complete: {complete_functions}/{len(all_functions)} ({complete_functions/len(all_functions)*100:.1f}%)")
    
    # Verifica lunghezza minima
    valid_length = sum(
        1 for f in all_functions 
        if len(f.get('body', f.get('output', ''))) >= 10
    )
    print(f"Lunghezza valida (>=10 char): {valid_length}/{len(all_functions)} ({valid_length/len(all_functions)*100:.1f}%)")
    
    # Verifica signature/input non vuote
    valid_sig = sum(
        1 for f in all_functions 
        if (f.get('signature', '') or f.get('input', '')).strip()
    )
    print(f"Input/Signature valide: {valid_sig}/{len(all_functions)} ({valid_sig/len(all_functions)*100:.1f}%)")
    print()

    # === CONSIGLI ===
    print("=" * 70)
    print("💡 CONSIGLI")
    print("=" * 70)
    
    if len(all_functions) < 100:
        print("⚠️  Hai meno di 100 funzioni. Considera:")
        print("   - Processare più repository (vedi example_bulk_processing.py)")
        print("   - Usare repository più grandi")
    
    if lang_stats.most_common(1)[0][1] / len(all_functions) > 0.8:
        dominant_lang = lang_stats.most_common(1)[0][0]
        print(f"⚠️  Dataset sbilanciato: {dominant_lang} rappresenta >80%")
        print("   Considera aggiungere repository di altri linguaggi")
    
    avg_length = sum(lengths) / len(lengths)
    if avg_length < 50:
        print("⚠️  Funzioni mediamente corte (<50 char)")
        print("   Valuta aumentare MIN_FUNCTION_LENGTH in config.py")
    
    if avg_length > 5000:
        print("⚠️  Funzioni mediamente lunghe (>5000 char)")
        print("   Valuta diminuire MAX_FILE_SIZE_MB in config.py")
    
    print()

    # === EXPORT SUMMARY ===
    print("=" * 70)
    print("💾 EXPORT SUMMARY")
    print("=" * 70)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_functions": len(all_functions),
        "total_files": files_processed,
        "total_size_mb": round(total_size / (1024*1024), 2),
        "languages": dict(lang_stats),
        "by_repository": dict(repo_counts),
        "quality": {
            "complete": complete_functions,
            "valid_length": valid_length,
            "valid_signature": valid_sig,
            "avg_body_length": round(avg_length, 0)
        }
    }
    
    summary_file = output_dir / "analysis_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Summary salvato in: {summary_file}")
    print()

    print("=" * 70)
    print("🎉 ANALISI COMPLETATA!")
    print("=" * 70)


if __name__ == "__main__":
    main()
