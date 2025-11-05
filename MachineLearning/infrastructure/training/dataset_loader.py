"""
Dataset Loader
==============

PyTorch Dataset implementation for ML training.

This component handles:
- Loading samples from JSON files
- Tokenization using HuggingFace tokenizers
- Batching and padding
- Train/test split
- Support for different task types

Supported Task Types:
--------------------
- text_classification: Binary or multi-class classification
- code_generation: Code generation with input/output pairs
- security_classification: 5-class security categorization

Example:
    >>> from infrastructure.training import ModelManager, DatasetLoader
    >>>
    >>> # Initialize model manager
    >>> manager = ModelManager(task='text_classification')
    >>> tokenizer = manager.get_tokenizer()
    >>>
    >>> # Load dataset
    >>> loader = DatasetLoader(
    ...     data_path='data/datasets/python_samples.json',
    ...     tokenizer=tokenizer,
    ...     task='text_classification',
    ...     max_length=512
    ... )
    >>>
    >>> # Get train/test split
    >>> train_dataset, test_dataset = loader.get_train_test_split(test_size=0.2)
    >>>
    >>> # Create PyTorch DataLoader
    >>> from torch.utils.data import DataLoader
    >>> train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

import torch
from torch.utils.data import Dataset

from domain.exceptions import DatasetError, ConfigurationError

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Supported ML tasks."""
    TEXT_CLASSIFICATION = "text_classification"
    CODE_GENERATION = "code_generation"
    SECURITY_CLASSIFICATION = "security_classification"


