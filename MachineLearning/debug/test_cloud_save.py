#!/usr/bin/env python3
"""
Test Cloud Storage Functionality
Verifies that functions are being extracted and saved to cloud storage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor
from module.storage.storage_manager import StorageManager

def test_cloud_save():
    """Test cloud storage saving with a small repository"""
    
    print("="*70)
    print("TESTING CLOUD STORAGE SAVE FUNCTIONALITY")
    print("="*70)
    
    # First check cloud connection
    print("\n[1] Testing Cloud Storage Connection...")
    storage = StorageManager()
    if not storage.connect():
        print("  ✗ Cloud storage connection FAILED")
        print("  Please check your .env file and credentials")
        return
    print("  ✓ Cloud storage connected successfully")
    
    # List existing files
    print("\n[2] Checking existing files in cloud...")
    files = storage.provider.list_files(prefix="datasets/code_generation/")
    print(f"  Found {len(files)} existing dataset files")
    if files:
        print(f"  Latest files:")
        for f in files[-3:]:
            print(f"    - {f}")
    
    # Initialize processor WITH cloud save enabled
    print("\n[3] Initializing GitHub Repository Processor...")
    processor = GitHubRepoProcessor(cloud_save=True)
    
    # Test with a small repository
    test_repo = 'https://github.com/requests/requests'
    
    print(f"\n[4] Processing repository: {test_repo}")
    print("    This will extract functions and save to cloud...")
    print("-"*70)
    
    # Process repository
    stats = processor.process_repository(test_repo)
    
    print("-"*70)
    print(f"\n[5] Processing Results:")
    print(f"  Status: {stats['status']}")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Functions extracted: {stats['functions_extracted']}")
    
    if stats['functions_extracted'] > 0:
        print("\n[6] Verifying cloud upload...")
        # List files again to see if new files were added
        new_files = storage.provider.list_files(prefix="datasets/code_generation/")
        print(f"  Total files now: {len(new_files)}")
        
        if len(new_files) > len(files):
            print(f"  ✓ NEW FILES ADDED: {len(new_files) - len(files)}")
            print(f"  Latest uploads:")
            for f in new_files[-3:]:
                print(f"    - {f}")
        else:
            print("  ⚠ WARNING: No new files detected in cloud storage")
            print("  This could mean:")
            print("    - All functions were duplicates")
            print("    - Functions didn't meet quality threshold")
            print("    - Upload failed silently")
    else:
        print("\n  ⚠ No functions extracted (could be duplicates or quality filtered)")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
    # Summary
    if stats['functions_extracted'] > 0 and len(new_files) > len(files):
        print("\n✓ SUCCESS: Functions extracted and saved to cloud storage!")
    elif stats['functions_extracted'] > 0:
        print("\n⚠ PARTIAL: Functions extracted but cloud save status unclear")
    else:
        print("\n⚠ WARNING: No functions were saved (check filters and duplicates)")

if __name__ == "__main__":
    test_cloud_save()
