# module/scripts/validate_dataset.py
"""
Dataset Validator

Valida la struttura e il contenuto dei dataset estratti.
Verifica:
- Formato JSON corretto
- Campi obbligatori presenti
- Lunghezza minima di input/output
- Distribuzione linguaggi e task types
- Qualità del codice estratto

Uso:
    python module/scripts/validate_dataset.py
    python module/scripts/validate_dataset.py --file datasets/dataset_classification_v2.json
    python module/scripts/validate_dataset.py --all
"""

import json
import sys
import argparse
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


class DatasetValidator:
    """Validatore completo per dataset"""
    
    def __init__(self, strict: bool = False):
        """
        Args:
            strict: Modalità strict (errore su warning)
        """
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0
        }
    
    def validate_item_structure(self, item: Dict, index: int) -> Tuple[bool, List[str]]:
        """Valida la struttura di un singolo item"""
        errors = []
        warnings = []
        
        # Campi obbligatori
        required_fields = ['task_type', 'language', 'input', 'output']
        for field in required_fields:
            if field not in item:
                errors.append(f"Item {index}: Campo obbligatorio mancante: {field}")
        
        # Campi opzionali ma consigliati
        recommended_fields = ['func_name']
        for field in recommended_fields:
            if field not in item:
                warnings.append(f"Item {index}: Campo consigliato mancante: {field}")
        
        # Valida lunghezza minima
        if 'input' in item:
            if not item['input'] or len(item['input'].strip()) < 10:
                errors.append(f"Item {index}: Input troppo corto (min 10 caratteri)")
        
        if 'output' in item:
            if not item['output'] or len(item['output'].strip()) < 5:
                errors.append(f"Item {index}: Output troppo corto (min 5 caratteri)")
        
        # Valida task_type
        if 'task_type' in item:
            valid_tasks = ['code_generation', 'bug_fixing', 'code_completion', 
                          'code_translation', 'code_review']
            if item['task_type'] not in valid_tasks:
                warnings.append(f"Item {index}: task_type '{item['task_type']}' non standard")
        
        # Valida language
        if 'language' in item:
            valid_languages = ['python', 'javascript', 'java', 'cpp', 'go', 'rust', 'php',
                             'typescript', 'ruby', 'c', 'csharp', 'swift']
            if item['language'].lower() not in valid_languages:
                warnings.append(f"Item {index}: language '{item['language']}' non riconosciuto")
        
        return len(errors) == 0, errors + warnings
    
    def validate_code_quality(self, item: Dict, index: int) -> Tuple[bool, List[str]]:
        """Valida la qualità del codice"""
        warnings = []
        
        output = item.get('output', '')
        
        # Check lunghezza
        if len(output) > 10000:
            warnings.append(f"Item {index}: Output molto lungo ({len(output)} caratteri)")
        
        # Check caratteri speciali problematici
        if '\x00' in output:
            warnings.append(f"Item {index}: Contiene caratteri null")
        
        # Check bilanciamento parentesi (Python)
        if item.get('language') == 'python':
            if output.count('(') != output.count(')'):
                warnings.append(f"Item {index}: Parentesi non bilanciate")
            if output.count('[') != output.count(']'):
                warnings.append(f"Item {index}: Parentesi quadre non bilanciate")
            if output.count('{') != output.count('}'):
                warnings.append(f"Item {index}: Parentesi graffe non bilanciate")
        
        return True, warnings
    
    def validate_file(self, file_path: str) -> bool:
        """Valida un file dataset completo"""
        print(f"\n{'='*70}")
        print(f"📄 VALIDAZIONE: {file_path}")
        print(f"{'='*70}\n")
        
        path = Path(file_path)
        
        # Check esistenza file
        if not path.exists():
            print(f"❌ File non trovato: {file_path}")
            return False
        
        # Check estensione
        if path.suffix != '.json':
            print(f"⚠️  Warning: File non è .json (estensione: {path.suffix})")
        
        # Carica JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Errore parsing JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Errore lettura file: {e}")
            return False
        
        print(f"✅ File caricato: {len(data)} items\n")
        
        # Valida ogni item
        self.stats['total'] = len(data)
        
        for i, item in enumerate(data):
            valid, messages = self.validate_item_structure(item, i)
            
            if valid:
                # Valida qualità
                _, quality_warnings = self.validate_code_quality(item, i)
                messages.extend(quality_warnings)
                
                self.stats['valid'] += 1
            else:
                self.stats['invalid'] += 1
            
            # Separa errori e warning
            for msg in messages:
                if 'Error' in msg or 'mancante' in msg or 'troppo corto' in msg:
                    self.errors.append(msg)
                else:
                    self.warnings.append(msg)
                    self.stats['warnings'] += 1
        
        # Statistiche
        self.print_statistics(data)
        
        # Report errori e warning
        self.print_issues()
        
        # Risultato finale
        has_errors = len(self.errors) > 0
        has_critical_warnings = self.strict and len(self.warnings) > 0
        
        print(f"\n{'='*70}")
        if has_errors or has_critical_warnings:
            print("❌ VALIDAZIONE FALLITA")
            return False
        else:
            print("✅ VALIDAZIONE SUPERATA")
            if len(self.warnings) > 0:
                print(f"⚠️  Con {len(self.warnings)} warnings (non bloccanti)")
            return True
    
    def print_statistics(self, data: List[Dict]):
        """Stampa statistiche dataset"""
        print(f"\n{'='*70}")
        print("📊 STATISTICHE DATASET")
        print(f"{'='*70}\n")
        
        print(f"Totale items:      {self.stats['total']}")
        print(f"Items validi:      {self.stats['valid']} ({self.stats['valid']/self.stats['total']*100:.1f}%)")
        print(f"Items invalidi:    {self.stats['invalid']}")
        print(f"Warning:           {self.stats['warnings']}")
        
        # Task types
        print(f"\n📋 Task Types:")
        tasks = Counter(item.get('task_type', 'unknown') for item in data)
        for task, count in tasks.most_common():
            percentage = count / len(data) * 100
            print(f"  • {task:20s}: {count:5d} ({percentage:5.1f}%)")
        
        # Languages
        print(f"\n💻 Languages:")
        languages = Counter(item.get('language', 'unknown') for item in data)
        for lang, count in languages.most_common():
            percentage = count / len(data) * 100
            print(f"  • {lang:20s}: {count:5d} ({percentage:5.1f}%)")
        
        # Lunghezze
        input_lengths = [len(item.get('input', '')) for item in data]
        output_lengths = [len(item.get('output', '')) for item in data]
        
        print(f"\n� Lunghezze:")
        print(f"  Input:")
        print(f"    Min:  {min(input_lengths):6d} caratteri")
        print(f"    Max:  {max(input_lengths):6d} caratteri")
        print(f"    Media: {sum(input_lengths)/len(input_lengths):6.0f} caratteri")
        print(f"  Output:")
        print(f"    Min:  {min(output_lengths):6d} caratteri")
        print(f"    Max:  {max(output_lengths):6d} caratteri")
        print(f"    Media: {sum(output_lengths)/len(output_lengths):6.0f} caratteri")
    
    def print_issues(self):
        """Stampa errori e warning"""
        if self.errors:
            print(f"\n{'='*70}")
            print(f"❌ ERRORI ({len(self.errors)})")
            print(f"{'='*70}\n")
            for error in self.errors[:10]:  # Primi 10
                print(f"  {error}")
            if len(self.errors) > 10:
                print(f"\n  ... e altri {len(self.errors) - 10} errori")
        
        if self.warnings:
            print(f"\n{'='*70}")
            print(f"⚠️  WARNING ({len(self.warnings)})")
            print(f"{'='*70}\n")
            for warning in self.warnings[:10]:  # Primi 10
                print(f"  {warning}")
            if len(self.warnings) > 10:
                print(f"\n  ... e altri {len(self.warnings) - 10} warning")
    
    def print_samples(self, data: List[Dict], count: int = 3):
        """Stampa esempi dal dataset"""
        print(f"\n{'='*70}")
        print(f"📝 ESEMPI DAL DATASET (primi {count})")
        print(f"{'='*70}\n")
        
        for i, item in enumerate(data[:count]):
            print(f"🔹 Esempio {i+1}")
            print(f"  Task:     {item.get('task_type', 'N/A')}")
            print(f"  Language: {item.get('language', 'N/A')}")
            print(f"  Function: {item.get('func_name', 'N/A')}")
            print(f"  Input:    {item.get('input', '')[:80]}...")
            print(f"  Output:   {item.get('output', '')[:80]}...")
            print()


