#!/usr/bin/env python3
"""
Interactive test for graceful stop handler.
Run this and press Ctrl+C to test the graceful shutdown.
"""

import time
from github_repo_processor import GitHubRepoProcessor

def main():
    print("=" * 70)
    print("🛑 Interactive Graceful Stop Test")
    print("=" * 70)
    print("\n📋 Instructions:")
    print("   - Processing will simulate 10 repositories")
    print("   - Press Ctrl+C ONCE to request graceful stop")
    print("   - Current repository will complete")
    print("   - Press Ctrl+C TWICE to force quit\n")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Initialize processor
    processor = GitHubRepoProcessor(cloud_save=False, batch_size=10)
    
    print("\n🚀 Processing repositories...")
    print("=" * 70 + "\n")
    
    # Simulate repository processing
    total_repos = 10
    for i in range(1, total_repos + 1):
        # Check for stop request
        if not processor.should_continue():
            print(f"\n{'='*70}")
            print(f"🛑 GRACEFUL STOP: Completed {i-1}/{total_repos} repositories")
            print(f"{'='*70}")
            print("✅ Data saved successfully!")
            print("   All processed data has been preserved.")
            return
        
        print(f"📦 [{i}/{total_repos}] Processing repository {i}...")
        
        # Simulate work with stop checks
        for j in range(5):
            if not processor.should_continue():
                print(f"   ⚠️  Stop requested, finishing repository {i}...")
                break
            time.sleep(0.5)  # Simulate processing time
            print(f"   {'▓' * (j+1)}{'░' * (5-j-1)} {(j+1)*20}%")
        
        print(f"   ✅ Repository {i} completed\n")
        time.sleep(0.5)
    
    # All completed
    print(f"\n{'='*70}")
    print(f"🎉 ALL DONE: Successfully processed {total_repos}/{total_repos} repositories")
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ FORCE QUIT: Second Ctrl+C detected")
        print("⚠️  Warning: Some data may not have been saved!")
        exit(1)
