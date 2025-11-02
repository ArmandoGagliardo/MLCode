"""
Test completo multi-language con TUTTI i linguaggi supportati
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from github_repo_processor import GitHubRepoProcessor
from module.utils.duplicate_manager import DuplicateManager

# Test repositories per ogni linguaggio
TEST_REPOS = {
    'python': 'https://github.com/psf/requests',
    'javascript': 'https://github.com/axios/axios',
    'go': 'https://github.com/spf13/cobra',
    'rust': 'https://github.com/clap-rs/clap',
    'java': 'https://github.com/spring-projects/spring-framework',
    'cpp': 'https://github.com/nlohmann/json',
    'ruby': 'https://github.com/rails/rails',
}

def test_all_languages():
    print("="*70)
    print("COMPLETE MULTI-LANGUAGE EXTRACTION TEST")
    print("After language parameter fix + Rust implementation")
    print("="*70)
    
    results_summary = {}
    
    for language, repo_url in TEST_REPOS.items():
        print(f"\n{'='*70}")
        print(f"Testing {language.upper()}: {repo_url}")
        print(f"{'='*70}\n")
        
        try:
            # Create fresh processor
            processor = GitHubRepoProcessor(
                cloud_save=False,
                batch_size=100
            )
            
            # Clear duplicates for clean test
            processor.duplicate_manager = DuplicateManager('datasets')
            processor.duplicate_manager.cache = {}
            
            # Process repository (limit to prevent long tests)
            result = processor.process_repository(repo_url)
            
            # Store results
            results_summary[language] = {
                'files': result.get('files_processed', 0),
                'functions': result.get('functions_extracted', 0),
                'status': result.get('status', 'unknown')
            }
            
            # Print results
            print(f"\nResults for {language}:")
            print(f"  Files processed: {results_summary[language]['files']}")
            print(f"  Functions extracted: {results_summary[language]['functions']}")
            print(f"  Status: {results_summary[language]['status']}")
            
            if results_summary[language]['functions'] > 0:
                print(f"  SUCCESS")
            else:
                print(f"  FAIL - No functions extracted")
                
        except Exception as e:
            print(f"ERROR testing {language}: {e}")
            results_summary[language] = {
                'files': 0,
                'functions': 0,
                'status': 'error'
            }

    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}\n")
    
    working = []
    partial = []
    failed = []
    
    for lang, data in results_summary.items():
        if data['functions'] > 50:
            working.append(lang)
            print(f"  {lang.upper()}: {data['functions']} functions - WORKING")
        elif data['functions'] > 0:
            partial.append(lang)
            print(f"  {lang.upper()}: {data['functions']} functions - PARTIAL")
        else:
            failed.append(lang)
            print(f"  {lang.upper()}: 0 functions - FAILED")
    
    print(f"\n{'='*70}")
    print(f"Working: {len(working)}/{len(TEST_REPOS)} - {', '.join(working)}")
    print(f"Partial: {len(partial)}/{len(TEST_REPOS)} - {', '.join(partial)}")
    print(f"Failed: {len(failed)}/{len(TEST_REPOS)} - {', '.join(failed)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    test_all_languages()
