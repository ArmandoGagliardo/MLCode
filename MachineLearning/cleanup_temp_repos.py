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


class RepoCleanup:
    """Gestisce la pulizia dei repository temporanei"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.total_size = 0
        self.total_files = 0
        self.total_dirs = 0
        
        # Directories da pulire
        self.temp_dirs = [
            Path("temp"),
            Path("repos"),
            Path("cloned_repos"),
            Path("temp_repos"),
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
    
    def cleanup(self, old_only: bool = False, auto: bool = False, force: bool = False):
        """Esegue pulizia completa"""
        print()
        print("=" * 70)
        print("🧹 CLEANUP REPOSITORY TEMPORANEI")
        print("=" * 70)
        print()
        
        if self.dry_run:
            print("⚠️  MODALITÀ DRY-RUN: nessun file verrà eliminato")
            print()
        
        # Cerca elementi
        print("🔍 Ricerca file temporanei...")
        repos = self.find_repo_dirs(old_only=old_only)
        files = self.find_temp_files(old_only=old_only)
        
        if not repos and not files:
            print()
            print("✅ Nessun file temporaneo trovato!")
            print("   Il sistema è già pulito.")
            return
        
        # Mostra riepilogo
        self.print_summary(repos, files)
        
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
            print(f"  • {self.format_size(deleted_size)} totali")
        else:
            print(f"✅ Eliminati:")
            print(f"  • {self.total_dirs} repository")
            print(f"  • {self.total_files} file temporanei")
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
  # Mostra cosa verrebbe eliminato
  python cleanup_temp_repos.py --dry-run
  
  # Elimina solo file più vecchi di 24 ore
  python cleanup_temp_repos.py --old-only --auto
  
  # Pulizia completa senza conferma
  python cleanup_temp_repos.py --force
  
  # Modalità interattiva (default)
  python cleanup_temp_repos.py
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
        help='Elimina solo file più vecchi di 24 ore'
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
    
    # Esegui cleanup
    try:
        cleaner.cleanup(
            old_only=args.old_only,
            auto=args.auto,
            force=args.force
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