class CodeDataset(Dataset):
    """
    PyTorch Dataset for code samples.

    Handles tokenization, padding, and batching for different task types.

    Attributes:
        samples: List of samples with inputs and targets
        tokenizer: HuggingFace tokenizer
        task: Task type
        max_length: Maximum sequence length
        label_map: Optional mapping from labels to indices

    Example:
        >>> dataset = CodeDataset(
        ...     samples=samples,
        ...     tokenizer=tokenizer,
        ...     task='text_classification',
        ...     max_length=512
        ... )
        >>> sample = dataset[0]
        >>> print(sample['input_ids'].shape)  # torch.Size([512])
    """

    def __init__(
        self,
        samples: List[Dict[str, Any]],
        tokenizer,
        task: str,
        max_length: int = 512,
        label_map: Optional[Dict[str, int]] = None
    ):
        """
        Initialize CodeDataset.

        Args:
            samples: List of samples with 'code' and optionally 'label' or 'target'
            tokenizer: HuggingFace tokenizer
            task: Task type (text_classification, code_generation, security_classification)
            max_length: Maximum sequence length
            label_map: Optional mapping from label strings to indices

        Raises:
            ConfigurationError: If task is unsupported
            DatasetError: If samples format is invalid
        """
        try:
            self.task = TaskType(task)
        except ValueError:
            raise ConfigurationError(
                f"Unsupported task: {task}",
                details={'task': task, 'supported_tasks': [t.value for t in TaskType]}
            )

        if not samples:
            raise DatasetError("Cannot create dataset from empty samples list")

        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_map = label_map

        # Validate samples format
        self._validate_samples()

        # Create label map if needed for classification
        if self.label_map is None and self.task in [
            TaskType.TEXT_CLASSIFICATION,
            TaskType.SECURITY_CLASSIFICATION
        ]:
            self.label_map = self._create_label_map()

        logger.info(
            f"CodeDataset initialized: task={self.task.value}, "
            f"samples={len(self.samples)}, max_length={self.max_length}"
        )

    def _validate_samples(self) -> None:
        """
        Validate samples format.

        Raises:
            DatasetError: If samples format is invalid
        """
        for i, sample in enumerate(self.samples[:10]):  # Check first 10
            if 'code' not in sample:
                raise DatasetError(
                    f"Sample {i} missing 'code' field",
                    details={'sample': sample}
                )

            if self.task == TaskType.CODE_GENERATION:
                if 'target' not in sample and 'description' not in sample:
                    raise DatasetError(
                        f"Sample {i} missing 'target' or 'description' field for code generation",
                        details={'sample': sample}
                    )
            elif self.task in [TaskType.TEXT_CLASSIFICATION, TaskType.SECURITY_CLASSIFICATION]:
                if 'label' not in sample:
                    raise DatasetError(
                        f"Sample {i} missing 'label' field for classification",
                        details={'sample': sample}
                    )

    def _create_label_map(self) -> Dict[str, int]:
        """
        Create mapping from labels to indices.

        Returns:
            Label to index mapping

        Example:
            >>> # For binary classification
            >>> {'positive': 1, 'negative': 0}
            >>> # For security classification
            >>> {'safe': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        """
        # Collect unique labels
        unique_labels = set()
        for sample in self.samples:
            if 'label' in sample:
                unique_labels.add(sample['label'])

        # Sort for consistency
        sorted_labels = sorted(unique_labels)

        # Create mapping
        label_map = {label: idx for idx, label in enumerate(sorted_labels)}

        logger.info(f"Created label map: {label_map}")
        return label_map

    def __len__(self) -> int:
        """Get dataset size."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get tokenized sample.

        Args:
            idx: Sample index

        Returns:
            Dictionary with input_ids, attention_mask, and labels

        Example:
            >>> sample = dataset[0]
            >>> sample.keys()
            dict_keys(['input_ids', 'attention_mask', 'labels'])
        """
        sample = self.samples[idx]

        if self.task == TaskType.CODE_GENERATION:
            return self._prepare_generation_sample(sample)
        else:
            return self._prepare_classification_sample(sample)

    def _prepare_classification_sample(self, sample: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Prepare classification sample.

        Args:
            sample: Sample with 'code' and 'label'

        Returns:
            Tokenized sample with labels
        """
        # Tokenize code
        encoding = self.tokenizer(
            sample['code'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Get label index
        label_str = sample['label']
        label_idx = self.label_map.get(label_str, 0)

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label_idx, dtype=torch.long)
        }

    def _prepare_generation_sample(self, sample: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Prepare code generation sample.

        Args:
            sample: Sample with 'code' and 'target' or 'description'

        Returns:
            Tokenized sample with input and target
        """
        # Get input (description or prompt)
        input_text = sample.get('description', sample.get('prompt', ''))

        # Get target (code to generate)
        target_text = sample.get('target', sample['code'])

        # Tokenize input
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length // 2,  # Use half for input
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Tokenize target
        target_encoding = self.tokenizer(
            target_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # For causal LM, labels are same as input_ids
        # For seq2seq, labels are the target
        return {
            'input_ids': input_encoding['input_ids'].squeeze(0),
            'attention_mask': input_encoding['attention_mask'].squeeze(0),
            'labels': target_encoding['input_ids'].squeeze(0)
        }


class DatasetLoader:
    """
    Dataset Loader for ML training.

    Loads samples from JSON files and creates PyTorch datasets.

    Attributes:
        data_path: Path to JSON file with samples
        tokenizer: HuggingFace tokenizer
        task: Task type
        max_length: Maximum sequence length
        samples: Loaded samples

    Example:
        >>> loader = DatasetLoader(
        ...     data_path='data/datasets/python_samples.json',
        ...     tokenizer=tokenizer,
        ...     task='text_classification',
        ...     max_length=512
        ... )
        >>> train_ds, test_ds = loader.get_train_test_split(test_size=0.2)
    """

    def __init__(
        self,
        data_path: str,
        tokenizer,
        task: str,
        max_length: int = 512
    ):
        """
        Initialize DatasetLoader.

        Args:
            data_path: Path to JSON file with samples
            tokenizer: HuggingFace tokenizer
            task: Task type (text_classification, code_generation, security_classification)
            max_length: Maximum sequence length

        Raises:
            DatasetError: If data file not found or invalid format
            ConfigurationError: If task is unsupported
        """
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.task = task
        self.max_length = max_length

        # Load samples
        self.samples = self._load_samples()

        logger.info(
            f"DatasetLoader initialized: path={self.data_path}, "
            f"task={self.task}, samples={len(self.samples)}"
        )

    def _load_samples(self) -> List[Dict[str, Any]]:
        """
        Load samples from JSON file.

        Returns:
            List of samples

        Raises:
            DatasetError: If file not found or invalid format
        """
        if not self.data_path.exists():
            raise DatasetError(
                f"Dataset file not found: {self.data_path}",
                details={'path': str(self.data_path)}
            )

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict) and 'samples' in data:
                samples = data['samples']
            elif isinstance(data, dict) and 'data' in data:
                samples = data['data']
            else:
                raise DatasetError(
                    "JSON file must contain a list of samples or {'samples': [...]}",
                    details={'keys': list(data.keys()) if isinstance(data, dict) else None}
                )

            if not samples:
                raise DatasetError("Dataset file contains no samples")

            logger.info(f"Loaded {len(samples)} samples from {self.data_path}")
            return samples

        except json.JSONDecodeError as e:
            raise DatasetError(
                f"Invalid JSON format: {e}",
                details={'path': str(self.data_path)}
            )
        except Exception as e:
            raise DatasetError(
                f"Failed to load dataset: {e}",
                details={'path': str(self.data_path)}
            )

    def get_full_dataset(self) -> CodeDataset:
        """
        Get full dataset without splitting.

        Returns:
            CodeDataset with all samples

        Example:
            >>> dataset = loader.get_full_dataset()
            >>> print(len(dataset))
        """
        return CodeDataset(
            samples=self.samples,
            tokenizer=self.tokenizer,
            task=self.task,
            max_length=self.max_length
        )

    def get_train_test_split(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        shuffle: bool = True
    ) -> Tuple[CodeDataset, CodeDataset]:
        """
        Split dataset into train and test sets.

        Args:
            test_size: Fraction of samples for test set (0.0 to 1.0)
            random_state: Random seed for reproducibility
            shuffle: Whether to shuffle before splitting

        Returns:
            Tuple of (train_dataset, test_dataset)

        Raises:
            ConfigurationError: If test_size is invalid

        Example:
            >>> train_ds, test_ds = loader.get_train_test_split(test_size=0.2)
            >>> print(f"Train: {len(train_ds)}, Test: {len(test_ds)}")
        """
        if not 0.0 < test_size < 1.0:
            raise ConfigurationError(
                f"test_size must be between 0.0 and 1.0, got {test_size}"
            )

        # Shuffle samples if requested
        samples = self.samples.copy()
        if shuffle:
            import random
            random.seed(random_state)
            random.shuffle(samples)

        # Split
        split_idx = int(len(samples) * (1 - test_size))
        train_samples = samples[:split_idx]
        test_samples = samples[split_idx:]

        logger.info(
            f"Split dataset: train={len(train_samples)}, test={len(test_samples)} "
            f"(test_size={test_size})"
        )

        # Create datasets
        train_dataset = CodeDataset(
            samples=train_samples,
            tokenizer=self.tokenizer,
            task=self.task,
            max_length=self.max_length
        )

        test_dataset = CodeDataset(
            samples=test_samples,
            tokenizer=self.tokenizer,
            task=self.task,
            max_length=self.max_length
        )

        return train_dataset, test_dataset

    def get_num_samples(self) -> int:
        """
        Get total number of samples.

        Returns:
            Number of samples

        Example:
            >>> num_samples = loader.get_num_samples()
        """
        return len(self.samples)

    def get_sample_info(self) -> Dict[str, Any]:
        """
        Get information about the dataset.

        Returns:
            Dictionary with dataset statistics

        Example:
            >>> info = loader.get_sample_info()
            >>> print(f"Total samples: {info['total_samples']}")
        """
        info = {
            'total_samples': len(self.samples),
            'data_path': str(self.data_path),
            'task': self.task,
            'max_length': self.max_length
        }

        # Add task-specific info
        if self.task in ['text_classification', 'security_classification']:
            # Count labels
            label_counts = {}
            for sample in self.samples:
                label = sample.get('label', 'unknown')
                label_counts[label] = label_counts.get(label, 0) + 1
            info['label_distribution'] = label_counts

        return info

    def __str__(self) -> str:
        """String representation."""
        return (
            f"DatasetLoader(path={self.data_path.name}, task={self.task}, "
            f"samples={len(self.samples)})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"DatasetLoader(data_path='{self.data_path}', task='{self.task}', "
            f"max_length={self.max_length}, samples={len(self.samples)})"
        )
