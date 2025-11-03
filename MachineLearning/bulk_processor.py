"""
Bulk Data Processor for Large-Scale Dataset Collection

This module handles massive data collection from multiple sources:
- GitHub repositories (using github_repo_processor)
- HuggingFace datasets
- Kaggle datasets (future)
- Web scraping

All processed data is saved to cloud storage for training.

Usage:
    python bulk_processor.py --source github --repos repo_list.txt
    python bulk_processor.py --source huggingface --dataset codeparrot/github-code
    python bulk_processor.py --all --workers 8
"""

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import tempfile

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# HuggingFace datasets
try:
    from datasets import load_dataset, Dataset
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    print("Warning: HuggingFace datasets not installed. Run: pip install datasets")

from github_repo_processor import GitHubRepoProcessor
from module.storage.storage_manager import StorageManager
from module.preprocessing.universal_parser_new import UniversalParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BulkProcessor:
    """
    Manages large-scale data processing from multiple sources.
    """

    # HuggingFace datasets for each task
    HUGGINGFACE_DATASETS = {
        'code_generation': [
            'codeparrot/github-code',
            'bigcode/the-stack',
            'code_search_net',
            'mbpp',
            'apps',
        ],
        'text_classification': [
            'imdb',
            'ag_news',
            'yelp_review_full',
            'amazon_polarity',
            'trec',
            'emotion',
        ],
        'security_classification': [
            'code_x_glue_cc_defect_detection',
            # More security datasets to be added
        ]
    }

    # Popular GitHub repositories by language
    GITHUB_REPOS = {
        'python': [
            # AI/ML Libraries
            'https://github.com/tensorflow/tensorflow',
            'https://github.com/pytorch/pytorch',
            'https://github.com/scikit-learn/scikit-learn',
            'https://github.com/keras-team/keras',
            'https://github.com/huggingface/transformers',
            'https://github.com/opencv/opencv-python',
            'https://github.com/facebookresearch/detectron2',

            # Web Frameworks
            'https://github.com/django/django',
            'https://github.com/flask/flask',
            'https://github.com/fastapi/fastapi',
            'https://github.com/tornadoweb/tornado',
            'https://github.com/aio-libs/aiohttp',

            # Data Science
            'https://github.com/pandas-dev/pandas',
            'https://github.com/numpy/numpy',
            'https://github.com/matplotlib/matplotlib',
            'https://github.com/bokeh/bokeh',
            'https://github.com/plotly/plotly.py',

            # Utilities
            'https://github.com/requests/requests',
            'https://github.com/psf/black',
            'https://github.com/celery/celery',
            'https://github.com/sqlalchemy/sqlalchemy',
            'https://github.com/redis/redis-py',
            'https://github.com/pallets/click',
            'https://github.com/benoitc/gunicorn',
        ],
        'javascript': [
            # Frameworks
            'https://github.com/facebook/react',
            'https://github.com/vuejs/vue',
            'https://github.com/angular/angular',
            'https://github.com/sveltejs/svelte',
            'https://github.com/vercel/next.js',

            # Runtime & Tools
            'https://github.com/nodejs/node',
            'https://github.com/denoland/deno',
            'https://github.com/webpack/webpack',
            'https://github.com/babel/babel',
            'https://github.com/parcel-bundler/parcel',

            # Libraries
            'https://github.com/expressjs/express',
            'https://github.com/axios/axios',
            'https://github.com/lodash/lodash',
            'https://github.com/moment/moment',
            'https://github.com/redux/redux',
            'https://github.com/socketio/socket.io',
            'https://github.com/typeorm/typeorm',
        ],
        'java': [
            # Frameworks
            'https://github.com/spring-projects/spring-boot',
            'https://github.com/spring-projects/spring-framework',
            'https://github.com/micronaut-projects/micronaut-core',
            'https://github.com/quarkusio/quarkus',

            # Big Data & Search
            'https://github.com/elastic/elasticsearch',
            'https://github.com/apache/kafka',
            'https://github.com/apache/spark',
            'https://github.com/apache/hadoop',
            'https://github.com/apache/flink',

            # Libraries
            'https://github.com/google/guava',
            'https://github.com/square/retrofit',
            'https://github.com/ReactiveX/RxJava',
            'https://github.com/netty/netty',
            'https://github.com/google/gson',
        ],
        'go': [
            'https://github.com/kubernetes/kubernetes',
            'https://github.com/docker/docker-ce',
            'https://github.com/hashicorp/terraform',
            'https://github.com/prometheus/prometheus',
            'https://github.com/grafana/grafana',
            'https://github.com/gin-gonic/gin',
            'https://github.com/gorilla/mux',
            'https://github.com/etcd-io/etcd',
            'https://github.com/containerd/containerd',
        ],
        'rust': [
            'https://github.com/rust-lang/rust',
            'https://github.com/servo/servo',
            'https://github.com/tokio-rs/tokio',
            'https://github.com/actix/actix-web',
            'https://github.com/diesel-rs/diesel',
            'https://github.com/serde-rs/serde',
        ],
        'security': [
            # Vulnerable apps for security training
            'https://github.com/OWASP/PyGoat',
            'https://github.com/juice-shop/juice-shop',
            'https://github.com/WebGoat/WebGoat',
            'https://github.com/digininja/DVWA',
            'https://github.com/ethicalhack3r/DVWA',
            'https://github.com/payatu/vuln-nodejs-app',
            'https://github.com/vegabird/xvna',
            'https://github.com/sqlmapproject/testenv',
            'https://github.com/Audi-1/sqli-labs',
            'https://github.com/commixproject/commix-testbed',
        ]
    }

    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """Initialize bulk processor."""
        self.storage = storage_manager or StorageManager()
        self.stats = {
            'start_time': datetime.now(),
            'datasets_processed': 0,
            'items_processed': 0,
            'errors': 0
        }

        # Connect to storage
        if not self.storage.connect():
            logger.warning("Could not connect to cloud storage, will save locally")

        # Checkpoint file for resume capability
        self.checkpoint_file = Path('bulk_processor_checkpoint.json')
        self.checkpoint = self.load_checkpoint()

    def load_checkpoint(self) -> Dict:
        """Load processing checkpoint for resume capability."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'processed_repos': [], 'processed_datasets': []}

    def save_checkpoint(self):
        """Save processing checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def process_github_repos(self,
                           repos_file: Optional[str] = None,
                           language: Optional[str] = None,
                           max_workers: int = 4):
        """
        Process GitHub repositories.

        Args:
            repos_file: File containing repo URLs
            language: Programming language to process
            max_workers: Number of parallel workers
        """
        logger.info("Starting GitHub repository processing")

        # Get repository list
        if repos_file and os.path.exists(repos_file):
            with open(repos_file, 'r') as f:
                repos = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        elif language:
            repos = self.GITHUB_REPOS.get(language, [])
        else:
            # Process all languages
            repos = []
            for lang_repos in self.GITHUB_REPOS.values():
                repos.extend(lang_repos)

        # Filter out already processed repos
        repos = [r for r in repos if r not in self.checkpoint['processed_repos']]

        logger.info(f"Processing {len(repos)} GitHub repositories")

        # Initialize processor
        processor = GitHubRepoProcessor(cloud_save=True)

        # Process repositories
        for i, repo in enumerate(repos, 1):
            try:
                logger.info(f"Processing {i}/{len(repos)}: {repo}")
                stats = processor.process_repository(repo)

                # Update checkpoint
                self.checkpoint['processed_repos'].append(repo)
                self.save_checkpoint()

                # Update statistics
                self.stats['items_processed'] += stats.get('functions_extracted', 0)

                # Small delay to avoid overwhelming GitHub
                time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to process {repo}: {e}")
                self.stats['errors'] += 1

    def process_huggingface_dataset(self,
                                   dataset_name: str,
                                   task_type: str = 'code_generation',
                                   max_samples: Optional[int] = None):
        """
        Process a HuggingFace dataset.

        Args:
            dataset_name: Name of HuggingFace dataset
            task_type: Task type for the dataset
            max_samples: Maximum number of samples to process
        """
        if not HUGGINGFACE_AVAILABLE:
            logger.error("HuggingFace datasets not available")
            return

        if dataset_name in self.checkpoint['processed_datasets']:
            logger.info(f"Dataset {dataset_name} already processed, skipping")
            return

        logger.info(f"Processing HuggingFace dataset: {dataset_name}")

        try:
            # Load dataset
            if dataset_name == 'codeparrot/github-code':
                # Special handling for large code dataset
                dataset = load_dataset(dataset_name,
                                      languages=['Python'],
                                      streaming=True)
                self.process_code_dataset_streaming(dataset, task_type, max_samples)

            elif dataset_name == 'bigcode/the-stack':
                # The Stack requires special access
                logger.warning("The Stack dataset requires authentication")
                return

            elif dataset_name in ['imdb', 'ag_news', 'yelp_review_full']:
                # Text classification datasets
                dataset = load_dataset(dataset_name)
                self.process_text_classification_dataset(dataset, max_samples)

            elif dataset_name == 'code_x_glue_cc_defect_detection':
                # Security dataset
                dataset = load_dataset(dataset_name)
                self.process_security_dataset(dataset, max_samples)

            else:
                # Generic processing
                dataset = load_dataset(dataset_name)
                self.process_generic_dataset(dataset, task_type, max_samples)

            # Update checkpoint
            self.checkpoint['processed_datasets'].append(dataset_name)
            self.save_checkpoint()

        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            self.stats['errors'] += 1

    def process_code_dataset_streaming(self,
                                      dataset,
                                      task_type: str,
                                      max_samples: Optional[int]):
        """Process large code dataset in streaming mode."""
        batch_size = 1000
        batch = []
        total_processed = 0
        
        # Create parser once for efficiency
        parser = UniversalParser()

        for item in dataset['train']:
            # Extract code content
            code = item.get('content', '') or item.get('code', '')
            if not code:
                continue

            # Parse functions from code
            functions = parser.parse(code, 'python')

            for func in functions:
                # Check max_samples limit based on total functions extracted
                if max_samples and total_processed >= max_samples:
                    break
                    
                # Use the fields returned by parse(): name, signature, doc, input, output
                dataset_item = {
                    'task_type': func.get('task_type', task_type),
                    'language': func.get('language', 'python'),
                    'func_name': func.get('name', 'unknown'),
                    'name': func.get('name', 'unknown'),
                    'signature': func.get('signature', ''),
                    'doc': func.get('doc', ''),
                    'input': func.get('input', ''),
                    'output': func.get('output', ''),
                    'source': 'huggingface_codeparrot'
                }
                batch.append(dataset_item)
                total_processed += 1

            # Check if we reached max_samples
            if max_samples and total_processed >= max_samples:
                break

            # Save batch when full
            if len(batch) >= batch_size:
                self.save_dataset_to_cloud(batch, f"{task_type}/huggingface")
                batch = []
                logger.info(f"Processed {total_processed} code samples")

        # Save remaining batch
        if batch:
            self.save_dataset_to_cloud(batch, f"{task_type}/huggingface")

        logger.info(f"Completed processing {total_processed} code samples")
        self.stats['items_processed'] += total_processed

    def process_text_classification_dataset(self,
                                           dataset,
                                           max_samples: Optional[int]):
        """Process text classification dataset."""
        batch = []
        total_processed = 0

        # Get train split
        train_data = dataset.get('train', dataset)

        for i, item in enumerate(train_data):
            if max_samples and i >= max_samples:
                break

            # Extract text and label
            text = item.get('text', '') or item.get('review', '') or item.get('sentence', '')
            label = item.get('label', 0)

            if not text:
                continue

            dataset_item = {
                'task_type': 'text_classification',
                'input': text,  # Changed from 'text' to 'input' for consistency with trainer
                'output': int(label),  # Changed from 'label' to 'output' for consistency with trainer
                'source': 'huggingface'
            }
            batch.append(dataset_item)

            # Save batch
            if len(batch) >= 1000:
                self.save_dataset_to_cloud(batch, 'text_classification/huggingface')
                total_processed += len(batch)
                batch = []

        # Save remaining
        if batch:
            self.save_dataset_to_cloud(batch, 'text_classification/huggingface')
            total_processed += len(batch)

        logger.info(f"Processed {total_processed} text classification samples")
        self.stats['items_processed'] += total_processed

    def process_security_dataset(self, dataset, max_samples: Optional[int]):
        """Process security/vulnerability detection dataset."""
        batch = []
        total_processed = 0

        train_data = dataset.get('train', dataset)

        for i, item in enumerate(train_data):
            if max_samples and i >= max_samples:
                break

            code = item.get('func', '') or item.get('code', '')
            label = item.get('target', 0) if 'target' in item else item.get('label', 0)

            if not code:
                continue

            dataset_item = {
                'task_type': 'security_classification',
                'input': code,
                'output': int(label),  # 0 = safe, 1 = vulnerable
                'source': 'huggingface_security'
            }
            batch.append(dataset_item)

            if len(batch) >= 1000:
                self.save_dataset_to_cloud(batch, 'security_classification/huggingface')
                total_processed += len(batch)
                batch = []

        if batch:
            self.save_dataset_to_cloud(batch, 'security_classification/huggingface')
            total_processed += len(batch)

        logger.info(f"Processed {total_processed} security samples")
        self.stats['items_processed'] += total_processed

    def process_generic_dataset(self,
                               dataset,
                               task_type: str,
                               max_samples: Optional[int]):
        """Generic dataset processing."""
        logger.info(f"Processing generic dataset for {task_type}")

        # Implementation depends on dataset structure
        # This is a fallback for unknown datasets
        pass

    def save_dataset_to_cloud(self, data: List[Dict], path_prefix: str):
        """
        Save dataset batch to cloud storage.

        Args:
            data: List of dataset items
            path_prefix: Path prefix in cloud storage
        """
        if not data:
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{path_prefix}/batch_{timestamp}_{len(data)}.json"

        try:
            # Convert to JSON
            json_data = json.dumps(data, indent=2)

            # Upload to cloud
            success = self.storage.upload_file_content(f"datasets/{filename}", json_data)

            if success:
                logger.info(f"Saved {len(data)} items to cloud: {filename}")
            else:
                # Fallback to local
                self.save_local_backup(data, filename)

        except Exception as e:
            logger.error(f"Failed to save to cloud: {e}")
            self.save_local_backup(data, filename)

    def save_local_backup(self, data: List[Dict], filename: str):
        """Save dataset locally as backup."""
        local_path = Path(f"dataset_storage/local_backup/{filename}")
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(data)} items locally: {local_path}")

    def process_all_sources(self, max_workers: int = 4):
        """Process all available data sources."""
        logger.info("Starting bulk processing of all sources")

        # Process GitHub repositories
        logger.info("Processing GitHub repositories...")
        for language in ['python', 'javascript', 'java', 'go']:
            self.process_github_repos(language=language, max_workers=max_workers)

        # Process HuggingFace datasets
        if HUGGINGFACE_AVAILABLE:
            logger.info("Processing HuggingFace datasets...")

            # Code generation datasets
            for dataset_name in self.HUGGINGFACE_DATASETS['code_generation']:
                self.process_huggingface_dataset(dataset_name, 'code_generation')

            # Text classification datasets
            for dataset_name in self.HUGGINGFACE_DATASETS['text_classification']:
                self.process_huggingface_dataset(dataset_name, 'text_classification')

            # Security datasets
            for dataset_name in self.HUGGINGFACE_DATASETS['security_classification']:
                self.process_huggingface_dataset(dataset_name, 'security_classification')

        # Print final statistics
        self.print_statistics()

    def print_statistics(self):
        """Print processing statistics."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()

        print("\n" + "="*60)
        print("BULK PROCESSING STATISTICS")
        print("="*60)
        print(f"Datasets processed: {self.stats['datasets_processed']}")
        print(f"Items processed: {self.stats['items_processed']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration/60:.2f} minutes")
        print(f"Items/minute: {self.stats['items_processed'] / max(duration/60, 1):.2f}")
        print("="*60)

        # Show checkpoint info
        print(f"\nProcessed repos: {len(self.checkpoint['processed_repos'])}")
        print(f"Processed datasets: {len(self.checkpoint['processed_datasets'])}")
        print("Checkpoint saved for resume capability")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Bulk data processor for ML training')
    parser.add_argument('--source', choices=['github', 'huggingface', 'all'],
                       help='Data source to process')
    parser.add_argument('--repos', type=str, help='File containing GitHub repo URLs')
    parser.add_argument('--dataset', type=str, help='HuggingFace dataset name')
    parser.add_argument('--language', type=str, help='Programming language for GitHub')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--max-samples', type=int, help='Maximum samples per dataset')
    parser.add_argument('--all', action='store_true', help='Process all sources')

    args = parser.parse_args()

    # Initialize processor
    processor = BulkProcessor()

    # Process based on arguments
    if args.all or args.source == 'all':
        processor.process_all_sources(max_workers=args.workers)

    elif args.source == 'github':
        processor.process_github_repos(
            repos_file=args.repos,
            language=args.language,
            max_workers=args.workers
        )

    elif args.source == 'huggingface':
        if args.dataset:
            processor.process_huggingface_dataset(
                args.dataset,
                max_samples=args.max_samples
            )
        else:
            # Process all HuggingFace datasets
            for task, datasets in processor.HUGGINGFACE_DATASETS.items():
                for dataset in datasets:
                    processor.process_huggingface_dataset(
                        dataset,
                        task_type=task,
                        max_samples=args.max_samples
                    )
    else:
        print("Please specify --source or --all")
        parser.print_help()


if __name__ == "__main__":
    main()