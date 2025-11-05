"""
Train Model Use Case
====================

Use case for training ML models on code datasets.

This use case orchestrates:
1. Dataset loading and validation
2. Model initialization
3. Training loop execution with advanced features (multi-GPU, mixed precision)
4. Validation and evaluation
5. Model persistence with checkpoint management

Example:
    >>> from application.use_cases.train_model import TrainModelUseCase, TrainModelRequest
    >>>
    >>> # Create use case
    >>> use_case = TrainModelUseCase()
    >>>
    >>> # Prepare request
    >>> request = TrainModelRequest(
    ...     dataset_path='data/datasets/python_samples.json',
    ...     task='text_classification',
    ...     model_name='microsoft/codebert-base',
    ...     num_labels=2,
    ...     epochs=10,
    ...     batch_size=8,
    ...     learning_rate=2e-5,
    ...     use_mixed_precision=True
    ... )
    >>>
    >>> # Execute training
    >>> response = use_case.execute(request)
    >>> print(f"Training completed: {response.success}")
    >>> print(f"Best metric: {response.best_metric:.4f}")
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.training import (
    ModelManager, DatasetLoader, AdvancedTrainer,
    TrainingMetricsTracker, CheckpointManager
)
from domain.exceptions import TrainingError, DatasetError, ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class TrainModelRequest:
    """
    Request object for model training.

    Attributes:
        dataset_path: Path to JSON file with training samples
        task: Task type ('text_classification', 'code_generation', 'security_classification')
        model_name: HuggingFace model name or path
        num_labels: Number of labels for classification tasks
        epochs: Number of training epochs
        batch_size: Batch size per device
        learning_rate: Learning rate
        max_length: Maximum sequence length
        output_dir: Directory for checkpoints and logs
        validation_split: Fraction of data for validation
        use_mixed_precision: Whether to use FP16 training
        gradient_accumulation_steps: Steps to accumulate gradients
        early_stopping_patience: Epochs without improvement before stopping
        warmup_steps: Number of warmup steps for learning rate
        weight_decay: Weight decay for regularization
        max_grad_norm: Maximum gradient norm for clipping
        seed: Random seed
        resume_from: Optional checkpoint path to resume from
    """
    dataset_path: str
    task: str = 'text_classification'
    model_name: Optional[str] = None
    num_labels: Optional[int] = None
    epochs: int = 10
    batch_size: int = 8
    learning_rate: float = 2e-5
    max_length: int = 512
    output_dir: str = 'models/checkpoints'
    validation_split: float = 0.2
    use_mixed_precision: bool = False
    gradient_accumulation_steps: int = 1
    early_stopping_patience: int = 3
    warmup_steps: int = 0
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    seed: int = 42
    resume_from: Optional[str] = None


@dataclass
class TrainModelResponse:
    """
    Response object for model training.

    Attributes:
        success: Whether training succeeded
        model_path: Path to saved best model
        checkpoint_dir: Directory with all checkpoints
        best_metric: Best evaluation metric achieved
        best_epoch: Epoch with best metric
        epochs_completed: Total epochs completed
        total_steps: Total training steps
        training_time: Total training time in seconds
        final_train_loss: Final training loss
        final_eval_loss: Final evaluation loss
        metrics_file: Path to metrics JSON file
        errors: List of errors encountered
    """
    success: bool
    model_path: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    best_metric: Optional[float] = None
    best_epoch: Optional[int] = None
    epochs_completed: int = 0
    total_steps: int = 0
    training_time: float = 0.0
    final_train_loss: Optional[float] = None
    final_eval_loss: Optional[float] = None
    metrics_file: Optional[str] = None
    errors: list = field(default_factory=list)


class TrainModelUseCase:
    """
    Use case for training ML models on code datasets.

    This use case orchestrates the complete training pipeline:
    - Dataset loading and preprocessing
    - Model initialization with HuggingFace
    - Advanced training (multi-GPU, mixed precision)
    - Metrics tracking
    - Checkpoint management
    - Error handling and recovery

    Features:
    - Supports text classification, code generation, security classification
    - Multi-GPU training with DataParallel
    - Mixed precision (FP16) for faster training
    - Early stopping to prevent overfitting
    - Automatic checkpoint cleanup
    - Real-time metrics tracking

    Example:
        >>> use_case = TrainModelUseCase()
        >>>
        >>> request = TrainModelRequest(
        ...     dataset_path='data/datasets/python_samples.json',
        ...     task='text_classification',
        ...     model_name='microsoft/codebert-base',
        ...     num_labels=2,
        ...     epochs=10,
        ...     batch_size=8,
        ...     use_mixed_precision=True
        ... )
        >>> response = use_case.execute(request)
        >>>
        >>> if response.success:
        ...     print(f"Model saved to: {response.model_path}")
        ...     print(f"Best metric: {response.best_metric:.4f}")
    """

    def __init__(self):
        """Initialize training use case."""
        logger.info("TrainModelUseCase initialized")

    def execute(self, request: TrainModelRequest) -> TrainModelResponse:
        """
        Execute the model training use case.

        Args:
            request: Training request parameters

        Returns:
            TrainModelResponse with training results

        Raises:
            TrainingError: If training fails
            DatasetError: If dataset cannot be loaded
            ConfigurationError: If configuration is invalid

        Example:
            >>> request = TrainModelRequest(
            ...     dataset_path='data/datasets/samples.json',
            ...     task='text_classification',
            ...     num_labels=2,
            ...     epochs=10
            ... )
            >>> response = use_case.execute(request)
            >>> print(f"Success: {response.success}")
        """
        logger.info("=" * 60)
        logger.info("Starting TrainModelUseCase execution")
        logger.info(f"Task: {request.task}, Epochs: {request.epochs}")
        logger.info("=" * 60)

        start_time = time.time()

        try:
            # Step 1: Validate request
            logger.info("Step 1: Validating request...")
            self._validate_request(request)

            # Step 2: Initialize model manager
            logger.info(f"Step 2: Initializing model ({request.task})...")
            model_manager = ModelManager(
                task=request.task,
                model_name=request.model_name,
                num_labels=request.num_labels
            )
            model = model_manager.get_model()
            tokenizer = model_manager.get_tokenizer()
            logger.info(f"Model: {model_manager.get_model_name()}")
            logger.info(f"Device: {model_manager.device}")

            # Step 3: Load dataset
            logger.info(f"Step 3: Loading dataset from {request.dataset_path}...")
            dataset_loader = DatasetLoader(
                data_path=request.dataset_path,
                tokenizer=tokenizer,
                task=request.task,
                max_length=request.max_length
            )
            train_dataset, eval_dataset = dataset_loader.get_train_test_split(
                test_size=request.validation_split,
                random_state=request.seed
            )
            logger.info(f"Train samples: {len(train_dataset)}")
            logger.info(f"Eval samples: {len(eval_dataset)}")

            # Step 4: Initialize metrics tracker
            logger.info("Step 4: Initializing metrics tracker...")
            experiment_name = f"{request.task}_{model_manager.get_model_name().split('/')[-1]}"
            metrics_tracker = TrainingMetricsTracker(
                output_dir=Path(request.output_dir) / 'logs',
                experiment_name=experiment_name
            )

            # Step 5: Initialize checkpoint manager
            logger.info("Step 5: Initializing checkpoint manager...")
            checkpoint_manager = CheckpointManager(
                checkpoint_dir=request.output_dir,
                max_checkpoints=3,
                metric_name='eval_loss',
                mode='min'
            )

            # Step 6: Create trainer
            logger.info("Step 6: Creating advanced trainer...")
            trainer = AdvancedTrainer(
                model=model,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                output_dir=request.output_dir,
                num_epochs=request.epochs,
                batch_size=request.batch_size,
                learning_rate=request.learning_rate,
                weight_decay=request.weight_decay,
                warmup_steps=request.warmup_steps,
                gradient_accumulation_steps=request.gradient_accumulation_steps,
                max_grad_norm=request.max_grad_norm,
                use_mixed_precision=request.use_mixed_precision,
                early_stopping_patience=request.early_stopping_patience,
                seed=request.seed
            )

            # Step 7: Train model
            logger.info("Step 7: Starting training...")
            logger.info("=" * 60)
            training_results = trainer.train()
            logger.info("=" * 60)

            # Step 8: Save metrics
            logger.info("Step 8: Saving metrics...")
            metrics_file = Path(request.output_dir) / 'logs' / f"{experiment_name}_metrics.json"
            metrics_tracker.save()

            # Step 9: Get best model path
            best_model_path = Path(request.output_dir) / 'best_model.pt'
            if not best_model_path.exists():
                logger.warning("Best model not found, using latest checkpoint")
                best_model_path = None

            # Calculate training time
            training_time = time.time() - start_time

            # Create successful response
            response = TrainModelResponse(
                success=True,
                model_path=str(best_model_path) if best_model_path else None,
                checkpoint_dir=str(request.output_dir),
                best_metric=training_results.get('best_metric'),
                best_epoch=training_results.get('best_epoch'),
                epochs_completed=request.epochs,
                total_steps=training_results.get('total_steps', 0),
                training_time=training_time,
                metrics_file=str(metrics_file)
            )

            logger.info("=" * 60)
            logger.info("Training completed successfully!")
            logger.info(f"Best metric: {response.best_metric:.4f}")
            logger.info(f"Best epoch: {response.best_epoch + 1}")
            logger.info(f"Total time: {training_time:.2f}s")
            logger.info(f"Model saved to: {response.model_path}")
            logger.info("=" * 60)

            return response

        except (TrainingError, DatasetError, ConfigurationError) as e:
            logger.error(f"Training failed (expected error): {e}")
            return TrainModelResponse(
                success=False,
                errors=[str(e)]
            )

        except Exception as e:
            logger.error(f"Training failed (unexpected error): {e}", exc_info=True)
            return TrainModelResponse(
                success=False,
                errors=[f"Unexpected error: {str(e)}"]
            )

    def _validate_request(self, request: TrainModelRequest) -> None:
        """
        Validate training request.

        Args:
            request: Training request

        Raises:
            ConfigurationError: If request is invalid
            FileNotFoundError: If dataset file not found
        """
        # Check dataset exists
        if not Path(request.dataset_path).exists():
            raise FileNotFoundError(f"Dataset not found: {request.dataset_path}")

        # Validate task
        valid_tasks = ['text_classification', 'code_generation', 'security_classification']
        if request.task not in valid_tasks:
            raise ConfigurationError(
                f"Invalid task: {request.task}. Must be one of {valid_tasks}"
            )

        # Validate epochs
        if request.epochs <= 0:
            raise ConfigurationError(f"epochs must be positive, got {request.epochs}")

        # Validate batch_size
        if request.batch_size <= 0:
            raise ConfigurationError(f"batch_size must be positive, got {request.batch_size}")

        # Validate learning_rate
        if request.learning_rate <= 0:
            raise ConfigurationError(f"learning_rate must be positive, got {request.learning_rate}")

        # Validate validation_split
        if not 0 < request.validation_split < 1:
            raise ConfigurationError(
                f"validation_split must be between 0 and 1, got {request.validation_split}"
            )

        # Validate num_labels for classification tasks
        if request.task in ['text_classification', 'security_classification']:
            if request.num_labels is None:
                raise ConfigurationError(
                    f"num_labels is required for task '{request.task}'"
                )
            if request.num_labels < 2:
                raise ConfigurationError(
                    f"num_labels must be at least 2, got {request.num_labels}"
                )

        logger.info("Request validation passed")

    def __str__(self) -> str:
        """String representation."""
        return "TrainModelUseCase()"

    def __repr__(self) -> str:
        """Detailed representation."""
        return "TrainModelUseCase()"
