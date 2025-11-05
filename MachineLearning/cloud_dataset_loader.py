"""
Cloud Dataset Loader

This module enables training models directly from datasets stored in cloud storage.
It streams data in batches to avoid memory overflow and supports checkpoint/resume.

Usage:
    from cloud_dataset_loader import CloudDatasetLoader

    loader = CloudDatasetLoader(task_type='code_generation')
    for batch in loader.get_batches(batch_size=32):
        # Train on batch
        pass
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Generator, Optional, Tuple
import random
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use Clean Architecture v2.0 - NO module/ imports!
from config.container import Container
from application.services.storage_service import StorageService
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudDataset(Dataset):
    """
    PyTorch Dataset that loads data from cloud storage.
    """

    def __init__(self,
                 task_type: str,
                 tokenizer,
                 storage_service: StorageService,
                 cache_size: int = 10000,
                 shuffle: bool = True):
        """
        Initialize cloud dataset.

        Args:
            task_type: Type of task (code_generation, text_classification, etc.)
            tokenizer: HuggingFace tokenizer
            storage_service: Storage service for cloud access (Clean Architecture v2.0)
            cache_size: Number of samples to cache in memory
            shuffle: Whether to shuffle data
        """
        self.task_type = task_type
        self.tokenizer = tokenizer
        self.storage = storage_service
        self.cache_size = cache_size
        self.shuffle = shuffle

        # Data cache
        self.data_cache = []
        self.cache_index = 0
        self.total_samples_loaded = 0

        # Cloud dataset files
        self.dataset_files = []
        self.current_file_index = 0

        # Load dataset file list from cloud
        self._load_dataset_files()

        # Load initial cache
        self._refresh_cache()

    def _load_dataset_files(self):
        """Load list of dataset files from cloud storage."""
        try:
            # List all dataset files for this task
            cloud_path = f"datasets/{self.task_type}/"
            self.dataset_files = self.storage.list_files(cloud_path)

            if not self.dataset_files:
                # Try alternative path structure
                cloud_path = f"datasets/processed/{self.task_type}/"
                self.dataset_files = self.storage.list_files(cloud_path)

            logger.info(f"Found {len(self.dataset_files)} dataset files for {self.task_type}")

            if self.shuffle:
                random.shuffle(self.dataset_files)

        except Exception as e:
            logger.error(f"Failed to load dataset files: {e}")
            self.dataset_files = []

    def _refresh_cache(self):
        """Refresh the in-memory cache from cloud storage."""
        self.data_cache = []

        while len(self.data_cache) < self.cache_size and self.current_file_index < len(self.dataset_files):
            try:
                # Download and load next file
                file_path = self.dataset_files[self.current_file_index]
                logger.info(f"Loading dataset file: {file_path}")

                # Download to temp file
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
                    success = self.storage.download_file(file_path, tmp.name)

                    if success:
                        # Load JSON data
                        with open(tmp.name, 'r') as f:
                            data = json.load(f)

                        # Add to cache
                        if isinstance(data, list):
                            self.data_cache.extend(data)
                        else:
                            self.data_cache.append(data)

                    # Clean up temp file
                    os.unlink(tmp.name)

                self.current_file_index += 1

            except Exception as e:
                logger.error(f"Failed to load file {self.dataset_files[self.current_file_index]}: {e}")
                self.current_file_index += 1

        if self.shuffle and self.data_cache:
            random.shuffle(self.data_cache)

        self.cache_index = 0
        self.total_samples_loaded += len(self.data_cache)
        logger.info(f"Loaded {len(self.data_cache)} samples into cache")

    def __len__(self):
        """Return approximate dataset size."""
        # Estimate based on files and average file size
        if not self.dataset_files:
            return 0

        # Assume average 1000 samples per file (adjust based on actual data)
        return len(self.dataset_files) * 1000

    def __getitem__(self, idx):
        """Get a single item from the dataset."""
        # Use modulo to handle idx beyond cache size
        cache_idx = idx % len(self.data_cache)

        # Refresh cache if we've used all samples
        if cache_idx == 0 and idx > 0:
            self._refresh_cache()
            if not self.data_cache:
                raise StopIteration("No more data available")

        item = self.data_cache[cache_idx]

        # Process based on task type
        if self.task_type == 'code_generation':
            return self._process_code_generation(item)
        elif self.task_type == 'text_classification':
            return self._process_text_classification(item)
        elif self.task_type == 'security_classification':
            return self._process_security_classification(item)
        else:
            return item

    def _process_code_generation(self, item: Dict) -> Dict:
        """Process code generation sample."""
        # Tokenize input and output
        input_text = item.get('input', '')
        output_text = item.get('output', '')

        # Tokenize
        inputs = self.tokenizer(
            input_text,
            max_length=256,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        outputs = self.tokenizer(
            output_text,
            max_length=256,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': outputs['input_ids'].squeeze(),
            'metadata': {
                'language': item.get('language', 'unknown'),
                'func_name': item.get('func_name', 'unknown')
            }
        }

    def _process_text_classification(self, item: Dict) -> Dict:
        """Process text classification sample."""
        text = item.get('text', '')
        label = item.get('label', 0)

        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=512,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

    def _process_security_classification(self, item: Dict) -> Dict:
        """Process security classification sample."""
        code = item.get('input', '')
        label = item.get('output', 0)

        # Tokenize
        inputs = self.tokenizer(
            code,
            max_length=512,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class CloudDatasetLoader:
    """
    Main loader for cloud datasets with streaming support.
    """

    def __init__(self,
                 task_type: str,
                 model_name: str = None,
                 batch_size: int = 32,
                 shuffle: bool = True,
                 num_workers: int = 0,
                 cache_size: int = 10000):
        """
        Initialize cloud dataset loader.

        Args:
            task_type: Type of task
            model_name: Model name for tokenizer
            batch_size: Batch size for training
            shuffle: Whether to shuffle data
            num_workers: Number of data loading workers
            cache_size: Size of in-memory cache
        """
        self.task_type = task_type
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_workers = num_workers
        self.cache_size = cache_size

        # Initialize storage service via Container (Clean Architecture v2.0)
        container = Container()
        self.storage = container.storage_service()
        if not self.storage.connect():
            raise ConnectionError("Failed to connect to cloud storage")

        # Initialize tokenizer
        if model_name:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        else:
            # Default tokenizers by task
            default_models = {
                'code_generation': 'Salesforce/codegen-350M-mono',
                'text_classification': 'microsoft/codebert-base',
                'security_classification': 'microsoft/codebert-base'
            }
            self.tokenizer = AutoTokenizer.from_pretrained(
                default_models.get(task_type, 'bert-base-uncased')
            )

        # Create dataset
        self.dataset = CloudDataset(
            task_type=task_type,
            tokenizer=self.tokenizer,
            storage_service=self.storage,
            cache_size=cache_size,
            shuffle=shuffle
        )

        # Create dataloader
        self.dataloader = DataLoader(
            self.dataset,
            batch_size=batch_size,
            shuffle=False,  # Shuffling handled by dataset
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )

    def get_dataloader(self) -> DataLoader:
        """Get PyTorch DataLoader."""
        return self.dataloader

    def get_batches(self) -> Generator:
        """Get batches generator for manual iteration."""
        for batch in self.dataloader:
            yield batch

    def stream_samples(self, max_samples: Optional[int] = None) -> Generator:
        """
        Stream individual samples from cloud storage.

        Args:
            max_samples: Maximum number of samples to stream

        Yields:
            Individual processed samples
        """
        samples_yielded = 0

        # List dataset files
        cloud_path = f"datasets/{self.task_type}/"
        dataset_files = self.storage.list_files(cloud_path)

        if not dataset_files:
            cloud_path = f"datasets/processed/{self.task_type}/"
            dataset_files = self.storage.list_files(cloud_path)

        for file_path in dataset_files:
            try:
                # Download file to temp
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
                    success = self.storage.download_file(file_path, tmp.name)

                    if success:
                        with open(tmp.name, 'r') as f:
                            data = json.load(f)

                        # Process each item
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if max_samples and samples_yielded >= max_samples:
                                return

                            # Process item based on task type
                            if self.task_type == 'code_generation':
                                yield self._process_code_item(item)
                            elif self.task_type == 'text_classification':
                                yield self._process_text_item(item)
                            elif self.task_type == 'security_classification':
                                yield self._process_security_item(item)
                            else:
                                yield item

                            samples_yielded += 1

                    os.unlink(tmp.name)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

    def _process_code_item(self, item: Dict) -> Tuple:
        """Process code generation item."""
        input_text = item.get('input', '')
        output_text = item.get('output', '')
        return input_text, output_text

    def _process_text_item(self, item: Dict) -> Tuple:
        """Process text classification item."""
        text = item.get('text', '')
        label = item.get('label', 0)
        return text, label

    def _process_security_item(self, item: Dict) -> Tuple:
        """Process security classification item."""
        code = item.get('input', '')
        label = item.get('output', 0)
        return code, label

    def get_dataset_info(self) -> Dict:
        """Get information about the cloud dataset."""
        cloud_path = f"datasets/{self.task_type}/"
        dataset_files = self.storage.list_files(cloud_path)

        if not dataset_files:
            cloud_path = f"datasets/processed/{self.task_type}/"
            dataset_files = self.storage.list_files(cloud_path)

        # Calculate total size
        total_size = 0
        for file_path in dataset_files[:10]:  # Sample first 10 files
            try:
                file_info = self.storage.get_file_info(file_path)
                if file_info:
                    total_size += file_info.get('size', 0)
            except:
                pass

        # Estimate total size
        if dataset_files and total_size > 0:
            avg_size = total_size / min(10, len(dataset_files))
            estimated_total = avg_size * len(dataset_files)
        else:
            estimated_total = 0

        return {
            'task_type': self.task_type,
            'num_files': len(dataset_files),
            'estimated_size_mb': estimated_total / (1024 * 1024),
            'estimated_samples': len(dataset_files) * 1000,  # Rough estimate
            'storage_provider': self.storage.provider,
            'files': dataset_files[:5]  # Show first 5 files
        }


def test_cloud_loader():
    """Test cloud dataset loader."""
    try:
        # Initialize loader
        loader = CloudDatasetLoader(
            task_type='code_generation',
            batch_size=16,
            cache_size=1000
        )

        # Get dataset info
        info = loader.get_dataset_info()
        print("Dataset Info:")
        print(json.dumps(info, indent=2))

        # Test streaming
        print("\nTesting streaming (first 5 samples):")
        for i, sample in enumerate(loader.stream_samples(max_samples=5)):
            print(f"Sample {i+1}: {sample[0][:50]}...")  # Show first 50 chars

        # Test batch loading
        print("\nTesting batch loading:")
        dataloader = loader.get_dataloader()
        for i, batch in enumerate(dataloader):
            if i >= 2:  # Only show first 2 batches
                break
            print(f"Batch {i+1} shape: {batch['input_ids'].shape}")

        print("\nCloud dataset loader test completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run test
    test_cloud_loader()