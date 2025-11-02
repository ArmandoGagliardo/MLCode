"""
Dataset Validator - Versione Corretta

Valida i dataset basandosi sulla struttura reale generata da github_repo_processor.py

Struttura attesa:
{
    "task_type": "code_generation",
    "language": "python",
    "func_name": "function_name",
    "input": "Write a python function named function_name",
    "output": "def function_name(): ...",
    "repo_url": "https://github.com/user/repo",
    "file_path": "/path/to/file.py",
    "extracted_at": "2025-11-02T14:51:16.959586"
}

Uso:
    python validate_datasets.py
    python validate_datasets.py --file data/datasets/code_generation/file.json
    python validate_datasets.py --all
    python validate_datasets.py --dir data/datasets/code_generation
"""

import json
import sys
import argparse
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple
from datetime import datetime


class DatasetValidator:
    """Validatore per dataset generati da github_repo_processor"""
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0
        }
    
    def validate_item(self, item: Dict, index: int) -> bool:
        """Valida un singolo item del dataset"""
        is_valid = True
        
        # Campi obbligatori
        required = ['task_type', 'language', 'input', 'output']
        for field in required:
            if field not in item:
                self.errors.append(f"Item {index}: Manca campo obbligatorio '{field}'")
                is_valid = False
        
        # Campi metadata (opzionali ma consigliati)
        metadata = ['func_name', 'repo_url', 'file_path', 'extracted_at']
        missing_meta = [f for f in metadata if f not in item]
        if missing_meta:
            self.warnings.append(f"Item {index}: Mancano metadata: {', '.join(missing_meta)}")
            self.stats['warnings'] += 1
        
        # Valida contenuto
        if 'input' in item:
            input_str = str(item['input']) if item['input'] else ''
            if len(input_str.strip()) < 10:
                self.errors.append(f"Item {index}: Input troppo corto")
                is_valid = False
        
        if 'output' in item:
            output_str = str(item['output']) if item['output'] else ''
            if len(output_str.strip()) < 5:
                self.errors.append(f"Item {index}: Output troppo corto")
                is_valid = False
        
        # Valida task_type
        if 'task_type' in item:
            valid_tasks = ['code_generation', 'bug_fixing', 'code_completion']
            if item['task_type'] not in valid_tasks:
                self.warnings.append(f"Item {index}: task_type non standard: {item['task_type']}")
                self.stats['warnings'] += 1
        
        # Valida language
        if 'language' in item:
            valid_langs = ['python', 'javascript', 'java', 'cpp', 'go', 'rust', 'php']
            if item['language'] not in valid_langs:
                self.warnings.append(f"Item {index}: language non riconosciuto: {item['language']}")
                self.stats['warnings'] += 1
        
        return is_valid
    
    def validate_file(self, filepath: str) -> bool:
        """Valida un file dataset completo"""
        print(f"\n{'='*70}")
        print(f"VALIDAZIONE: {filepath}")
        print(f"{'='*70}\n")
        
        path = Path(filepath)
        if not path.exists():
            print(f"ERRORE: File non trovato")
            return False
        
        # Carica JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERRORE: JSON non valido - {e}")
            return False
        except Exception as e:
            print(f"ERRORE: Impossibile leggere file - {e}")
            return False
        
        print(f"Caricato: {len(data)} items\n")
        
        # Reset statistiche
        self.errors = []
        self.warnings = []
        self.stats = {'total': len(data), 'valid': 0, 'invalid': 0, 'warnings': 0}
        
        # Valida ogni item
        for i, item in enumerate(data):
            if self.validate_item(item, i):
                self.stats['valid'] += 1
            else:
                self.stats['invalid'] += 1
        
        # Stampa statistiche
        self.print_statistics(data)
        
        # Stampa errori/warning
        self.print_issues()
        
        # Risultato
        print(f"\n{'='*70}")
        has_errors = len(self.errors) > 0
        if has_errors:
            print("RISULTATO: FALLITO")
            return False
        else:
            print("RISULTATO: SUPERATO")
            if len(self.warnings) > 0:
                print(f"Con {len(self.warnings)} warning (non bloccanti)")
            return True
    
    def print_statistics(self, data: List[Dict]):
        """Stampa statistiche del dataset"""
        print(f"\n{'='*70}")
        print("STATISTICHE")
        print(f"{'='*70}\n")
        
        print(f"Totale items:      {self.stats['total']}")
        print(f"Items validi:      {self.stats['valid']} ({self.stats['valid']/self.stats['total']*100:.1f}%)")
        print(f"Items invalidi:    {self.stats['invalid']}")
        print(f"Warning:           {self.stats['warnings']}")
        
        # Task types
        print(f"\nTask Types:")
        tasks = Counter(item.get('task_type', 'unknown') for item in data)
        for task, count in tasks.most_common():
            pct = count / len(data) * 100
            print(f"  - {task:20s}: {count:5d} ({pct:5.1f}%)")
        
        # Languages
        print(f"\nLanguages:")
        languages = Counter(item.get('language', 'unknown') for item in data)
        for lang, count in languages.most_common():
            pct = count / len(data) * 100
            print(f"  - {lang:20s}: {count:5d} ({pct:5.1f}%)")
        
        # Repository sources
        repos = Counter(item.get('repo_url', 'unknown') for item in data)
        if len(repos) > 0:
            print(f"\nRepository Sources: {len(repos)} repository diversi")
            for repo, count in list(repos.most_common(5)):
                repo_name = repo.split('/')[-1] if repo != 'unknown' else 'unknown'
                print(f"  - {repo_name:30s}: {count:5d} funzioni")
            if len(repos) > 5:
                print(f"  ... e altri {len(repos) - 5} repository")
        
        # Lunghezze
        input_lens = [len(str(item.get('input', ''))) for item in data]
        output_lens = [len(str(item.get('output', ''))) for item in data]
        
        print(f"\nLunghezze:")
        print(f"  Input:  min={min(input_lens):6d}, max={max(input_lens):6d}, media={sum(input_lens)/len(input_lens):6.0f}")
        print(f"  Output: min={min(output_lens):6d}, max={max(output_lens):6d}, media={sum(output_lens)/len(output_lens):6.0f}")
    
    def print_issues(self):
        """Stampa errori e warning"""
        if self.errors:
            print(f"\n{'='*70}")
            print(f"ERRORI ({len(self.errors)})")
            print(f"{'='*70}\n")
            for error in self.errors[:10]:
                print(f"  {error}")
            if len(self.errors) > 10:
                print(f"\n  ... e altri {len(self.errors) - 10} errori")
        
        if self.warnings:
            print(f"\n{'='*70}")
            print(f"WARNING ({len(self.warnings)})")
            print(f"{'='*70}\n")
            for warning in self.warnings[:10]:
                print(f"  {warning}")
            if len(self.warnings) > 10:
                print(f"\n  ... e altri {len(self.warnings) - 10} warning")


