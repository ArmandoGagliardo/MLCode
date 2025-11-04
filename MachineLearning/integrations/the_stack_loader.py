"""
The Stack Dataset Integration
==============================

This script provides seamless integration with The Stack dataset from HuggingFace,
allowing efficient downloading and processing of high-quality code datasets.

The Stack contains 6TB+ of permissively licensed code from GitHub in 350+ languages.

Features:
- Streaming download (no need to download entire dataset)
- Language filtering
- License filtering (MIT, Apache, BSD only)
- Quality-based sampling
- Automatic formatting for training

Usage:
    # Download 100k Python samples
    python the_stack_loader.py --language python --count 100000

    # Download with quality filtering
    python the_stack_loader.py --language javascript --count 50000 --min-stars 10

    # Download multiple languages
    python the_stack_loader.py --languages python javascript java --count 50000

Author: ML Code Intelligence Project
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Iterator
from tqdm import tqdm

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.advanced_quality_filter import AdvancedQualityFilter
from module.utils.duplicate_manager import DuplicateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TheStackLoader:
    """
    Efficient loader for The Stack dataset with quality filtering.
    """

    def __init__(self,
                 output_dir: str = "dataset_storage/the_stack",
                 min_quality_score: int = 60,
                 use_ast_dedup: bool = True):
        """
        Initialize The Stack loader.

        Args:
            output_dir: Directory to save processed data
            min_quality_score: Minimum quality score (0-100)
            use_ast_dedup: Use AST-aware deduplication
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.parser = UniversalParser()
        self.quality_filter = AdvancedQualityFilter(min_score=min_quality_score)
        self.duplicate_manager = DuplicateManager(use_ast_hash=use_ast_dedup)

        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_accepted': 0,
            'total_rejected': 0,
            'duplicates_found': 0,
            'quality_failures': 0,
            'parse_failures': 0,
            'by_language': {}
        }

        logger.info("[OK] TheStackLoader initialized")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"  Quality threshold: {min_quality_score}/100")
        logger.info(f"  Deduplication: {'AST-aware' if use_ast_dedup else 'simple'}")

    def load_dataset(self,
                    language: str = "python",
                    split: str = "train",
                    streaming: bool = True) -> Iterator:
        """
        Load The Stack dataset from HuggingFace.

        Args:
            language: Programming language to filter
            split: Dataset split (train/validation/test)
            streaming: Use streaming mode (recommended for large datasets)

        Returns:
            Dataset iterator
        """
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("datasets library not installed!")
            logger.info("Install with: pip install datasets")
            return None

        logger.info(f"Loading The Stack dataset for {language}...")

        try:
            # Get HuggingFace token - try multiple methods
            token = None
            try:
                from huggingface_hub.utils import get_token
                token = get_token()
            except:
                pass

            # Fallback: read from token file directly
            if not token:
                import os
                token_path = os.path.expanduser("~/.cache/huggingface/token")
                if os.path.exists(token_path):
                    with open(token_path, 'r') as f:
                        token = f.read().strip()

            # Load dataset in streaming mode to avoid downloading everything
            dataset = load_dataset(
                "bigcode/the-stack",
                data_dir=f"data/{language}",
                split=split,
                streaming=streaming,
                token=token if token else True  # Use token or True for auto-detection
            )

            logger.info("[OK] Dataset loaded successfully")
            return dataset

        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            logger.info("Make sure you have:")
            logger.info("1. Accepted the dataset license on HuggingFace")
            logger.info("2. Logged in with: huggingface-cli login")
            return None

    def process_example(self, example: Dict, language: str) -> List[Dict]:
        """
        Process a single example from The Stack.

        Args:
            example: Raw example from dataset
            language: Programming language

        Returns:
            List of processed training examples
        """
        processed = []

        # Extract code content
        code = example.get('content', '')
        if not code or len(code) < 50:
            self.stats['total_rejected'] += 1
            return []

        # Extract metadata
        repo_name = example.get('max_forks_repo_name', 'unknown')
        license_info = example.get('max_forks_repo_licenses', ['unknown'])
        stars = example.get('max_stars_count', 0)
        path = example.get('path', '')

        # Skip if not permissive license
        permissive_licenses = ['MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'ISC']
        if not any(lic in str(license_info) for lic in permissive_licenses):
            self.stats['total_rejected'] += 1
            return []

        # Quality check on full file
        if not self.quality_filter.is_valid_code(code):
            self.stats['quality_failures'] += 1
            self.stats['total_rejected'] += 1
            return []

        # Try to parse and extract functions/classes
        try:
            # Extract functions
            functions = self.parser.extract_all_functions(code, language)

            # Extract classes
            classes = self.parser.extract_classes(code, language)

            # Process functions
            for func in functions[:5]:  # Limit to 5 functions per file
                # Check duplicate
                func_code = func.get('output', '')
                code_hash = self.duplicate_manager.generate_hash(func_code)

                if self.duplicate_manager.is_duplicate(code_hash):
                    self.stats['duplicates_found'] += 1
                    continue

                # Extract imports from original file
                imports = self._extract_imports(code, language)

                # Create high-quality training example
                training_example = {
                    'task_type': 'code_generation',
                    'language': language,
                    'input': func.get('doc', '') or f"Write a {language} function named {func.get('func_name', 'function')}",
                    'context': {
                        'imports': imports,
                        'signature': func.get('signature', ''),
                        'parent_class': func.get('parent_class'),
                        'file_path': path,
                        'repo_name': repo_name,
                        'stars': stars
                    },
                    'output': func_code,
                    'func_name': func.get('func_name'),
                    'doc': func.get('doc'),
                    'source': 'the-stack',
                    'license': license_info[0] if license_info else 'unknown',
                    'quality_score': self.quality_filter.calculate_score(func_code) if hasattr(self.quality_filter, 'calculate_score') else None,
                    'extracted_at': datetime.now().isoformat()
                }

                processed.append(training_example)

            # Process classes
            for cls in classes[:2]:  # Limit to 2 classes per file
                class_code = cls.get('output', '')
                code_hash = self.duplicate_manager.generate_hash(class_code)

                if self.duplicate_manager.is_duplicate(code_hash):
                    self.stats['duplicates_found'] += 1
                    continue

                training_example = {
                    'task_type': 'class_definition',
                    'language': language,
                    'input': cls.get('doc', '') or f"Write a {language} class named {cls.get('class_name', 'Class')}",
                    'context': {
                        'imports': self._extract_imports(code, language),
                        'parent_class': cls.get('parent_class'),
                        'file_path': path,
                        'repo_name': repo_name,
                        'stars': stars
                    },
                    'output': class_code,
                    'class_name': cls.get('class_name'),
                    'methods': cls.get('method_count', 0),
                    'source': 'the-stack',
                    'license': license_info[0] if license_info else 'unknown',
                    'extracted_at': datetime.now().isoformat()
                }

                processed.append(training_example)

            # If no functions/classes found, use file-level
            if not processed and len(code) < 2000:  # Only small files
                code_hash = self.duplicate_manager.generate_hash(code)
                if not self.duplicate_manager.is_duplicate(code_hash):
                    file_doc = self._extract_file_docstring(code, language)
                    training_example = {
                        'task_type': 'file_completion',
                        'language': language,
                        'input': file_doc or f"Write a {language} script",
                        'context': {
                            'file_path': path,
                            'repo_name': repo_name,
                            'stars': stars
                        },
                        'output': code,
                        'source': 'the-stack',
                        'license': license_info[0] if license_info else 'unknown',
                        'extracted_at': datetime.now().isoformat()
                    }
                    processed.append(training_example)

        except Exception as e:
            self.stats['parse_failures'] += 1
            logger.debug(f"Parse error: {e}")

        # Update statistics
        self.stats['total_accepted'] += len(processed)
        if language not in self.stats['by_language']:
            self.stats['by_language'][language] = 0
        self.stats['by_language'][language] += len(processed)

        return processed

    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        lines = code.split('\n')[:50]  # Check first 50 lines

        if language == 'python':
            for line in lines:
                line = line.strip()
                if line.startswith(('import ', 'from ')) and not line.startswith('#'):
                    imports.append(line)
                elif line and not line.startswith('#') and not line.startswith(('import ', 'from ')):
                    break

        elif language in ['javascript', 'typescript']:
            for line in lines:
                line = line.strip()
                if line.startswith(('import ', 'const ', 'require(')) and not line.startswith('//'):
                    imports.append(line)
                elif line and not line.startswith('//') and not line.startswith('import '):
                    break

        elif language == 'java':
            for line in lines:
                line = line.strip()
                if line.startswith(('import ', 'package ')) and not line.startswith('//'):
                    imports.append(line)
                elif line and not line.startswith(('import ', 'package ', '//')):
                    break

        return imports[:10]  # Limit imports

    def _extract_file_docstring(self, code: str, language: str) -> str:
        """Extract file-level documentation."""
        lines = code.split('\n')[:30]
        comments = []

        for line in lines:
            line = line.strip()
            if language == 'python' and line.startswith('#'):
                comments.append(line[1:].strip())
            elif language in ['javascript', 'java'] and line.startswith('//'):
                comments.append(line[2:].strip())
            elif comments:
                break

        return ' '.join(comments[:5]) if comments else ""

    def download_and_process(self,
                           languages: List[str],
                           count_per_language: int = 10000,
                           batch_size: int = 100,
                           min_stars: int = 0):
        """
        Download and process examples from The Stack.

        Args:
            languages: List of programming languages
            count_per_language: Number of examples per language
            batch_size: Batch size for saving
            min_stars: Minimum repository stars
        """
        logger.info("="*60)
        logger.info("DOWNLOADING FROM THE STACK")
        logger.info("="*60)
        logger.info(f"Languages: {', '.join(languages)}")
        logger.info(f"Examples per language: {count_per_language:,}")
        logger.info(f"Minimum stars: {min_stars}")
        logger.info("="*60)

        for language in languages:
            logger.info(f"\nProcessing {language}...")

            # Load dataset
            dataset = self.load_dataset(language)
            if not dataset:
                logger.error(f"Failed to load {language} dataset")
                continue

            # Process examples
            batch = []
            processed_count = 0

            with tqdm(total=count_per_language, desc=f"{language}") as pbar:
                for i, example in enumerate(dataset):
                    if processed_count >= count_per_language:
                        break

                    self.stats['total_processed'] += 1

                    # Filter by stars if specified
                    stars = example.get('max_stars_count', 0)
                    if stars is None:
                        stars = 0
                    if stars < min_stars:
                        continue

                    # Process example
                    processed = self.process_example(example, language)

                    if processed:
                        batch.extend(processed)
                        processed_count += len(processed)
                        pbar.update(len(processed))

                    # Save batch
                    if len(batch) >= batch_size:
                        self._save_batch(batch, language)
                        batch = []

            # Save remaining
            if batch:
                self._save_batch(batch, language)

            logger.info(f"[OK] {language}: {processed_count} examples processed")

        # Print final statistics
        self._print_statistics()

    def _save_batch(self, examples: List[Dict], language: str):
        """Save a batch of examples to JSONL file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"the_stack_{language}_{timestamp}_{len(examples)}.jsonl"
        filepath = self.output_dir / language / filename

        # Create language directory
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save to JSONL
        with open(filepath, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        logger.debug(f"Saved {len(examples)} examples to {filepath}")

    def _print_statistics(self):
        """Print processing statistics."""
        print("\n" + "="*60)
        print("PROCESSING STATISTICS")
        print("="*60)
        print(f"Total processed:     {self.stats['total_processed']:,}")
        print(f"Total accepted:      {self.stats['total_accepted']:,}")
        print(f"Total rejected:      {self.stats['total_rejected']:,}")
        print(f"  - Duplicates:      {self.stats['duplicates_found']:,}")
        print(f"  - Quality fails:   {self.stats['quality_failures']:,}")
        print(f"  - Parse failures:  {self.stats['parse_failures']:,}")

        if self.stats['by_language']:
            print("\nBy language:")
            for lang, count in self.stats['by_language'].items():
                print(f"  {lang:15} {count:,}")

        if self.stats['total_processed'] > 0:
            acceptance_rate = self.stats['total_accepted'] / self.stats['total_processed'] * 100
            print(f"\nAcceptance rate:     {acceptance_rate:.1f}%")

        print("="*60)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Download and process code from The Stack dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Language selection
    parser.add_argument('--language', type=str,
                       help='Single language to download')
    parser.add_argument('--languages', type=str, nargs='+',
                       help='Multiple languages to download')

    # Processing options
    parser.add_argument('--count', type=int, default=10000,
                       help='Number of examples per language (default: 10000)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for saving (default: 100)')
    parser.add_argument('--min-quality', type=int, default=60,
                       help='Minimum quality score 0-100 (default: 60)')
    parser.add_argument('--min-stars', type=int, default=0,
                       help='Minimum repository stars (default: 0)')

    # Output options
    parser.add_argument('--output-dir', type=str, default='dataset_storage/the_stack',
                       help='Output directory (default: dataset_storage/the_stack)')
    parser.add_argument('--no-dedup', action='store_true',
                       help='Disable deduplication')

    args = parser.parse_args()

    # Determine languages
    languages = []
    if args.languages:
        languages = args.languages
    elif args.language:
        languages = [args.language]
    else:
        # Default to Python
        languages = ['python']

    # Initialize loader
    loader = TheStackLoader(
        output_dir=args.output_dir,
        min_quality_score=args.min_quality,
        use_ast_dedup=not args.no_dedup
    )

    # Download and process
    loader.download_and_process(
        languages=languages,
        count_per_language=args.count,
        batch_size=args.batch_size,
        min_stars=args.min_stars
    )


if __name__ == '__main__':
    main()