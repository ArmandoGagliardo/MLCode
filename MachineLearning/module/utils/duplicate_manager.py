"""
Duplicate Manager

Manages duplicate detection for extracted code to avoid redundant training data.
Uses hash-based detection and stores metadata for tracking.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class DuplicateManager:
    """
    Manages duplicate detection for code snippets and functions.
    """

    def __init__(self, storage_path: str = "datasets/duplicates_cache.json"):
        """
        Initialize the duplicate manager.

        Args:
            storage_path: Path to store duplicate hashes cache
        """
        self.storage_path = Path(storage_path)
        self.hashes: Set[str] = set()
        self.metadata: Dict[str, Dict] = {}
        
        # Create directory if it doesn't exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing hashes
        self._load_cache()

    def _load_cache(self):
        """Load existing duplicate cache from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.hashes = set(data.get('hashes', []))
                    self.metadata = data.get('metadata', {})
                logger.info(f"Loaded {len(self.hashes)} hashes from cache")
            except Exception as e:
                logger.warning(f"Failed to load duplicate cache: {e}")
                self.hashes = set()
                self.metadata = {}
        else:
            logger.info("No existing duplicate cache found, starting fresh")

    def _save_cache(self):
        """Save duplicate cache to disk."""
        try:
            data = {
                'hashes': list(self.hashes),
                'metadata': self.metadata
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save duplicate cache: {e}")

    def generate_hash(self, content: str, algorithm: str = 'md5') -> str:
        """
        Generate hash for content.

        Args:
            content: Content to hash
            algorithm: Hashing algorithm ('md5', 'sha256')

        Returns:
            Hexadecimal hash string
        """
        # Normalize content (strip whitespace, lowercase)
        normalized = content.strip().lower()
        
        # Remove common variations
        normalized = normalized.replace(' ', '').replace('\n', '').replace('\t', '')
        
        # Generate hash
        if algorithm == 'md5':
            return hashlib.md5(normalized.encode('utf-8')).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def is_duplicate(self, hash_value: str, metadata: Optional[Dict] = None) -> bool:
        """
        Check if a hash is a duplicate.

        Args:
            hash_value: Hash to check
            metadata: Optional metadata to store if not duplicate

        Returns:
            True if duplicate, False otherwise
        """
        is_dup = hash_value in self.hashes
        
        if is_dup:
            logger.debug(f"Duplicate detected: {hash_value}")
        
        return is_dup

    def add_item(self, hash_value: str, metadata: Optional[Dict] = None):
        """
        Add a new item to the duplicate tracker.

        Args:
            hash_value: Hash of the item
            metadata: Optional metadata about the item
        """
        self.hashes.add(hash_value)
        
        if metadata:
            self.metadata[hash_value] = metadata

    def remove_item(self, hash_value: str):
        """
        Remove an item from the duplicate tracker.

        Args:
            hash_value: Hash to remove
        """
        if hash_value in self.hashes:
            self.hashes.remove(hash_value)
        
        if hash_value in self.metadata:
            del self.metadata[hash_value]

    def is_duplicate_content(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Check if content is duplicate and add if not.

        Args:
            content: Content to check
            metadata: Optional metadata

        Returns:
            True if duplicate, False otherwise
        """
        hash_value = self.generate_hash(content)
        
        if self.is_duplicate(hash_value, metadata):
            return True
        
        # Not duplicate, add it
        self.add_item(hash_value, metadata)
        return False

    def get_stats(self) -> Dict:
        """
        Get duplicate manager statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_hashes': len(self.hashes),
            'metadata_count': len(self.metadata),
            'cache_path': str(self.storage_path)
        }

    def clear_cache(self):
        """Clear all cached duplicates."""
        self.hashes.clear()
        self.metadata.clear()
        logger.info("Cleared duplicate cache")

    def save(self):
        """Save current state to disk."""
        self._save_cache()
        logger.info(f"Saved {len(self.hashes)} hashes to cache")

    def __len__(self):
        """Return number of tracked items."""
        return len(self.hashes)

    def __contains__(self, hash_value: str):
        """Check if hash is tracked."""
        return hash_value in self.hashes

    def __del__(self):
        """Save cache on deletion."""
        try:
            self._save_cache()
        except:
            pass


# Example usage
if __name__ == "__main__":
    # Test duplicate manager
    manager = DuplicateManager()
    
    # Test code snippets
    code1 = "def hello(): return 'world'"
    code2 = "def hello():\n    return 'world'"  # Same but different formatting
    code3 = "def goodbye(): return 'world'"
    
    # Check duplicates
    print(f"Code1 duplicate: {manager.is_duplicate_content(code1, {'name': 'hello1'})}")  # False
    print(f"Code2 duplicate: {manager.is_duplicate_content(code2, {'name': 'hello2'})}")  # True (same as code1)
    print(f"Code3 duplicate: {manager.is_duplicate_content(code3, {'name': 'goodbye'})}")  # False
    
    # Stats
    print(f"Stats: {manager.get_stats()}")
    
    # Save
    manager.save()
