#!/usr/bin/env python3
"""
Test multi-language extraction dopo i fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor

def test_language(lang, repo_url):
    """Test extraction for a language"""
    print(f"\n{'='*70}")
    print(f"Testing {lang.upper()}: {repo_url.split('/')[-1]}")
    print('='*70)
    
    processor = GitHubRepoProcessor(cloud_save=False)
    
    try:
        result = processor.process_repository(repo_url)
        
        files = result.get('files_processed', 0)
        funcs = result.get('functions_extracted', 0)
        status = result.get('status', 'unknown')
        
        print(f"\nResult:")
        print(f"  Status: {status}")
        print(f"  Files processed: {files}")
        print(f"  Functions extracted: {funcs}")
        
        if funcs > 0:
            rate = funcs / files if files > 0 else 0
            print(f"  ✅ SUCCESS! ({rate:.1f} functions/file)")
            return True
        else:
            print(f"  ⚠️  No functions extracted")
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def main():
    print("="*70)
    print("MULTI-LANGUAGE PARSER TEST (after fixes)")
    print("="*70)
    
    tests = [
        ('Python', 'https://github.com/psf/requests'),
        ('JavaScript', 'https://github.com/axios/axios'),
        ('Go', 'https://github.com/spf13/cobra'),
        ('Rust', 'https://github.com/clap-rs/clap'),
    ]
    
    results = {}
    
    for lang, repo_url in tests:
        success = test_language(lang, repo_url)
        results[lang] = success
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    working = [lang for lang, success in results.items() if success]
    failed = [lang for lang, success in results.items() if not success]
    
    print(f"\n✅ Working: {', '.join(working) if working else 'None'}")
    print(f"❌ Not working: {', '.join(failed) if failed else 'None'}")
    
    print(f"\nTotal: {len(working)}/{len(results)} languages working")
    print("="*70)

if __name__ == "__main__":
    main()
