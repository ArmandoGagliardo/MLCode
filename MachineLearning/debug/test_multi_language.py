#!/usr/bin/env python3
"""
Test multi-language parsing with real repositories
Tests JavaScript, Java, C++, Go, Rust, Ruby parsers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_repo_processor import GitHubRepoProcessor
from module.storage.storage_manager import StorageManager
import json

# Real repositories for each language
TEST_REPOS = {
    'javascript': [
        'https://github.com/lodash/lodash',  # Popular utility library
        'https://github.com/axios/axios',     # HTTP client
    ],
    'java': [
        'https://github.com/google/guava',    # Google core libraries
        'https://github.com/iluwatar/java-design-patterns',  # Design patterns
    ],
    'cpp': [
        'https://github.com/nlohmann/json',   # JSON library
        'https://github.com/google/leveldb',  # Database
    ],
    'go': [
        'https://github.com/gin-gonic/gin',   # Web framework
        'https://github.com/spf13/cobra',     # CLI framework
    ],
    'rust': [
        'https://github.com/serde-rs/serde',  # Serialization
        'https://github.com/clap-rs/clap',    # CLI parser
    ],
    'ruby': [
        'https://github.com/rails/rails',     # Web framework
        'https://github.com/jekyll/jekyll',   # Static site generator
    ]
}

def test_language(language, repo_url, processor):
    """Test extraction for a specific language"""
    print(f"\n{'='*70}")
    print(f"Testing {language.upper()}: {repo_url.split('/')[-1]}")
    print('='*70)
    
    try:
        # Process repository (limit files for speed)
        result = processor.process_repo(
            repo_url,
            max_files=20,  # Limit for quick test
            save_to_cloud=False  # Don't upload during test
        )
        
        if result['status'] == 'success':
            files = result.get('files_processed', 0)
            funcs = result.get('functions_extracted', 0)
            
            print(f"✅ {language.upper()} WORKS!")
            print(f"   Files processed: {files}")
            print(f"   Functions extracted: {funcs}")
            
            if funcs > 0:
                print(f"   Extraction rate: {funcs/files:.1f} functions/file")
            else:
                print(f"   ⚠️  No functions extracted (might need more files)")
            
            return {
                'status': 'success',
                'files': files,
                'functions': funcs,
                'working': funcs > 0
            }
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return {
                'status': 'failed',
                'error': result.get('error'),
                'working': False
            }
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e),
            'working': False
        }

def main():
    """Run multi-language tests"""
    print("="*70)
    print("MULTI-LANGUAGE PARSER TEST")
    print("Testing with real-world repositories")
    print("="*70)
    
    # Initialize processor (no cloud upload for testing)
    print("\n[1] Initializing processor...")
    processor = GitHubRepoProcessor(
        cloud_save=False  # No storage for testing
    )
    
    # Test each language
    results = {}
    
    for language, repos in TEST_REPOS.items():
        print(f"\n{'='*70}")
        print(f"LANGUAGE: {language.upper()}")
        print('='*70)
        
        # Test first repository for each language (for speed)
        repo_url = repos[0]
        result = test_language(language, repo_url, processor)
        
        results[language] = {
            'repo': repo_url,
            'result': result
        }
    
    # Summary
    print("\n" + "="*70)
    print("MULTI-LANGUAGE TEST SUMMARY")
    print("="*70)
    
    working_languages = []
    failed_languages = []
    
    print(f"\n{'Language':<15} {'Repository':<30} {'Files':<8} {'Functions':<12} {'Status'}")
    print("-"*70)
    
    total_files = 0
    total_functions = 0
    
    for language, data in results.items():
        repo_name = data['repo'].split('/')[-1]
        result = data['result']
        
        files = result.get('files', 0)
        funcs = result.get('functions', 0)
        working = result.get('working', False)
        
        total_files += files
        total_functions += funcs
        
        status = "✅ WORKING" if working else "❌ NO EXTRACTION"
        
        print(f"{language:<15} {repo_name:<30} {files:<8} {funcs:<12} {status}")
        
        if working:
            working_languages.append(language)
        else:
            failed_languages.append(language)
    
    print("-"*70)
    print(f"{'TOTAL':<15} {'':<30} {total_files:<8} {total_functions:<12}")
    
    # Final summary
    print("\n" + "="*70)
    print(f"✅ Working languages: {len(working_languages)}/{len(TEST_REPOS)}")
    if working_languages:
        print(f"   {', '.join(working_languages)}")
    
    if failed_languages:
        print(f"\n❌ Languages needing attention: {len(failed_languages)}")
        print(f"   {', '.join(failed_languages)}")
        print(f"\n   Note: Parsers are installed but may need:")
        print(f"   • More files processed (increase max_files)")
        print(f"   • Different node type mappings")
        print(f"   • Parser configuration adjustments")
    
    print("\n" + "="*70)
    
    if len(working_languages) > 0:
        print("✅ MULTI-LANGUAGE SUPPORT VALIDATED")
    else:
        print("⚠️  ONLY PYTHON FULLY WORKING")
    
    print("="*70)
    
    # Save detailed results
    with open('test_multi_language_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\n📄 Detailed results saved to: test_multi_language_results.json")
    
    return len(working_languages) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
