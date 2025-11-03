"""
Cleanup Temporary Repository Files

Script per ripulire i file locali dei repository clonati quando non vengono
salvati sullo storage esterno. Utile per:
- Liberare spazio disco
- Rimuovere repository temporanei dopo estrazione
- Pulizia automatica dopo fallimento upload

Uso:
    python cleanup_temp_repos.py                    # Modalità interattiva
    python cleanup_temp_repos.py --auto             # Pulizia automatica
    python cleanup_temp_repos.py --dry-run          # Solo mostra cosa verrebbe eliminato
    python cleanup_temp_repos.py --old-only         # Solo file > 24 ore
    python cleanup_temp_repos.py --force            # Elimina tutto senza conferma

Esempio:
    # Mostra cosa verrebbe eliminato
    python cleanup_temp_repos.py --dry-run
    
    # Elimina file più vecchi di 24 ore
    python cleanup_temp_repos.py --old-only --auto
    
    # Pulizia completa
    python cleanup_temp_repos.py --force
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOCAL_DATASET_PATH


class RepoCleanup:
    """Gestisce la pulizia dei repository temporanei"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.total_size = 0
        self.total_files = 0
        self.total_dirs = 0
        
        # Directories da pulire (repository clonati temporanei)
        self.temp_dirs = [
            Path("temp"),
            Path("repos"),
            Path("cloned_repos"),
            Path("temp_repos"),
        ]
        
        # Directories dataset locali (non vengono eliminate di default)
        # Path corretto: stesso path dello storage cloud ma con local_backup
        # Importato da config.py per mantenere coerenza
        self.dataset_dirs = [
            LOCAL_DATASET_PATH,  # dataset_storage/local_backup/code_generation
        ]
        
        # Pattern da mantenere (whitelist)
        self.keep_patterns = [
            ".git",
            ".env",
            "venv",
            ".venv",
            "node_modules",
        ]
    
    def get_dir_size(self, path: Path) -> int:
        """Calcola dimensione totale di una directory"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except (PermissionError, OSError):
            pass
        return total
    
    def format_size(self, size: int) -> str:
        """Formatta dimensione in formato leggibile"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def is_old_file(self, path: Path, hours: int = 24) -> bool:
        """Verifica se file è più vecchio di N ore"""
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            threshold = datetime.now() - timedelta(hours=hours)
            return mtime < threshold
        except (OSError, PermissionError):
            return False
    
    def should_keep(self, path: Path) -> bool:
        """Verifica se path deve essere mantenuto"""
        path_str = str(path)
        for pattern in self.keep_patterns:
            if pattern in path_str:
                return True
        return False
    
    def find_repo_dirs(self, old_only: bool = False) -> List[Tuple[Path, int, datetime]]:
        """Trova tutte le directory di repository da eliminare"""
        repo_dirs = []
        
        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue
            
            try:
                for item in temp_dir.iterdir():
                    if not item.is_dir():
                        continue
                    
                    if self.should_keep(item):
                        continue
                    
                    # Filtra per età se richiesto
                    if old_only and not self.is_old_file(item, hours=24):
                        continue
                    
                    size = self.get_dir_size(item)
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    repo_dirs.append((item, size, mtime))
            
            except (PermissionError, OSError) as e:
                if self.verbose:
                    print(f"⚠️  Errore accesso {temp_dir}: {e}")
        
        return sorted(repo_dirs, key=lambda x: x[2], reverse=True)
    
    def find_temp_files(self, old_only: bool = False) -> List[Tuple[Path, int, datetime]]:
        """Trova file temporanei da eliminare"""
        temp_files = []
        
        # Pattern file temporanei
        patterns = [
            "*.tmp",
            "*.temp",
            "*.cache",
            "*_temp_*",
            "temp_*",
        ]
        
        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue
            
            try:
                for pattern in patterns:
                    for file_path in temp_dir.rglob(pattern):
                        if not file_path.is_file():
                            continue
                        
                        if old_only and not self.is_old_file(file_path, hours=24):
                            continue
                        
                        size = file_path.stat().st_size
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        temp_files.append((file_path, size, mtime))
            
            except (PermissionError, OSError) as e:
                if self.verbose:
                    print(f"⚠️  Errore ricerca {temp_dir}: {e}")
        
        return temp_files
    
    def find_dataset_files(self, old_only: bool = False, min_age_hours: int = 168, 
                          filter_repo: str = None) -> List[Tuple[Path, int, datetime]]:
        """
        Trova file dataset da eliminare
        
        Args:
            old_only: Se True, filtra per età
            min_age_hours: Età minima in ore (default: 168 = 7 giorni)
            filter_repo: Se specificato, cerca solo dataset di un repository specifico (es: 'black', 'requests')
        """
        dataset_files = []
        
        for dataset_dir in self.dataset_dirs:
            if not dataset_dir.exists():
                continue
            
            try:
                # Trova tutti i file JSON eccetto summary/analysis
                for file_path in dataset_dir.glob("*.json"):
                    if not file_path.is_file():
                        continue
                    
                    # Skip file speciali
                    if file_path.name.startswith('analysis_') or file_path.name.startswith('summary_'):
                        continue
                    
                    # Filtra per repository se specificato
                    if filter_repo and not file_path.name.startswith(f"{filter_repo}_"):
                        continue
                    
                    # Filtra per età se richiesto
                    if old_only and not self.is_old_file(file_path, hours=min_age_hours):
                        continue
                    
                    size = file_path.stat().st_size
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    dataset_files.append((file_path, size, mtime))
            
            except (PermissionError, OSError) as e:
                if self.verbose:
                    print(f"⚠️  Errore ricerca {dataset_dir}: {e}")
        
        return dataset_files
    
    def get_dataset_stats_by_repo(self) -> dict:
        """
        Ottiene statistiche sui dataset raggruppate per repository
        
        Returns:
            Dict con repo_name -> {'count': int, 'size': int, 'files': list}
        """
        stats = {}
        
        for dataset_dir in self.dataset_dirs:
            if not dataset_dir.exists():
                continue
            
            try:
                for file_path in dataset_dir.glob("*.json"):
                    if not file_path.is_file():
                        continue
                    
                    # Skip file speciali
                    if file_path.name.startswith('analysis_') or file_path.name.startswith('summary_'):
                        continue
                    
                    # Estrai nome repository (es: "black_20251102_143831_51.json" -> "black")
                    repo_name = file_path.stem.split('_')[0]
                    
                    if repo_name not in stats:
                        stats[repo_name] = {'count': 0, 'size': 0, 'files': []}
                    
                    size = file_path.stat().st_size
                    stats[repo_name]['count'] += 1
                    stats[repo_name]['size'] += size
                    stats[repo_name]['files'].append(file_path)
            
            except (PermissionError, OSError) as e:
                if self.verbose:
                    print(f"⚠️  Errore analisi {dataset_dir}: {e}")
        
        return stats
    
    def show_dataset_stats(self, group_by_repo: bool = True):
        """
        Mostra statistiche sui dataset locali
        
        Args:
            group_by_repo: Se True, raggruppa per repository
        """
        print()
        print("=" * 70)
        print("📊 STATISTICHE DATASET LOCALI")
        print("=" * 70)
        print()
        
        if group_by_repo:
            # Statistiche raggruppate per repository
            stats = self.get_dataset_stats_by_repo()
            
            if not stats:
                print("✅ Nessun dataset trovato")
                print()
                return
            
            # Ordina per dimensione
            sorted_repos = sorted(stats.items(), key=lambda x: x[1]['size'], reverse=True)
            
            total_files = 0
            total_size = 0
            
            for repo_name, data in sorted_repos:
                total_files += data['count']
                total_size += data['size']
                
                print(f"📦 {repo_name}")
                print(f"   File: {data['count']}")
                print(f"   Dimensione: {self.format_size(data['size'])}")
                print(f"   Media: {self.format_size(data['size'] // data['count'])} per file")
                print()
            
            print("=" * 70)
            print(f"📊 Totale: {len(stats)} repository, {total_files} file, {self.format_size(total_size)}")
            print("=" * 70)
            print()
        else:
            # Statistiche per directory
            total_files = 0
            total_size = 0
            
            for dataset_dir in self.dataset_dirs:
                if not dataset_dir.exists():
                    continue
                
                files = [f for f in dataset_dir.glob("*.json") 
                        if f.is_file() and not f.name.startswith('analysis_') and not f.name.startswith('summary_')]
                
                if files:
                    dir_size = sum(f.stat().st_size for f in files)
                    total_files += len(files)
                    total_size += dir_size
                    
                    print(f"📁 {dataset_dir}")
                    print(f"   File: {len(files)}")
                    print(f"   Dimensione: {self.format_size(dir_size)}")
                    print()
            
            print("=" * 70)
            print(f"Totale: {total_files} file, {self.format_size(total_size)}")
            print("=" * 70)
            print()
    
    def print_summary(self, repos: List[Tuple[Path, int, datetime]], 
                      files: List[Tuple[Path, int, datetime]]):
        """Stampa riepilogo trovato"""
        print()
        print("=" * 70)
        print("🗑️  ELEMENTI DA ELIMINARE")
        print("=" * 70)
        print()
        
        if repos:
            print(f"📁 Repository Clonati: {len(repos)}")
            print()
            for path, size, mtime in repos[:10]:  # Mostra primi 10
                age = datetime.now() - mtime
                age_str = f"{age.days}d {age.seconds//3600}h" if age.days > 0 else f"{age.seconds//3600}h {(age.seconds//60)%60}m"
                print(f"  • {path.name}")
                print(f"    Dimensione: {self.format_size(size)}")
                print(f"    Età: {age_str}")
                print(f"    Path: {path}")
                print()
            
            if len(repos) > 10:
                print(f"  ... e altri {len(repos) - 10} repository")
                print()
        
        if files:
            print(f"📄 File Temporanei: {len(files)}")
            print()
            for path, size, mtime in files[:10]:  # Mostra primi 10
                age = datetime.now() - mtime
                age_str = f"{age.days}d {age.seconds//3600}h" if age.days > 0 else f"{age.seconds//3600}h {(age.seconds//60)%60}m"
                print(f"  • {path.name}")
                print(f"    Dimensione: {self.format_size(size)}")
                print(f"    Età: {age_str}")
                print()
            
            if len(files) > 10:
                print(f"  ... e altri {len(files) - 10} file")
                print()
        
        # Totali
        total_size = sum(size for _, size, _ in repos) + sum(size for _, size, _ in files)
        print("=" * 70)
        print(f"Totale da liberare: {self.format_size(total_size)}")
        print("=" * 70)
        print()
    
    def delete_items(self, repos: List[Tuple[Path, int, datetime]], 
                     files: List[Tuple[Path, int, datetime]]) -> Tuple[int, int]:
        """Elimina repository e file"""
        deleted_size = 0
        deleted_count = 0
        
        # Elimina repository
        for path, size, _ in repos:
            try:
                if self.dry_run:
                    print(f"[DRY-RUN] Eliminerei: {path}")
                else:
                    shutil.rmtree(path)
                    if self.verbose:
                        print(f"✅ Eliminato: {path} ({self.format_size(size)})")
                
                deleted_size += size
                deleted_count += 1
                self.total_dirs += 1
            
            except Exception as e:
                if self.verbose:
                    print(f"❌ Errore eliminazione {path}: {e}")
        
        # Elimina file
        for path, size, _ in files:
            try:
                if self.dry_run:
                    print(f"[DRY-RUN] Eliminerei: {path}")
                else:
                    path.unlink()
                    if self.verbose:
                        print(f"✅ Eliminato: {path} ({self.format_size(size)})")
                
                deleted_size += size
                deleted_count += 1
                self.total_files += 1
            
            except Exception as e:
                if self.verbose:
                    print(f"❌ Errore eliminazione {path}: {e}")
        
        return deleted_count, deleted_size
    
    def cleanup(self, old_only: bool = False, auto: bool = False, force: bool = False, 
                include_datasets: bool = False, filter_repo: str = None, 
                datasets_only: bool = False):
        """
        Esegue pulizia completa
        
        Args:
            old_only: Pulisci solo file vecchi
            auto: Esegui senza conferma
            force: Forza eliminazione
            include_datasets: Include anche i dataset locali (default: False)
            filter_repo: Filtra per repository specifico (es: 'black', 'requests')
            datasets_only: Pulisci SOLO i dataset (ignora temp repos)
        """
        print()
        print("=" * 70)
        if datasets_only:
            print("🧹 CLEANUP DATASET")
            if filter_repo:
                print(f"   Repository: {filter_repo}")
        else:
            print("🧹 CLEANUP REPOSITORY TEMPORANEI")
            if include_datasets:
                print("   + DATASET LOCALI")
                if filter_repo:
                    print(f"   Repository: {filter_repo}")
        print("=" * 70)
        print()
        
        if self.dry_run:
            print("⚠️  MODALITÀ DRY-RUN: nessun file verrà eliminato")
            print()
        
        # Cerca elementi
        repos = []
        files = []
        
        if not datasets_only:
            print("🔍 Ricerca file temporanei...")
            repos = self.find_repo_dirs(old_only=old_only)
            files = self.find_temp_files(old_only=old_only)
        
        # Cerca dataset se richiesto
        datasets = []
        if include_datasets or datasets_only:
            print("🔍 Ricerca dataset locali...")
            if filter_repo:
                print(f"   Filtrando per repository: {filter_repo}")
            # Per i dataset usa età minima di 7 giorni se old_only
            datasets = self.find_dataset_files(
                old_only=old_only, 
                min_age_hours=168,
                filter_repo=filter_repo
            )
        
        if not repos and not files and not datasets:
            print()
            if datasets_only:
                print("✅ Nessun dataset trovato!")
            else:
                print("✅ Nessun file temporaneo trovato!")
            print("   Il sistema è già pulito.")
            return
        
        # Mostra riepilogo
        self.print_summary(repos, files)
        
        # Mostra dataset se inclusi
        if datasets:
            print()
            print("=" * 70)
            print(f"📦 DATASET LOCALI DA ELIMINARE: {len(datasets)}")
            print("=" * 70)
            print()
            for path, size, mtime in datasets[:10]:
                age = datetime.now() - mtime
                age_str = f"{age.days}d" if age.days > 0 else f"{age.seconds//3600}h"
                print(f"  • {path.name}")
                print(f"    Dimensione: {self.format_size(size)}")
                print(f"    Età: {age_str}")
                print()
            
            if len(datasets) > 10:
                print(f"  ... e altri {len(datasets) - 10} dataset")
                print()
            
            dataset_size = sum(size for _, size, _ in datasets)
            print(f"Totale dataset: {self.format_size(dataset_size)}")
            print()
        
        # Conferma
        if not auto and not force and not self.dry_run:
            response = input("Procedere con l'eliminazione? (s/n): ").lower()
            if response != 's':
                print("❌ Operazione annullata")
                return
        
        # Elimina
        print()
        print("🗑️  Eliminazione in corso...")
        print()
        
        deleted_count, deleted_size = self.delete_items(repos, files)
        
        # Elimina dataset se inclusi
        dataset_deleted_count = 0
        dataset_deleted_size = 0
        if datasets:
            dataset_deleted_count, dataset_deleted_size = self.delete_items([], datasets)
            deleted_count += dataset_deleted_count
            deleted_size += dataset_deleted_size
        
        # Riepilogo finale
        print()
        print("=" * 70)
        print("📊 RIEPILOGO PULIZIA")
        print("=" * 70)
        print()
        
        if self.dry_run:
            print(f"Verrebbero eliminati:")
            print(f"  • {len(repos)} repository")
            print(f"  • {len(files)} file temporanei")
            if datasets:
                print(f"  • {len(datasets)} dataset")
            print(f"  • {self.format_size(deleted_size)} totali")
        else:
            print(f"✅ Eliminati:")
            print(f"  • {self.total_dirs} repository")
            print(f"  • {self.total_files} file temporanei")
            if datasets:
                print(f"  • {dataset_deleted_count} dataset")
            print(f"  • {self.format_size(deleted_size)} liberati")
        
        print()
        print("=" * 70)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup repository temporanei e file locali",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Mostra statistiche dataset (raggruppati per repository)
  python cleanup_temp_repos.py --show-datasets
  
  # Elimina SOLO i dataset del repository 'black'
  python cleanup_temp_repos.py --datasets-only --repo black --auto
  
  # Elimina TUTTI i dataset (tutti i repository)
  python cleanup_temp_repos.py --datasets-only --force
  
  # Elimina dataset più vecchi di 7 giorni
  python cleanup_temp_repos.py --datasets-only --old-only --auto
  
  # Elimina dataset 'requests' con preview
  python cleanup_temp_repos.py --datasets-only --repo requests --dry-run
  
  # Pulizia completa: repository temporanei + dataset
  python cleanup_temp_repos.py --include-datasets --force
  
  # Elimina solo repository temporanei (come prima)
  python cleanup_temp_repos.py --auto
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostra cosa verrebbe eliminato senza eliminare'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Esegui senza chiedere conferma'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Elimina tutto senza conferma (implica --auto)'
    )
    
    parser.add_argument(
        '--old-only',
        action='store_true',
        help='Elimina solo file più vecchi di 24 ore (repo temp) o 7 giorni (dataset)'
    )
    
    parser.add_argument(
        '--include-datasets',
        action='store_true',
        help='Include anche i dataset locali nella pulizia'
    )
    
    parser.add_argument(
        '--show-datasets',
        action='store_true',
        help='Mostra statistiche sui dataset locali senza eliminare'
    )
    
    parser.add_argument(
        '--datasets-only',
        action='store_true',
        help='Pulisci SOLO i dataset (ignora repository temporanei)'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        help='Filtra per repository specifico (es: black, requests, flask)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Modalità silenziosa (solo errori)'
    )
    
    args = parser.parse_args()
    
    # Se force, abilita auto
    if args.force:
        args.auto = True
    
    # Crea cleaner
    cleaner = RepoCleanup(
        dry_run=args.dry_run,
        verbose=not args.quiet
    )
    
    # Solo mostra statistiche dataset
    if args.show_datasets:
        cleaner.show_dataset_stats(group_by_repo=True)
        sys.exit(0)
    
    # Se datasets_only è specificato, abilita automaticamente include_datasets
    if args.datasets_only:
        args.include_datasets = True
    
    # Esegui cleanup
    try:
        cleaner.cleanup(
            old_only=args.old_only,
            auto=args.auto,
            force=args.force,
            include_datasets=args.include_datasets,
            filter_repo=args.repo,
            datasets_only=args.datasets_only
        )
    except KeyboardInterrupt:
        print()
        print("❌ Operazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
