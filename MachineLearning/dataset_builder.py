"""
Dataset Builder - Complete Pipeline for ML Code Training Data

This script provides a unified interface for building high-quality code datasets
from multiple sources:
- HuggingFace datasets (The Stack, CodeSearchNet)
- GitHub repositories
- Local directories

Features:
- AST-aware deduplication
- Advanced quality filtering (radon metrics)
- Docstring→code pairing
- Hybrid extraction (functions + files)
- Cloud storage integration
- Progress tracking and statistics

Usage:
    # Download from The Stack (Python subset)
    python dataset_builder.py --source the-stack --subset python --count 100000
    
    # Process GitHub repositories
    python dataset_builder.py --source github --repos-file repos.txt
    
    # Process local directory
    python dataset_builder.py --source local --directory ./my_code
    
    # With advanced options
    python dataset_builder.py \\
        --source the-stack \\
        --subset python \\
        --count 50000 \\
        --min-quality 70 \\
        --extraction-mode hybrid \\
        --enable-docstring-pairs \\
        --upload-cloud

Version: 1.0.0
Author: ML Code Intelligence Project
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from tqdm import tqdm

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from github_repo_processor import GitHubRepoProcessor
# Clean Architecture v2.0
from config.container import Container
from application.services.storage_service import StorageService
from infrastructure.parsers.tree_sitter_parser import TreeSitterParser
from infrastructure.quality.heuristic_quality_filter import HeuristicQualityFilter
from infrastructure.duplicate.ast_duplicate_manager import ASTDuplicateManager
from config import CLOUD_DATASET_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatasetBuilder:
    """
    Unified dataset builder for ML code training data.
    """
    
    def __init__(self,
                 min_quality_score: int = 60,
                 use_ast_dedup: bool = True,
                 extraction_mode: str = 'hybrid',
                 enable_docstring_pairs: bool = False,
                 upload_cloud: bool = False,
                 output_dir: str = 'dataset_storage'):
        """
        Initialize dataset builder.
        
        Args:
            min_quality_score: Minimum quality score (0-100)
            use_ast_dedup: Use AST-aware deduplication
            extraction_mode: 'function', 'file', or 'hybrid'
            enable_docstring_pairs: Extract docstring→code pairs
            upload_cloud: Upload to cloud storage
            output_dir: Local output directory
        """
        self.min_quality_score = min_quality_score
        self.use_ast_dedup = use_ast_dedup
        self.extraction_mode = extraction_mode
        self.enable_docstring_pairs = enable_docstring_pairs
        self.upload_cloud = upload_cloud
        self.output_dir = Path(output_dir)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.parser = UniversalParser()
        self.quality_filter = AdvancedQualityFilter(min_score=min_quality_score)
        self.duplicate_manager = DuplicateManager(use_ast_hash=use_ast_dedup)
        
        # Storage manager (if cloud upload enabled)
        self.storage = None
        if upload_cloud:
            self.storage = StorageManager()
            if not self.storage.connect():
                logger.error("Failed to connect to cloud storage")
                self.upload_cloud = False
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_accepted': 0,
            'total_rejected': 0,
            'duplicates_found': 0,
            'quality_failures': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"DatasetBuilder initialized")
        logger.info(f"  Quality threshold: {min_quality_score}/100")
        logger.info(f"  Deduplication: {'AST-aware' if use_ast_dedup else 'simple'}")
        logger.info(f"  Extraction mode: {extraction_mode}")
        logger.info(f"  Cloud upload: {'enabled' if upload_cloud else 'disabled'}")
    
    def build_from_the_stack(self, subset: str = 'python', count: int = 100000):
        """
        Download and process dataset from The Stack (HuggingFace).
        
        Args:
            subset: Language subset (python, javascript, java, etc.)
            count: Number of examples to process
        """
        logger.info(f"Building dataset from The Stack ({subset} subset)")
        logger.info(f"Target count: {count:,} examples")
        
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("datasets library not found. Install: pip install datasets")
            return
        
        # Try multiple methods to get HuggingFace token
        token = None
        
        # Method 1: Try get_token() from huggingface_hub
        try:
            from huggingface_hub import get_token
            token = get_token()
            if token:
                logger.info("✅ HuggingFace token found via get_token()")
        except Exception:
            pass
        
        # Method 2: Try reading from token file directly
        if not token:
            try:
                import os
                token_path = os.path.expanduser("~/.cache/huggingface/token")
                if os.path.exists(token_path):
                    with open(token_path, 'r') as f:
                        token = f.read().strip()
                    if token:
                        logger.info("✅ HuggingFace token found via token file")
            except Exception:
                pass
        
        # Method 3: Try environment variable
        if not token:
            try:
                import os
                token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')
                if token:
                    logger.info("✅ HuggingFace token found via environment variable")
            except Exception:
                pass
        
        if not token:
            logger.warning("⚠️  No HuggingFace token found. The Stack dataset requires authentication.")
            logger.warning("Please run: huggingface-cli login")
            logger.warning("Or set HF_TOKEN environment variable")
        
        # Load dataset in streaming mode (no need to download all)
        logger.info("Loading dataset in streaming mode...")
        
        # Try with token
        try:
            dataset = load_dataset(
                "bigcode/the-stack",
                data_dir=f"data/{subset}",
                split="train",
                streaming=True,
                token=token if token else None
            )
            logger.info("✅ Dataset loaded successfully!")
        except Exception as e:
            if "gated" in str(e).lower() or "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error("[FAIL] Authentication required for The Stack dataset!")
                logger.error("")
                logger.error("SOLUTIONS:")
                logger.error("1. Run: huggingface-cli login")
                logger.error("2. Request access: https://huggingface.co/datasets/bigcode/the-stack")
                logger.error("3. Use local files: --data-source local --directory 'dataset_storage/the_stack/python/'")
                logger.error("")
                raise
            else:
                raise
        
        # Process examples
        accepted_examples = []
        batch_size = 100
        
        with tqdm(total=count, desc="Processing") as pbar:
            for i, example in enumerate(dataset):
                if i >= count:
                    break
                
                self.stats['total_processed'] += 1
                
                # Extract code content
                code = example.get('content', '')
                
                if not code or len(code) < 50:
                    self.stats['total_rejected'] += 1
                    continue
                
                # Quality check
                if not self.quality_filter.is_valid_code(code):
                    self.stats['quality_failures'] += 1
                    self.stats['total_rejected'] += 1
                    continue
                
                # Duplicate check
                code_hash = self.duplicate_manager.generate_hash(code)
                if self.duplicate_manager.is_duplicate(code_hash):
                    self.stats['duplicates_found'] += 1
                    self.stats['total_rejected'] += 1
                    continue
                
                # Parse code to extract functions with context
                try:
                    functions = self.parser.extract_all_functions(code, subset)
                    if functions:
                        # Use first function for better quality
                        func = functions[0]

                        # Extract imports from file
                        imports = self._extract_imports(code, subset)

                        # Create context-rich training example
                        formatted_example = {
                            'task_type': 'code_generation',
                            'language': subset,
                            'input': func.get('doc', '') or f"Write a {subset} function named {func.get('func_name', 'function')}",
                            'context': {
                                'imports': imports,
                                'signature': func.get('signature', ''),
                                'parent_class': func.get('parent_class'),
                                'file_path': example.get('path', ''),
                            },
                            'output': func.get('output', code),
                            'func_name': func.get('func_name'),
                            'source': 'the-stack',
                            'license': example.get('max_forks_repo_licenses', ['unknown'])[0],
                            'repo_name': example.get('max_forks_repo_name', ''),
                            'extracted_at': datetime.now().isoformat()
                        }
                    else:
                        # Fallback to full file if no functions found
                        formatted_example = {
                            'task_type': 'file_completion',
                            'language': subset,
                            'input': self._extract_file_docstring(code, subset) or f"Write {subset} code",
                            'context': {
                                'imports': self._extract_imports(code, subset),
                                'file_path': example.get('path', ''),
                            },
                            'output': code,
                            'source': 'the-stack',
                            'license': example.get('max_forks_repo_licenses', ['unknown'])[0],
                            'repo_name': example.get('max_forks_repo_name', ''),
                            'extracted_at': datetime.now().isoformat()
                        }
                except:
                    # Fallback to simple format if parsing fails
                    formatted_example = {
                        'task_type': 'code_generation',
                        'language': subset,
                        'input': f"Write {subset} code",
                        'output': code,
                        'source': 'the-stack',
                        'license': example.get('max_forks_repo_licenses', ['unknown'])[0],
                        'extracted_at': datetime.now().isoformat()
                    }
                
                accepted_examples.append(formatted_example)
                self.stats['total_accepted'] += 1
                
                # Save batch
                if len(accepted_examples) >= batch_size:
                    self._save_batch(accepted_examples, f"the_stack_{subset}")
                    accepted_examples = []
                
                pbar.update(1)
        
        # Save remaining examples
        if accepted_examples:
            self._save_batch(accepted_examples, f"the_stack_{subset}")
        
        self._print_statistics()
    
    def build_from_github(self, repos_file: str = None, repo_urls: List[str] = None):
        """
        Build dataset from GitHub repositories.
        
        Args:
            repos_file: Path to file with repository URLs
            repo_urls: List of repository URLs
        """
        logger.info("Building dataset from GitHub repositories")
        
        # Use GitHubRepoProcessor with advanced features
        processor = GitHubRepoProcessor(
            cloud_save=self.upload_cloud,
            extraction_mode=self.extraction_mode,
            use_advanced_quality=True,
            enable_docstring_pairs=self.enable_docstring_pairs
        )
        
        if repos_file:
            logger.info(f"Processing repositories from file: {repos_file}")
            processor.process_repos_from_file(repos_file, max_workers=4)
        elif repo_urls:
            logger.info(f"Processing {len(repo_urls)} repositories")
            for repo_url in repo_urls:
                try:
                    stats = processor.process_repository(repo_url)
                    logger.info(f"Processed {repo_url}: {stats['functions_extracted']} functions")
                except Exception as e:
                    logger.error(f"Failed to process {repo_url}: {e}")
        else:
            logger.error("Specify either repos_file or repo_urls")
            return
        
        processor.print_statistics()
    
    def build_from_local(self, directory: str, language: str = 'python'):
        """
        Build dataset from local code directory.
        
        Args:
            directory: Path to directory with code files
            language: Programming language
        """
        logger.info(f"Building dataset from local directory: {directory}")
        
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return
        
        # Check if directory contains JSONL files (already processed data)
        jsonl_files = list(dir_path.glob('*.jsonl'))
        
        if jsonl_files:
            logger.info(f"Found {len(jsonl_files)} JSONL files - loading pre-processed data")
            self._load_from_jsonl_files(jsonl_files, language)
            return
        
        # Otherwise, process code files
        # File extensions by language
        extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.hpp', '.cc', '.h']
        }
        
        exts = extensions.get(language, ['.py'])
        
        # Find all code files
        code_files = []
        for ext in exts:
            code_files.extend(dir_path.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(code_files)} {language} files")
        
        accepted_examples = []
        batch_size = 100
        
        for file_path in tqdm(code_files, desc="Processing files"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                self.stats['total_processed'] += 1
                
                # Extract functions
                if self.enable_docstring_pairs:
                    functions = self.parser.extract_with_docstring_pairs(code, language)
                else:
                    functions = self.parser.extract_all_functions(code, language)
                
                for func in functions:
                    # Quality check
                    func_code = func.get('output', '')
                    if not self.quality_filter.is_valid_code(func_code):
                        self.stats['quality_failures'] += 1
                        continue
                    
                    # Duplicate check
                    code_hash = self.duplicate_manager.generate_hash(func_code)
                    if self.duplicate_manager.is_duplicate(code_hash):
                        self.stats['duplicates_found'] += 1
                        continue
                    
                    # Add metadata
                    func['file_path'] = str(file_path)
                    func['source'] = 'local'
                    func['extracted_at'] = datetime.now().isoformat()
                    
                    accepted_examples.append(func)
                    self.stats['total_accepted'] += 1
                    
                    # Save batch
                    if len(accepted_examples) >= batch_size:
                        self._save_batch(accepted_examples, f"local_{language}")
                        accepted_examples = []
                        
            except Exception as e:
                logger.debug(f"Error processing {file_path}: {e}")
                continue
        
        # Save remaining
        if accepted_examples:
            self._save_batch(accepted_examples, f"local_{language}")
        
        self._print_statistics()
    
    def _load_from_jsonl_files(self, jsonl_files: List[Path], language: str):
        """
        Load and process data from JSONL files (e.g., from The Stack).
        
        Args:
            jsonl_files: List of JSONL file paths
            language: Programming language
        """
        logger.info(f"Processing {len(jsonl_files)} JSONL files")
        
        accepted_examples = []
        batch_size = 100
        
        for jsonl_file in tqdm(jsonl_files, desc="Processing JSONL files"):
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            item = json.loads(line.strip())
                            self.stats['total_processed'] += 1
                            
                            # FORMATO 1: Code-generation dataset (già estratto)
                            # Campi: output, input, func_name, doc, context, etc.
                            if 'output' in item:
                                code = item.get('output', '').strip()
                                if not code or len(code) < 10:
                                    continue
                                
                                # Quality check
                                if not self.quality_filter.is_valid_code(code):
                                    self.stats['quality_failures'] += 1
                                    continue
                                
                                # Duplicate check
                                code_hash = self.duplicate_manager.generate_hash(code)
                                if self.duplicate_manager.is_duplicate(code_hash):
                                    self.stats['duplicates_found'] += 1
                                    continue
                                
                                # Costruisci esempio (formato già estratto)
                                context = item.get('context', {})
                                func_example = {
                                    'input': item.get('input', ''),
                                    'output': code,
                                    'func_name': item.get('func_name', 'unknown'),
                                    'docstring': item.get('doc', ''),
                                    'file_path': context.get('file_path', '') if isinstance(context, dict) else '',
                                    'repo_name': context.get('repo_name', 'unknown') if isinstance(context, dict) else 'unknown',
                                    'source': 'the-stack',
                                    'license': item.get('license', 'unknown'),
                                    'extracted_at': item.get('extracted_at', datetime.now().isoformat()),
                                }
                                
                                accepted_examples.append(func_example)
                                self.stats['total_accepted'] += 1
                                
                                # Save batch
                                if len(accepted_examples) >= batch_size:
                                    self._save_batch(accepted_examples, f"the_stack_{language}")
                                    accepted_examples = []
                            
                            # FORMATO 2: Raw code (da estrarre funzioni)
                            else:
                                code = item.get('content') or item.get('code') or item.get('text', '')
                                if not code or len(code) < 10:
                                    continue
                                
                                # Extract functions using parser
                                if self.enable_docstring_pairs:
                                    functions = self.parser.extract_with_docstring_pairs(code, language)
                                else:
                                    functions = self.parser.extract_all_functions(code, language)
                                
                                for func in functions:
                                    # Quality check
                                    func_code = func.get('output', '')
                                    if not self.quality_filter.is_valid_code(func_code):
                                        self.stats['quality_failures'] += 1
                                        continue
                                    
                                    # Duplicate check
                                    code_hash = self.duplicate_manager.generate_hash(func_code)
                                    if self.duplicate_manager.is_duplicate(code_hash):
                                        self.stats['duplicates_found'] += 1
                                        continue
                                    
                                    # Add metadata
                                    func['file_path'] = item.get('path', str(jsonl_file))
                                    func['source'] = 'the-stack'
                                    func['repo_name'] = item.get('repo_name', 'unknown')
                                    func['extracted_at'] = datetime.now().isoformat()
                                    
                                    accepted_examples.append(func)
                                    self.stats['total_accepted'] += 1
                                    
                                    # Save batch
                                    if len(accepted_examples) >= batch_size:
                                        self._save_batch(accepted_examples, f"the_stack_{language}")
                                        accepted_examples = []
                                    
                        except json.JSONDecodeError:
                            logger.debug(f"Skipping invalid JSON at line {line_num} in {jsonl_file}")
                            continue
                        except Exception as e:
                            logger.debug(f"Error processing line {line_num} in {jsonl_file}: {e}")
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading {jsonl_file}: {e}")
                continue
        
        # Save remaining
        if accepted_examples:
            self._save_batch(accepted_examples, f"the_stack_{language}")
        
        self._print_statistics()

    def _extract_imports(self, code: str, language: str) -> List[str]:
        """
        Extract import statements from code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of import statements
        """
        imports = []
        lines = code.split('\n')

        if language == 'python':
            for line in lines:
                line = line.strip()
                if line.startswith(('import ', 'from ')) and not line.startswith('#'):
                    imports.append(line)
                elif not line.startswith('#') and line and not line.startswith(('import ', 'from ')):
                    # Stop at first non-import, non-comment line
                    break

        elif language in ['javascript', 'typescript']:
            for line in lines:
                line = line.strip()
                if line.startswith(('import ', 'const ', 'require(')) and not line.startswith('//'):
                    imports.append(line)
                elif not line.startswith('//') and line and not line.startswith('import '):
                    break

        elif language == 'java':
            for line in lines:
                line = line.strip()
                if line.startswith('import ') and not line.startswith('//'):
                    imports.append(line)
                elif line.startswith('package '):
                    imports.append(line)
                elif line and not line.startswith(('import ', 'package ', '//')):
                    break

        return imports[:20]  # Limit to 20 imports to avoid token explosion

    def _extract_file_docstring(self, code: str, language: str) -> str:
        """
        Extract file-level docstring or first comment block.

        Args:
            code: Source code
            language: Programming language

        Returns:
            File docstring or description
        """
        if language == 'python':
            # Check for module docstring
            if code.startswith(('"""', "'''")):
                quote = code[:3]
                end_idx = code.find(quote, 3)
                if end_idx > 0:
                    return code[3:end_idx].strip()

        # Extract first comment block for any language
        lines = code.split('\n')
        comment_lines = []
        in_comment = False

        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()

            if language == 'python' and line.startswith('#'):
                comment_lines.append(line[1:].strip())
            elif language in ['javascript', 'java', 'cpp'] and line.startswith('//'):
                comment_lines.append(line[2:].strip())
            elif line.startswith('/*'):
                in_comment = True
                comment_lines.append(line[2:].strip())
            elif in_comment:
                if '*/' in line:
                    comment_lines.append(line.replace('*/', '').strip())
                    break
                else:
                    comment_lines.append(line.replace('*', '').strip())
            elif comment_lines:
                # Stop at first non-comment line if we have comments
                break

        return ' '.join(comment_lines[:10])  # First 10 lines of comments

    def _save_batch(self, examples: List[Dict], prefix: str):
        """
        Save batch of examples to file and optionally upload to cloud.
        
        Args:
            examples: List of training examples
            prefix: Filename prefix
        """
        if not examples:
            return
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}_{len(examples)}.jsonl"
        filepath = self.output_dir / filename
        
        # Save to local file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for example in examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
            
            logger.info(f"Saved {len(examples)} examples to {filepath}")
            
            # Upload to cloud if enabled
            if self.upload_cloud and self.storage:
                try:
                    remote_path = f"{CLOUD_DATASET_PATH}/{filename}"
                    self.storage.upload_file(filepath, remote_path)
                    logger.info(f"Uploaded to cloud: {remote_path}")
                except Exception as e:
                    logger.error(f"Cloud upload failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
    
    def _print_statistics(self):
        """Print final statistics."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("DATASET BUILDING STATISTICS")
        print("="*60)
        print(f"Total processed:    {self.stats['total_processed']:,}")
        print(f"Total accepted:     {self.stats['total_accepted']:,}")
        print(f"Total rejected:     {self.stats['total_rejected']:,}")
        print(f"  - Duplicates:     {self.stats['duplicates_found']:,}")
        print(f"  - Quality fails:  {self.stats['quality_failures']:,}")
        print(f"Duration:           {duration:.1f}s")
        print(f"Acceptance rate:    {self.stats['total_accepted']/max(1, self.stats['total_processed'])*100:.1f}%")
        print("="*60)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Build high-quality ML code training datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Source selection
    parser.add_argument('--source', type=str, required=True,
                       choices=['the-stack', 'github', 'local'],
                       help='Data source')
    
    # The Stack options
    parser.add_argument('--subset', type=str, default='python',
                       help='Language subset for The Stack (default: python)')
    parser.add_argument('--count', type=int, default=100000,
                       help='Number of examples to process (default: 100000)')
    
    # GitHub options
    parser.add_argument('--repos-file', type=str,
                       help='File with repository URLs (one per line)')
    parser.add_argument('--repos', type=str, nargs='+',
                       help='List of repository URLs')
    
    # Local options
    parser.add_argument('--directory', type=str,
                       help='Local directory with code files')
    parser.add_argument('--language', type=str, default='python',
                       help='Programming language (default: python)')
    
    # Quality options
    parser.add_argument('--min-quality', type=int, default=60,
                       help='Minimum quality score 0-100 (default: 60)')
    parser.add_argument('--extraction-mode', type=str, default='hybrid',
                       choices=['function', 'file', 'hybrid'],
                       help='Extraction mode (default: hybrid)')
    parser.add_argument('--enable-docstring-pairs', action='store_true',
                       help='Extract docstring→code pairs')
    
    # Storage options
    parser.add_argument('--upload-cloud', action='store_true',
                       help='Upload to cloud storage')
    parser.add_argument('--output-dir', type=str, default='dataset_storage',
                       help='Local output directory (default: dataset_storage)')
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = DatasetBuilder(
        min_quality_score=args.min_quality,
        use_ast_dedup=True,
        extraction_mode=args.extraction_mode,
        enable_docstring_pairs=args.enable_docstring_pairs,
        upload_cloud=args.upload_cloud,
        output_dir=args.output_dir
    )
    
    # Execute based on source
    if args.source == 'the-stack':
        builder.build_from_the_stack(subset=args.subset, count=args.count)
    
    elif args.source == 'github':
        if args.repos_file:
            builder.build_from_github(repos_file=args.repos_file)
        elif args.repos:
            builder.build_from_github(repo_urls=args.repos)
        else:
            parser.error("--source github requires --repos-file or --repos")
    
    elif args.source == 'local':
        if not args.directory:
            parser.error("--source local requires --directory")
        builder.build_from_local(directory=args.directory, language=args.language)


if __name__ == '__main__':
    main()
