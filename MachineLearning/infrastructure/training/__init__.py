"""
Training Infrastructure
=======================

Infrastructure layer components for ML model training.

This module provides:
- ModelManager: Model initialization and configuration
- DatasetLoader: Dataset loading for PyTorch
- AdvancedTrainer: Multi-GPU training with mixed precision
- TrainingMetricsTracker: Real-time metrics tracking
- CheckpointManager: Checkpoint management and recovery

Example:
    >>> from infrastructure.training import ModelManager, DatasetLoader
    >>>
    >>> # Initialize model
    >>> manager = ModelManager(task='code_generation', model_name='Salesforce/codegen-350M-mono')
    >>> model, tokenizer = manager.get_model(), manager.get_tokenizer()
    >>>
    >>> # Load dataset
    >>> loader = DatasetLoader(
    ...     data_path='data/datasets/samples.json',
    ...     tokenizer=tokenizer,
    ...     task='code_generation'
    ... )
    >>> train_ds, test_ds = loader.get_train_test_split(test_size=0.2)
"""

from infrastructure.training.model_manager import ModelManager, TaskType, ModelType
from infrastructure.training.dataset_loader import DatasetLoader, CodeDataset
from infrastructure.training.advanced_trainer import AdvancedTrainer, TrainingConfig, TrainingState
from infrastructure.training.training_metrics_tracker import TrainingMetricsTracker, MetricEntry, MetricStatistics
from infrastructure.training.checkpoint_manager import CheckpointManager, CheckpointMetadata

__all__ = [
    'ModelManager',
    'TaskType',
    'ModelType',
    'DatasetLoader',
    'CodeDataset',
    'AdvancedTrainer',
    'TrainingConfig',
    'TrainingState',
    'TrainingMetricsTracker',
    'MetricEntry',
    'MetricStatistics',
    'CheckpointManager',
    'CheckpointMetadata',
]
