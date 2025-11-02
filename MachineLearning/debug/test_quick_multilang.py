#!/usr/bin/env python3
"""
Quick multi-language test with small repos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor
import json

# Small repositories for quick testing
TEST_REPOS = {
    'javascript': 'https://github.com/lodash/lodash',
    'java': 'https://github.com/google/guava', 
    'cpp': 'https://github.com/nlohmann/json',
    'go': 'https://github.com/spf13/cobra',
    'rust': 'https://github.com/clap-rs/clap',
    'ruby': 'https://github.com/sinatra/sinatra',
}

def main():
    print("="*70)
    print("QUICK MULTI-LANGUAGE TEST")
    print("="*70)
    
    # Initialize processor without cloud save
    print("\nInitializing processor (cloud save disabled)...")
    processor = GitHubRepoProcessor(cloud_save=False)
    
    results = {}
    
    for language, repo_url in TEST_REPOS.items():
        repo_name = repo_url.split('/')[-1]
        print(f"\n{'='*70}")
        print(f"Testing {language.upper()}: {repo_name}")
        print('='*70)
        
        try:
            # Process repository
            result = processor.process_repository(repo_url)
            
            files = result.get('files_processed', 0)
            funcs = result.get('functions_extracted', 0)
            status = result.get('status', 'unknown')
            
            if status == 'success' and funcs > 0:
                print(f"✅ {language.upper()} WORKS!")
                print(f"   Files: {files}, Functions: {funcs}")
                results[language] = {'status': 'working', 'files': files, 'functions': funcs}
            elif status == 'success' and funcs == 0:
                print(f"⚠️  {language.upper()} - No functions extracted")
                print(f"   Files processed: {files}")
                results[language] = {'status': 'no_extraction', 'files': files, 'functions': 0}
            else:
                print(f"❌ {language.upper()} - Processing failed: {status}")
                results[language] = {'status': 'failed', 'error': status}
                
        except KeyboardInterrupt:
            print(f"\n⚠️  Skipping {language} (interrupted)")
            results[language] = {'status': 'skipped'}
            continue
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[language] = {'status': 'error', 'error': str(e)}
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    working = [lang for lang, data in results.items() if data.get('status') == 'working']
    no_extract = [lang for lang, data in results.items() if data.get('status') == 'no_extraction']
    failed = [lang for lang, data in results.items() if data.get('status') in ['failed', 'error']]
    
    print(f"\n✅ Working ({len(working)}): {', '.join(working) if working else 'None'}")
    print(f"⚠️  No extraction ({len(no_extract)}): {', '.join(no_extract) if no_extract else 'None'}")
    print(f"❌ Failed ({len(failed)}): {', '.join(failed) if failed else 'None'}")
    
    # Detailed table
    print(f"\n{'Language':<15} {'Files':<10} {'Functions':<12} {'Status'}")
    print("-"*70)
    
    for lang in sorted(results.keys()):
        data = results[lang]
        files = data.get('files', 0)
        funcs = data.get('functions', 0)
        status = data.get('status', 'unknown')
        
        if status == 'working':
            status_str = "✅ WORKING"
        elif status == 'no_extraction':
            status_str = "⚠️  NO EXTRACTION"
        else:
            status_str = f"❌ {status.upper()}"
        
        print(f"{lang:<15} {files:<10} {funcs:<12} {status_str}")
    
    # Save results
    with open('multi_language_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: multi_language_test_results.json")
    print("="*70)
    
    return len(working) > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