def validate_directory(dir_path: str) -> Tuple[int, int]:
    """Valida tutti i JSON in una directory"""
    path = Path(dir_path)
    if not path.exists():
        print(f"ERRORE: Directory non trovata: {dir_path}")
        return 0, 0
    
    json_files = list(path.glob("*.json"))
    if not json_files:
        print(f"ERRORE: Nessun file JSON in {dir_path}")
        return 0, 0
    
    print(f"\n{'='*70}")
    print(f"VALIDAZIONE MULTIPLA")
    print(f"{'='*70}")
    print(f"\nDirectory: {dir_path}")
    print(f"File trovati: {len(json_files)}\n")
    
    results = {}
    for json_file in json_files:
        validator = DatasetValidator()
        success = validator.validate_file(str(json_file))
        results[json_file.name] = success
    
    # Summary
    print(f"\n{'='*70}")
    print(f"RIEPILOGO")
    print(f"{'='*70}\n")
    
    for filename, success in results.items():
        status = "OK" if success else "FAIL"
        print(f"  [{status:4s}] {filename}")
    
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotale: {passed}/{len(results)} file validi")
    
    return passed, len(results)


def validate_all():
    """Valida tutti i dataset in tutte le directory standard"""
    dirs = [
        "data/datasets/code_generation",
        "datasets",
        "datasets/local_backup/code_generation",
    ]
    
    total_passed = 0
    total_files = 0
    
    print(f"\n{'='*70}")
    print(f"VALIDAZIONE GLOBALE")
    print(f"{'='*70}\n")
    
    for dir_path in dirs:
        if Path(dir_path).exists():
            passed, count = validate_directory(dir_path)
            total_passed += passed
            total_files += count
    
    print(f"\n{'='*70}")
    print(f"RISULTATO FINALE")
    print(f"{'='*70}")
    print(f"\n{total_passed}/{total_files} file validi totali\n")
    
    return total_passed == total_files


def main():
    parser = argparse.ArgumentParser(
        description="Valida dataset JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--file', '-f', help='File specifico da validare')
    parser.add_argument('--dir', '-d', help='Directory da validare')
    parser.add_argument('--all', '-a', action='store_true', help='Valida tutte le directory standard')
    parser.add_argument('--strict', '-s', action='store_true', help='Modalita strict (warning come errori)')
    
    args = parser.parse_args()
    
    if args.all:
        success = validate_all()
    elif args.dir:
        passed, total = validate_directory(args.dir)
        success = (passed == total)
    elif args.file:
        validator = DatasetValidator(strict=args.strict)
        success = validator.validate_file(args.file)
    else:
        # Default: valida directory principale
        default_dir = "data/datasets/code_generation"
        if Path(default_dir).exists():
            passed, total = validate_directory(default_dir)
            success = (passed == total)
        else:
            print(f"ERRORE: Directory di default non trovata: {default_dir}")
            print(f"Usa --file o --dir per specificare cosa validare")
            success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
