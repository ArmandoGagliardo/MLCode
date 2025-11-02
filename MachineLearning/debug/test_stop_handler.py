#!/usr/bin/env python3
"""
Test script for graceful stop handler in GitHubRepoProcessor.
Tests that Ctrl+C properly interrupts processing and saves data.
"""

import time
import signal
import sys
from github_repo_processor import GitHubRepoProcessor

def test_stop_handler():
    """Test the stop handler functionality."""
    print("=" * 70)
    print("Testing Graceful Stop Handler")
    print("=" * 70)
    print("\n📋 Test Instructions:")
    print("   1. Script will simulate processing 5 repositories")
    print("   2. Press Ctrl+C during processing")
    print("   3. Verify 'Stop requested' message appears")
    print("   4. Verify current iteration completes")
    print("   5. Verify processing stops gracefully\n")
    
    # Initialize processor
    processor = GitHubRepoProcessor(
        cloud_save=False,  # No cloud save for testing
        batch_size=10
    )
    
    print("Starting simulated repository processing...")
    print("(Press Ctrl+C to test graceful shutdown)\n")
    
    # Simulate repository processing
    total_repos = 5
    for i in range(1, total_repos + 1):
        # Check for stop request
        if not processor.should_continue():
            print(f"\n✅ Stop handled gracefully after {i-1} iterations")
            break
        
        print(f"[{i}/{total_repos}] Processing repository {i}...")
        
        # Simulate work
        for j in range(3):
            if not processor.should_continue():
                print("   Stop requested during processing")
                break
            time.sleep(1)
            print(f"   - Step {j+1}/3")
        
        print(f"✓ Repository {i} completed\n")
    else:
        print(f"\n✅ All {total_repos} repositories processed successfully")
    
    # Print final statistics
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_stop_handler()
    except KeyboardInterrupt:
        print("\n\n⚠️  KeyboardInterrupt caught but not handled properly!")
        print("The stop handler should have prevented this.")
        sys.exit(1)
