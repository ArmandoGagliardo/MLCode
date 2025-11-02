#!/usr/bin/env python3
"""
Quick test: JavaScript and Go parsers with real repos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor

def main():
    print("="*70)
    print("QUICK PARSER TEST: JavaScript & Go")
    print("="*70)
    
    # Initialize processor without cloud save
    print("\nInitializing processor...")
    processor = GitHubRepoProcessor(cloud_save=False)
    
    tests = [
        ('javascript', 'https://github.com/lodash/lodash'),
        ('go', 'https://github.com/spf13/cobra'),
    ]
    
    for language, repo_url in tests:
        repo_name = repo_url.split('/')[-1]
        print(f"\n{'='*70}")
        print(f"Testing {language.upper()}: {repo_name}")
        print('='*70)
        
        try:
            result = processor.process_repository(repo_url)
            
            files = result.get('files_processed', 0)
            funcs = result.get('functions_extracted', 0)
            status = result.get('status', 'unknown')
            
            print(f"\nResult:")
            print(f"  Status: {status}")
            print(f"  Files: {files}")
            print(f"  Functions: {funcs}")
            
            if funcs > 0:
                print(f"  ✅ {language.upper()} WORKS! ({funcs/files:.1f} functions/file)")
            else:
                print(f"  ⚠️  No functions extracted")
                
        except KeyboardInterrupt:
            print(f"\n⚠️  Test interrupted")
            break
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
