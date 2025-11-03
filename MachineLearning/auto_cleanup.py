"""
Auto Cleanup After Processing

Script da integrare nel workflow per pulire automaticamente i repository
dopo l'estrazione e l'upload al cloud storage.

Funzionalità:
- Pulizia automatica dopo estrazione riuscita
- Mantiene repository in caso di errore (per debug)
- Verifica upload cloud prima di eliminare
- Logging dettagliato

Uso nel tuo codice:
    from auto_cleanup import AutoCleanup
    
    cleaner = AutoCleanup()
    
    # Dopo estrazione e upload
    if upload_success:
        cleaner.cleanup_repo(repo_path)
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class AutoCleanup:
    """Gestisce pulizia automatica dei repository temporanei"""
    
    def __init__(self, 
                 keep_on_error: bool = True,
                 keep_days: int = 0,
                 log_file: Optional[str] = None):
        """
        Args:
            keep_on_error: Mantieni repo se ci sono errori
            keep_days: Giorni da mantenere (0 = elimina subito)
            log_file: File per logging (None = console)
        """
        self.keep_on_error = keep_on_error
        self.keep_days = keep_days
        
        # Setup logging
        self.logger = logging.getLogger('AutoCleanup')
        self.logger.setLevel(logging.INFO)
        
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def get_dir_size(self, path: Path) -> int:
        """Calcola dimensione directory"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except (PermissionError, OSError):
            pass
        return total
    
    def format_size(self, size: int) -> str:
        """Formatta dimensione"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def cleanup_repo(self, repo_path: str, force: bool = False) -> bool:
        """
        Pulisce repository dopo elaborazione
        
        Args:
            repo_path: Path del repository da eliminare
            force: Forza eliminazione anche se keep_on_error
        
        Returns:
            True se eliminato, False altrimenti
        """
        path = Path(repo_path)
        
        if not path.exists():
            self.logger.warning(f"Repository non trovato: {repo_path}")
            return False
        
        if not path.is_dir():
            self.logger.warning(f"Path non è una directory: {repo_path}")
            return False
        
        # Calcola dimensione
        size = self.get_dir_size(path)
        size_str = self.format_size(size)
        
        try:
            # Elimina
            shutil.rmtree(path)
            self.logger.info(f"[OK] Eliminato repository: {path.name} ({size_str})")
            return True
        
        except Exception as e:
            self.logger.error(f"[FAIL] Errore eliminazione {path.name}: {e}")
            return False
    
    def cleanup_after_upload(self, 
                            repo_path: str,
                            upload_success: bool,
                            extracted_count: int = 0) -> bool:
        """
        Pulisce dopo upload al cloud
        
        Args:
            repo_path: Path repository
            upload_success: Se upload è riuscito
            extracted_count: Numero funzioni estratte
        
        Returns:
            True se eliminato
        """
        path = Path(repo_path)
        
        # Log contesto
        self.logger.info(
            f"Cleanup {path.name}: "
            f"upload={'[OK]' if upload_success else '[FAIL]'}, "
            f"functions={extracted_count}"
        )
        
        # Mantieni se errore e keep_on_error
        if not upload_success and self.keep_on_error:
            self.logger.info(
                f"[WARN] Mantengo {path.name} per debug (upload fallito)"
            )
            return False
        
        # Mantieni se nessuna funzione estratta
        if extracted_count == 0 and self.keep_on_error:
            self.logger.info(
                f"[WARN] Mantengo {path.name} per debug (0 funzioni estratte)"
            )
            return False
        
        # Elimina se tutto OK
        if upload_success:
            return self.cleanup_repo(str(path))
        
        return False
    
    def cleanup_old_repos(self, base_dir: str = "temp") -> int:
        """
        Pulisce repository più vecchi di keep_days
        
        Args:
            base_dir: Directory base da pulire
        
        Returns:
            Numero repository eliminati
        """
        if self.keep_days <= 0:
            return 0
        
        base_path = Path(base_dir)
        if not base_path.exists():
            return 0
        
        deleted = 0
        threshold = datetime.now().timestamp() - (self.keep_days * 86400)
        
        try:
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue
                
                # Check età
                mtime = item.stat().st_mtime
                if mtime < threshold:
                    if self.cleanup_repo(str(item)):
                        deleted += 1
        
        except Exception as e:
            self.logger.error(f"Errore cleanup old repos: {e}")
        
        if deleted > 0:
            self.logger.info(f"[CLEANUP] Eliminati {deleted} repository vecchi")
        
        return deleted


# Funzioni helper per integrazione facile

def cleanup_after_success(repo_path: str, logger: Optional[logging.Logger] = None):
    """Helper per pulizia dopo estrazione riuscita"""
    cleaner = AutoCleanup()
    if logger:
        cleaner.logger = logger
    
    return cleaner.cleanup_repo(repo_path)


def cleanup_if_uploaded(repo_path: str, upload_ok: bool, functions: int = 0):
    """Helper per pulizia condizionale"""
    cleaner = AutoCleanup(keep_on_error=True)
    return cleaner.cleanup_after_upload(repo_path, upload_ok, functions)


# Esempio integrazione in github_repo_processor.py:
"""
from auto_cleanup import cleanup_if_uploaded

# ... dopo estrazione ...

# Salva locale
local_file = self._save_dataset_local(dataset, task_type, repo_name, provider_type)

# Upload cloud (se configurato)
upload_success = False
if self.storage_manager:
    remote_path = f"datasets/{task_type}/{local_file.name}"
    upload_success = self.storage_manager.upload_file(str(local_file), remote_path)

# Cleanup automatico
if repo_path:
    cleanup_if_uploaded(
        repo_path=repo_path,
        upload_ok=upload_success,
        functions=len(dataset)
    )
"""


if __name__ == "__main__":
    # Test
    print("🧹 Auto Cleanup - Test")
    print()
    
    cleaner = AutoCleanup(keep_on_error=True)
    
    # Simula scenari
    print("Scenario 1: Upload riuscito, 100 funzioni estratte")
    result = cleaner.cleanup_after_upload(
        repo_path="temp/test_repo",
        upload_success=True,
        extracted_count=100
    )
    print(f"Eliminato: {result}")
    print()
    
    print("Scenario 2: Upload fallito, 50 funzioni estratte")
    result = cleaner.cleanup_after_upload(
        repo_path="temp/test_repo",
        upload_success=False,
        extracted_count=50
    )
    print(f"Eliminato: {result} (mantenuto per debug)")
    print()
    
    print("Scenario 3: Upload riuscito, 0 funzioni estratte")
    result = cleaner.cleanup_after_upload(
        repo_path="temp/test_repo",
        upload_success=True,
        extracted_count=0
    )
    print(f"Eliminato: {result} (mantenuto per debug)")
    print()
