"""
Test multi-language extraction dopo il fix del quality filter
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from github_repo_processor import GitHubRepoProcessor
from module.utils.duplicate_manager import DuplicateManager

# Test repositories per linguaggio
TEST_REPOS = {
    'javascript': 'https://github.com/axios/axios',
    'go': 'https://github.com/spf13/cobra',
    'python': 'https://github.com/psf/requests',
}

def test_extraction():
    print("="*70)
    print("TEST MULTI-LANGUAGE EXTRACTION (After Quality Filter Fix)")
    print("="*70)
    
    for language, repo_url in TEST_REPOS.items():
        print(f"\n{'='*70}")
        print(f"Testing {language.upper()}: {repo_url}")
        print(f"{'='*70}\n")
        
        # Create fresh processor
        processor = GitHubRepoProcessor(
            cloud_save=False,  # Don't upload during test
            batch_size=100
        )
        
        # Clear duplicates for clean test
        processor.duplicate_manager = DuplicateManager('datasets')
        processor.duplicate_manager.cache = {}
        
        # Process repository
        result = processor.process_repository(repo_url)
        
        # Results
        print(f"\nResults for {language}:")
        print(f"  Files processed: {result.get('files_processed', 0)}")
        print(f"  Functions extracted: {result.get('functions_extracted', 0)}")
        print(f"  Status: {result.get('status', 'unknown')}")
        
        if result.get('functions_extracted', 0) > 0:
            print(f"  SUCCESS - Extracted {result['functions_extracted']} functions")
        else:
            print(f"  FAIL - No functions extracted")

    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    print("\nSe JavaScript e Go ora estraggono funzioni,")
    print("   il problema era il parametro 'language' mancante!")

if __name__ == "__main__":
    test_extraction()