def validate_all_datasets():
    """Valida tutti i dataset nella cartella datasets/"""
    dataset_dir = Path("datasets")
    
    if not dataset_dir.exists():
        print(f"❌ Directory datasets/ non trovata")
        return False
    
    json_files = list(dataset_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ Nessun file .json trovato in datasets/")
        return False
    
    print(f"\n{'='*70}")
    print(f"🔍 VALIDAZIONE MULTIPLA")
    print(f"{'='*70}")
    print(f"\nTrovati {len(json_files)} file da validare\n")
    
    results = {}
    
    for json_file in json_files:
        validator = DatasetValidator()
        success = validator.validate_file(str(json_file))
        results[json_file.name] = success
    
    # Summary
    print(f"\n{'='*70}")
    print(f"� RIEPILOGO VALIDAZIONE")
    print(f"{'='*70}\n")
    
    for filename, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {filename}")
    
    total_success = sum(1 for s in results.values() if s)
    print(f"\n{total_success}/{len(results)} file validi")
    
    return all(results.values())


def main():
    parser = argparse.ArgumentParser(
        description="Valida dataset JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Valida dataset di default
  python module/scripts/validate_dataset.py
  
  # Valida file specifico
  python module/scripts/validate_dataset.py --file datasets/dataset_classification_v2.json
  
  # Valida tutti i dataset
  python module/scripts/validate_dataset.py --all
  
  # Modalità strict (warning come errori)
  python module/scripts/validate_dataset.py --strict
  
  # Mostra esempi
  python module/scripts/validate_dataset.py --samples 5
        """
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='File dataset da validare (default: datasets/dataset_migrated.json)'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Valida tutti i dataset nella cartella datasets/'
    )
    
    parser.add_argument(
        '--strict', '-s',
        action='store_true',
        help='Modalità strict: warning come errori'
    )
    
    parser.add_argument(
        '--samples', '-n',
        type=int,
        default=0,
        help='Numero di esempi da mostrare'
    )
    
    args = parser.parse_args()
    
    # Determina file da validare
    if args.all:
        success = validate_all_datasets()
    else:
        file_path = args.file or "datasets/dataset_migrated.json"
        
        validator = DatasetValidator(strict=args.strict)
        success = validator.validate_file(file_path)
        
        # Mostra esempi se richiesto
        if args.samples > 0:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                validator.print_samples(data, args.samples)
            except Exception as e:
                print(f"❌ Errore lettura esempi: {e}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
