"""
Test Java con repository più semplice
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from github_repo_processor import GitHubRepoProcessor
from module.utils.duplicate_manager import DuplicateManager

# Test con repository Java più piccolo
JAVA_REPO = 'https://github.com/google/gson'

processor = GitHubRepoProcessor(cloud_save=False, batch_size=100)
processor.duplicate_manager = DuplicateManager('datasets')
processor.duplicate_manager.cache = {}

print("Testing Java extraction with gson...")
result = processor.process_repository(JAVA_REPO)

print(f"\nResults:")
print(f"  Files: {result.get('files_processed', 0)}")
print(f"  Functions: {result.get('functions_extracted', 0)}")
print(f"  Status: {result.get('status', 'unknown')}")
