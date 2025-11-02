#!/usr/bin/env python3
"""
Final test: Extract functions and save to cloud
"""

from github_repo_processor import GitHubRepoProcessor
from module.storage.storage_manager import StorageManager

print("="*70)
print("FINAL TEST: CLOUD UPLOAD")
print("="*70)

# Clear duplicate cache for fresh test
import os
if os.path.exists('datasets/duplicates_cache.json'):
    os.remove('datasets/duplicates_cache.json')
    print("[INFO] Cleared duplicate cache for fresh test")

# Initialize processor with cloud save
print("\n[1] Initializing processor with cloud save enabled...")
processor = GitHubRepoProcessor(cloud_save=True)

# Process small repo
repo_url = 'https://github.com/psf/black'
print(f"\n[2] Processing: {repo_url}")
print("-"*70)

stats = processor.process_repository(repo_url)

print("-"*70)
print(f"\n[3] Results:")
print(f"  Files processed: {stats['files_processed']}")
print(f"  Functions extracted: {stats['functions_extracted']}")
print(f"  Status: {stats['status']}")

# Check cloud storage
if stats['functions_extracted'] > 0:
    print(f"\n[4] Checking cloud storage...")
    storage = StorageManager()
    if storage.connect():
        files = storage.provider.list_files(prefix="datasets/code_generation/")
        print(f"  Total files in cloud: {len(files)}")
        if files:
            print(f"  Latest files:")
            for f in files[-3:]:
                print(f"    - {f}")
            print(f"\n  [SUCCESS] Functions saved to cloud!")
        else:
            print(f"  [WARNING] No files found in cloud")
    else:
        print(f"  [ERROR] Could not connect to cloud storage")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
