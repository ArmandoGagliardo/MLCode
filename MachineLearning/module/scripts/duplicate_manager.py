import os
import hashlib
from pathlib import Path
import json
class DuplicateManager:
    """
    Carica i file da self.path_files e restituisce set di hash dei path e dei contenuti.
    Per i contenuti lunghi, usa solo i primi e ultimi 50 caratteri per il confronto.
    Note: Assicurarsi che i file o i contenuti siano normalizzati. Nessun accento, carattere speciale o spazziatura e spazziatura multipla.
    """
    def __init__(self,path_files:Path, size_hash:int = 50, metadata_path:Path = None):
       
        self.path_files = path_files
        self.size_hash = size_hash
        self.hash_paths = set()
        self.hash_contents = set()
        self.hash_metadata = set()
        self.metadata_path = metadata_path

        self.hash_paths, self.hash_contents = self._load_files() 
        if self.metadata_path:
            self.hash_metadata = self._load_metadata(self.metadata_path)

    def _load_metadata(self,metadata_path:Path):
        """
        Carica i metadati da un file JSON e restituisce un set di hash dei metadati.
        """
        hash_metadata = set()
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if "hash" in entry:
                            hash_metadata.add(entry["hash"])
                    except json.JSONDecodeError:
                        continue
            return hash_metadata
        except Exception as e:
            print(f"Errore nella lettura di {metadata_path}: {e}")
            return set()

    def _load_files(self):
        """
        Carica i file da self.path_files e restituisce set di hash dei path e dei contenuti.
        """
        path_hashes = set()
        content_hashes = set()
        
        if not self.path_files.exists():
            print(f"Il percorso {self.path_files} non esiste.")
            return
        
        for filename in self.path_files.glob("*"):
            full_path = self.path_files / filename

            if not full_path.is_file():
                continue

            if filename.suffix.lower() not in {'.txt', '.csv', '.json'}:
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Errore nella lettura di {filename}: {e}")
                continue
            
            if not content:
                print(f"Il file {filename} è vuoto.")
                continue
            
            if len(content) > 100:
                start_content = content[:self.size_hash]
                end_content = content[-self.size_hash:]
                content = start_content + end_content

            path_hashes.add(self._hash_path(full_path))
            content_hashes.add(self._hash_content(content))

        return path_hashes, content_hashes

    def _hash_content(self,content:str):
        """
        Hash 256 del contenuto del file.
        """
        assert isinstance(content, str), "Il contenuto deve essere una stringa."
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _hash_path(self, path:Path):
        """
        Hash 256 del path del file.
        """
        assert isinstance(path, Path), "Il path deve essere un oggetto Path."
        return hashlib.sha256(str(path.resolve()).encode('utf-8')).hexdigest()
   
    def is_duplicate_path(self, path:Path):
        """
        Controlla se il path è duplicato.
        """
        assert isinstance(path, Path), "Il path deve essere un oggetto Path."
        return self._hash_path(path) in self.hash_paths
    
    def is_duplicate_content(self, content:str):
        """
        Controlla se il contenuto è duplicato.
        """
        assert isinstance(content, str), "Il contenuto deve essere una stringa."
        return self._hash_content(content) in self.hash_contents

    def register_path(self, path:Path):
        """
        Registra un nuovo path.
        """
        assert isinstance(path, Path), "Il path deve essere un oggetto Path."
        self.hash_paths.add(self._hash_path(path))
    
    def register_content(self, content:str):
        """
        Registra un nuovo contenuto.
        """
        assert isinstance(content, str), "Il contenuto deve essere una stringa."
        self.hash_contents.add(self._hash_content(content))
    
    def is_duplicate_metadata(self,content:str):
        """
        Controlla se il path o il contenuto sono duplicati.
        """
        return content in self.hash_metadata
    
    def register_metadata(self,content:str):
        """
        Registra un nuovo path o contenuto.
        """
        assert isinstance(content, str), "Il contenuto deve essere una stringa."
        if not self.is_duplicate_metadata(content):
            self.hash_metadata.add(self._hash_content(content))