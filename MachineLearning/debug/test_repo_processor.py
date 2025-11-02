#!/usr/bin/env python3
"""
Test the fixes for github_repo_processor.
Tests handling of missing 'name' field and Windows cleanup issues.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from github_repo_processor import GitHubRepoProcessor

def test_small_repo():
    """Test processing a small repository."""
    print("="*70)
    print("Testing GitHub Repo Processor Fixes")
    print("="*70)
    print()
    
    # Create processor
    processor = GitHubRepoProcessor(
        cloud_save=False,  # Don't save to cloud for test
        batch_size=10
    )
    
    # Test with a small, simple repository
    test_repos = [
        "https://github.com/octocat/Hello-World",  # Very small test repo
    ]
    
    print(f"Testing with {len(test_repos)} repository...")
    print()
    
    for i, repo_url in enumerate(test_repos, 1):
        print(f"[{i}/{len(test_repos)}] Processing: {repo_url}")
        print("-" * 70)
        
        try:
            stats = processor.process_repository(repo_url)
            
            print(f"\nResults:")
            print(f"  Status: {stats['status']}")
            print(f"  Files processed: {stats['files_processed']}")
            print(f"  Functions extracted: {stats['functions_extracted']}")
            
            if stats['status'] == 'success':
                print(f"  [OK] Repository processed successfully!")
            else:
                print(f"  [ERROR] Status: {stats['status']}")
                if 'error' in stats:
                    print(f"  Error: {stats['error']}")
                    
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("="*70)
    print("Test completed!")
    print("="*70)

if __name__ == "__main__":
    try:
        test_small_repo()
    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
