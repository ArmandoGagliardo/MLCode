#!/usr/bin/env python3
"""
Test Cloud Save with Fresh Repository
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor
from module.storage.storage_manager import StorageManager

def test_fresh_repo():
    """Test with a repository that hasn't been processed yet"""
    
    print("="*70)
    print("TESTING CLOUD SAVE WITH FRESH REPOSITORY")
    print("="*70)
    
    # Test with different small repositories
    test_repos = [
        'https://github.com/psf/black',  # Python code formatter
        # 'https://github.com/pytest-dev/pytest',  # Testing framework
    ]
    
    # Check cloud storage
    storage = StorageManager()
    if not storage.connect():
        print("✗ Cloud storage connection failed")
        return
    
    print(f"\n[1] Current files in cloud storage:")
    files_before = storage.provider.list_files(prefix="datasets/code_generation/")
    print(f"  Files: {len(files_before)}")
    if files_before:
        for f in files_before[:5]:
            print(f"    - {f}")
    
    # Process repository
    print(f"\n[2] Processing fresh repository...")
    processor = GitHubRepoProcessor(cloud_save=True)
    
    for repo_url in test_repos:
        print(f"\n  Repository: {repo_url}")
        print("  " + "-"*66)
        
        stats = processor.process_repository(repo_url)
        
        print(f"\n  Results:")
        print(f"    Files processed: {stats['files_processed']}")
        print(f"    Functions extracted: {stats['functions_extracted']}")
        print(f"    Status: {stats['status']}")
    
    # Check cloud storage again
    print(f"\n[3] Checking cloud storage after processing...")
    files_after = storage.provider.list_files(prefix="datasets/code_generation/")
    print(f"  Files: {len(files_after)}")
    
    new_files_count = len(files_after) - len(files_before)
    if new_files_count > 0:
        print(f"\n  ✓ SUCCESS: {new_files_count} new file(s) uploaded!")
        print(f"  New files:")
        for f in files_after[len(files_before):]:
            print(f"    - {f}")
    elif stats['functions_extracted'] > 0:
        print(f"\n  ⚠ Functions extracted but upload status unclear")
    else:
        print(f"\n  ℹ No functions extracted (possibly all duplicates)")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_fresh_repo()
