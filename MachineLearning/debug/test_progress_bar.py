#!/usr/bin/env python3
"""
Test script to verify progress bar functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor

def test_progress_bar():
    """Test the progress bar with a small repository"""
    
    print("="*70)
    print("TESTING PROGRESS BAR FUNCTIONALITY")
    print("="*70)
    
    # Initialize processor (without cloud save for testing)
    processor = GitHubRepoProcessor(cloud_save=False)
    
    # Test with a small repository
    test_repos = [
        'https://github.com/requests/requests',  # Small Python repo
    ]
    
    print("\n[TEST] Processing 1 repository to demonstrate progress bar...")
    print("Watch for:")
    print("  - Progress bar showing file processing")
    print("  - Clean output without verbose logs")
    print("  - Function extraction count")
    print("-"*70)
    
    # Process just one repository
    processor.process_repository(test_repos[0])
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nExpected improvements:")
    print("  ✓ No docstring spam in terminal")
    print("  ✓ Progress bar shows percentage")
    print("  ✓ Real-time function count")
    print("  ✓ Cleaner output overall")

if __name__ == "__main__":
    test_progress_bar()
