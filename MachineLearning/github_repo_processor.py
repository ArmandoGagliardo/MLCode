"""
GitHub Repository Processor

This module clones GitHub repositories locally, processes all code files,
extracts functions/classes, and saves the processed datasets to cloud storage.
Repositories are deleted after processing to save disk space.

Usage:
    python github_repo_processor.py --repo https://github.com/user/repo
    python github_repo_processor.py --repos-file repo_list.txt
    python github_repo_processor.py --language python --count 100
"""

import os
import sys
import json
import shutil
import logging
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import time
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.storage.storage_manager import StorageManager
from module.preprocessing.universal_parser_new import UniversalParser
from module.utils.duplicate_manager import DuplicateManager
from module.preprocessing.code_quality_filter import QualityFilter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubRepoProcessor:
    """
    Processes GitHub repositories by cloning, extracting code, and saving to cloud.
    """

    # Supported file extensions by language
    FILE_EXTENSIONS = {
        'python': ['.py'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
        'go': ['.go'],
        'rust': ['.rs'],
        'php': ['.php'],
        'ruby': ['.rb'],
        'c': ['.c', '.h'],
        'csharp': ['.cs'],
        'swift': ['.swift'],
        'kotlin': ['.kt'],
        'scala': ['.scala'],
        'shell': ['.sh', '.bash'],
    }

    # Files to exclude
    EXCLUDE_PATTERNS = [
        '__pycache__', '.git', 'node_modules', '.venv', 'venv',
        'build', 'dist', '.egg-info', 'target', 'vendor',
        '.idea', '.vscode', 'test', 'tests', 'spec', 'specs',
        'migrations', '__tests__', '.pytest_cache'
    ]

    def __init__(self,
                 temp_dir: str = None,
                 cloud_save: bool = True,
                 max_file_size_mb: int = 10,
                 batch_size: int = 100):
        """
        Initialize the processor.

        Args:
            temp_dir: Temporary directory for cloning repos
            cloud_save: Whether to save datasets to cloud storage
            max_file_size_mb: Maximum file size to process (in MB)
            batch_size: Number of functions to batch before saving
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="repos_")
        self.cloud_save = cloud_save
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.batch_size = batch_size

        # Initialize components
        self.storage = StorageManager() if cloud_save else None
        self.parser = UniversalParser()
        self.duplicate_manager = DuplicateManager()
        self.quality_filter = QualityFilter()

        # Statistics
        self.stats = {
            'repos_processed': 0,
            'files_processed': 0,
            'functions_extracted': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Stop flag for graceful shutdown
        self.stop_requested = False
        self._setup_stop_handler()

        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized processor with temp dir: {self.temp_dir}")

        # Connect to cloud storage if enabled
        if self.cloud_save and self.storage:
            if not self.storage.connect():
                logger.error("Failed to connect to cloud storage")
                self.cloud_save = False

    def _setup_stop_handler(self):
        """Setup signal handler for graceful shutdown"""
        import signal
        
        def signal_handler(signum, frame):
            """Handle stop signals gracefully"""
            if not self.stop_requested:
                self.stop_requested = True
                logger.warning("\n[STOP] Signal received! Finishing current operation...")
                logger.warning("Press Ctrl+C again to force quit (may lose data)")
                print("\n[!] STOP REQUESTED - Finishing current repository...")
                print("[*] Current progress will be saved")
                print("[*] Press Ctrl+C again to force quit (not recommended)")
            else:
                logger.error("\n[FORCE QUIT] Force quit requested!")
                print("\n[!] FORCE QUIT - Some data may be lost!")
                sys.exit(1)
        
        # Register signal handlers for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def request_stop(self):
        """Request graceful stop of processing"""
        self.stop_requested = True
        logger.info("Stop requested programmatically")
        print("\n[PAUSE] Stop requested - will finish current operation")
    
    def should_continue(self) -> bool:
        """Check if processing should continue"""
        return not self.stop_requested

    def clone_repository(self, repo_url: str) -> Optional[str]:
        """
        Clone a repository to local temp directory.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Path to cloned repository or None if failed
        """
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        repo_owner = repo_url.rstrip('/').split('/')[-2]

        local_path = os.path.join(self.temp_dir, f"{repo_owner}_{repo_name}")

        # Remove if already exists
        if os.path.exists(local_path):
            shutil.rmtree(local_path)

        try:
            # Reduced logging - cloning happens quietly
            logger.debug(f"Cloning {repo_url} to {local_path}")

            # Clone with depth 1 to save bandwidth
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, local_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.lower()
                if 'repository not found' in error_msg or 'not found' in error_msg:
                    logger.warning(f"Repository not found or private: {repo_url}")
                else:
                    logger.error(f"Failed to clone {repo_url}: {result.stderr}")
                return None

            # Check repo size
            repo_size = sum(f.stat().st_size for f in Path(local_path).rglob('*') if f.is_file())
            # Reduced logging - size shown in progress output
            logger.debug(f"Cloned {repo_name}: {repo_size / 1024 / 1024:.2f} MB")

            return local_path

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout cloning {repo_url}")
            return None
        except Exception as e:
            logger.error(f"Error cloning {repo_url}: {e}")
            return None

    def find_code_files(self, repo_path: str, languages: List[str] = None) -> List[str]:
        """
        Find all code files in repository.

        Args:
            repo_path: Path to repository
            languages: List of languages to include (None = all)

        Returns:
            List of file paths
        """
        code_files = []
        repo_path = Path(repo_path)

        # Determine extensions to look for
        if languages:
            extensions = []
            for lang in languages:
                extensions.extend(self.FILE_EXTENSIONS.get(lang, []))
        else:
            extensions = [ext for exts in self.FILE_EXTENSIONS.values() for ext in exts]

        # Walk repository
        for file_path in repo_path.rglob('*'):
            # Skip directories
            if not file_path.is_file():
                continue

            # Skip excluded patterns
            if any(pattern in str(file_path) for pattern in self.EXCLUDE_PATTERNS):
                continue

            # Skip large files
            if file_path.stat().st_size > self.max_file_size_bytes:
                continue

            # Check extension
            if file_path.suffix.lower() in extensions:
                code_files.append(str(file_path))

        # Reduced logging - count shown in progress bar
        return code_files

    def extract_functions_from_file(self, file_path: str) -> List[Dict]:
        """
        Extract functions from a code file.

        Args:
            file_path: Path to code file

        Returns:
            List of extracted functions with metadata
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Detect language from extension
            ext = Path(file_path).suffix.lower()
            language = None
            for lang, exts in self.FILE_EXTENSIONS.items():
                if ext in exts:
                    language = lang
                    break

            if not language:
                return []

            # Parse with UniversalParser
            functions = self.parser.extract_all_functions(content, language)

            # Add metadata to each function
            for func in functions:
                # Add file metadata
                func['file_path'] = file_path
                func['language'] = language

                # Generate unique ID
                func_str = f"{func.get('name', '')}_{func.get('body', '')}"
                func['hash'] = hashlib.md5(func_str.encode()).hexdigest()

                # Add timestamp
                func['extracted_at'] = datetime.now().isoformat()

            return functions

        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return []

    def process_repository(self, repo_url: str) -> Dict:
        """
        Process a complete repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Processing statistics
        """
        repo_stats = {
            'repo_url': repo_url,
            'files_processed': 0,
            'functions_extracted': 0,
            'start_time': datetime.now(),
            'status': 'processing'
        }

        local_path = None

        try:
            # Extract repo name from URL for progress display
            repo_name = repo_url.rstrip('/').split('/')[-1]
            
            # Clone repository
            local_path = self.clone_repository(repo_url)
            if not local_path:
                repo_stats['status'] = 'clone_failed'
                return repo_stats

            # Find code files
            code_files = self.find_code_files(local_path)

            # Process files in batches with progress bar
            all_functions = []
            total_functions_extracted = 0  # Track total across batches
            
            # Create progress bar for file processing
            with tqdm(total=len(code_files), 
                     desc=f"Processing {repo_name}", 
                     unit="file",
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                     leave=False) as pbar:
                
                for file_path in code_files:
                    # Check for stop request
                    if not self.should_continue():
                        logger.info("Stop requested, finishing current repository...")
                        break

                    functions = self.extract_functions_from_file(file_path)

                    # Filter duplicates and low quality
                    filtered_functions = []
                    for func in functions:
                        # Skip if no name or body
                        if not func.get('name') or not func.get('body'):
                            continue
                        
                        # Check duplicate
                        if not self.duplicate_manager.is_duplicate(
                            func['hash'],
                            {'function': func['name']}
                        ):
                            # Check quality - use 'output' field which contains properly formatted code
                            code_to_validate = func.get('output', '')
                            if not code_to_validate:
                                # Fallback: build from signature + body with indentation
                                signature = func.get('signature', '')
                                body = func.get('body', '')
                                if signature and body:
                                    # Add indentation for Python
                                    body_lines = body.split('\n')
                                    indented_body = '\n'.join('    ' + line if line.strip() else line for line in body_lines)
                                    code_to_validate = signature + '\n' + indented_body
                                else:
                                    code_to_validate = body
                            
                            # Pass language parameter to quality filter for proper validation
                            func_language = func.get('language', 'python')
                            if self.quality_filter.is_valid_code(code_to_validate.strip(), language=func_language):
                                filtered_functions.append(func)
                                self.duplicate_manager.add_item(
                                    func['hash'],
                                    {'function': func['name']}
                                )

                    all_functions.extend(filtered_functions)
                    total_functions_extracted += len(filtered_functions)
                    repo_stats['files_processed'] += 1
                    
                    # Update progress bar with function count
                    pbar.set_postfix({'functions': total_functions_extracted})
                    pbar.update(1)

                    # Save batch if reached batch size
                    if len(all_functions) >= self.batch_size:
                        self.save_dataset_batch(all_functions, repo_url)
                        all_functions = []

            # Save remaining functions
            if all_functions:
                self.save_dataset_batch(all_functions, repo_url)

            repo_stats['functions_extracted'] = total_functions_extracted
            repo_stats['status'] = 'success'

        except Exception as e:
            logger.error(f"Error processing {repo_url}: {e}")
            repo_stats['status'] = 'error'
            repo_stats['error'] = str(e)

        finally:
            # Cleanup - delete cloned repo
            if local_path and os.path.exists(local_path):
                try:
                    # On Windows, git files can be locked. Try multiple times.
                    import time
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            shutil.rmtree(local_path)
                            # Reduced logging - cleanup successful
                            logger.debug(f"Cleaned up {local_path}")
                            break
                        except PermissionError as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.5)  # Wait before retry
                                # Try to change permissions
                                try:
                                    import stat
                                    for root, dirs, files in os.walk(local_path):
                                        for dir in dirs:
                                            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
                                        for file in files:
                                            os.chmod(os.path.join(root, file), stat.S_IRWXU)
                                except:
                                    pass
                            else:
                                logger.warning(f"Could not cleanup {local_path} after {max_retries} attempts: {e}")
                                logger.warning("Repository folder will be left in temp directory")
                except Exception as e:
                    logger.error(f"Failed to cleanup {local_path}: {e}")

            repo_stats['end_time'] = datetime.now()
            repo_stats['duration'] = (repo_stats['end_time'] - repo_stats['start_time']).total_seconds()

        return repo_stats

    def save_dataset_batch(self, functions: List[Dict], repo_url: str):
        """
        Save a batch of functions to cloud storage or local file.

        Args:
            functions: List of extracted functions
            repo_url: Source repository URL
        """
        if not functions:
            return

        # Prepare dataset format
        dataset = []
        for func in functions:
            # Format for training
            if func.get('language') == 'python':
                task_type = 'code_generation'
            else:
                task_type = 'code_generation'

            dataset_item = {
                'task_type': task_type,
                'language': func.get('language'),
                'func_name': func.get('name', 'unknown'),
                'input': f"Write a {func.get('language')} function named {func.get('name')}",
                'output': func.get('body', ''),
                'repo_url': repo_url,
                'file_path': func.get('file_path', ''),
                'extracted_at': func.get('extracted_at', '')
            }
            dataset.append(dataset_item)

        # Generate filename
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{repo_name}_{timestamp}_{len(dataset)}.json"

        if self.cloud_save and self.storage:
            # Save to cloud storage
            cloud_path = f"datasets/code_generation/{filename}"
            try:
                # Convert to JSON
                json_data = json.dumps(dataset, indent=2)

                # Upload to cloud using provider directly
                success = self.storage.provider.upload_file_content(cloud_path, json_data)

                if success:
                    # Log successful save
                    print(f"    [OK] Saved {len(dataset)} functions to cloud: {filename}")
                    logger.info(f"Saved {len(dataset)} functions to cloud: {cloud_path}")
                else:
                    # Fallback to local
                    print(f"    [WARNING] Cloud save failed, saving locally: {filename}")
                    self.save_local_backup(dataset, filename)

            except Exception as e:
                logger.error(f"Failed to save to cloud: {e}")
                self.save_local_backup(dataset, filename)
        else:
            # Save locally
            self.save_local_backup(dataset, filename)

    def save_local_backup(self, dataset: List[Dict], filename: str):
        """Save dataset locally as backup."""
        local_dir = Path("datasets/local_backup/code_generation")
        local_dir.mkdir(parents=True, exist_ok=True)

        local_path = local_dir / filename
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)

        logger.info(f"Saved {len(dataset)} functions locally: {local_path}")

    def process_repos_from_file(self, repos_file: str, max_workers: int = 4):
        """
        Process multiple repositories from a file.

        Args:
            repos_file: File containing repository URLs (one per line)
            max_workers: Number of parallel workers
        """
        # Read repository URLs
        with open(repos_file, 'r') as f:
            repo_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        logger.info(f"Processing {len(repo_urls)} repositories with {max_workers} workers")

        # Process repositories sequentially to allow graceful stop
        for i, repo_url in enumerate(repo_urls, 1):
            # Check for stop request
            if not self.should_continue():
                logger.info(f"Stop requested. Processed {i-1}/{len(repo_urls)} repositories.")
                break

            try:
                print(f"\n[{i}/{len(repo_urls)}] Processing: {repo_url}")
                stats = self.process_repository(repo_url)
                
                self.stats['repos_processed'] += 1
                self.stats['files_processed'] += stats['files_processed']
                self.stats['functions_extracted'] += stats['functions_extracted']

                print(f"  [OK] Extracted: {stats['functions_extracted']} functions\n")

            except Exception as e:
                logger.error(f"✗ Failed to process {repo_url}: {e}")
                self.stats['errors'] += 1

            # Small delay to avoid overwhelming resources
            time.sleep(1)

        # Print final statistics
        self.print_statistics()

    def get_popular_repos(self, language: str, count: int = 100) -> List[str]:
        """
        Get popular GitHub repositories for a language.

        Args:
            language: Programming language
            count: Number of repositories to get

        Returns:
            List of repository URLs
        """
        # This is a curated list of popular repositories
        # In production, you could use GitHub API to get trending repos

        repos = {
            'python': [
                'https://github.com/tensorflow/tensorflow',
                'https://github.com/django/django',
                'https://github.com/flask/flask',
                'https://github.com/keras-team/keras',
                'https://github.com/scikit-learn/scikit-learn',
                'https://github.com/pandas-dev/pandas',
                'https://github.com/numpy/numpy',
                'https://github.com/requests/requests',
                'https://github.com/pytorch/pytorch',
                'https://github.com/apache/airflow',
                'https://github.com/fastapi/fastapi',
                'https://github.com/psf/black',
                'https://github.com/pallets/click',
                'https://github.com/celery/celery',
                'https://github.com/sqlalchemy/sqlalchemy',
            ],
            'javascript': [
                'https://github.com/facebook/react',
                'https://github.com/vuejs/vue',
                'https://github.com/angular/angular',
                'https://github.com/nodejs/node',
                'https://github.com/expressjs/express',
                'https://github.com/axios/axios',
                'https://github.com/webpack/webpack',
                'https://github.com/babel/babel',
                'https://github.com/redux/redux',
                'https://github.com/lodash/lodash',
            ],
            'java': [
                'https://github.com/spring-projects/spring-boot',
                'https://github.com/spring-projects/spring-framework',
                'https://github.com/elastic/elasticsearch',
                'https://github.com/apache/kafka',
                'https://github.com/google/guava',
                'https://github.com/square/retrofit',
                'https://github.com/apache/dubbo',
                'https://github.com/netty/netty',
            ],
        }

        return repos.get(language, [])[:count]

    def print_statistics(self):
        """Print processing statistics."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()

        print("\n" + "="*50)
        print("PROCESSING STATISTICS")
        print("="*50)
        print(f"Repositories processed: {self.stats['repos_processed']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Functions extracted: {self.stats['functions_extracted']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Functions/second: {self.stats['functions_extracted'] / max(duration, 1):.2f}")
        print("="*50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Process GitHub repositories for ML training data')
    parser.add_argument('--repo', type=str, help='Single repository URL to process')
    parser.add_argument('--repos-file', type=str, help='File containing repository URLs')
    parser.add_argument('--language', type=str, help='Programming language to focus on')
    parser.add_argument('--count', type=int, default=10, help='Number of repos to process')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--temp-dir', type=str, help='Temporary directory for cloning')
    parser.add_argument('--no-cloud', action='store_true', help='Disable cloud storage')

    args = parser.parse_args()

    # Initialize processor
    processor = GitHubRepoProcessor(
        temp_dir=args.temp_dir,
        cloud_save=not args.no_cloud
    )

    # Process based on arguments
    if args.repo:
        # Process single repository
        stats = processor.process_repository(args.repo)
        print(f"Processed {args.repo}: {stats}")

    elif args.repos_file:
        # Process from file
        processor.process_repos_from_file(args.repos_file, max_workers=args.workers)

    elif args.language:
        # Process popular repos for language
        repos = processor.get_popular_repos(args.language, args.count)
        for repo in repos:
            stats = processor.process_repository(repo)
            print(f"Processed {repo}: {stats['functions_extracted']} functions")
    else:
        print("Please specify --repo, --repos-file, or --language")


if __name__ == "__main__":
    main()