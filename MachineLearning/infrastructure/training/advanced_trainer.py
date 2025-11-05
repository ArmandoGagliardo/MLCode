"""
Advanced Trainer
================

Advanced training implementation with multi-GPU, mixed precision, and gradient accumulation.

This component provides:
- Multi-GPU training with DataParallel
- Mixed precision training (FP16) for faster training
- Gradient accumulation for large effective batch sizes
- Early stopping to prevent overfitting
- Learning rate scheduling
- Gradient clipping for stability
- Training state management

Example:
    >>> from infrastructure.training import ModelManager, DatasetLoader, AdvancedTrainer
    >>>
    >>> # Initialize components
    >>> manager = ModelManager(task='text_classification', num_labels=2)
    >>> loader = DatasetLoader(data_path='data/datasets/samples.json',
    ...                        tokenizer=manager.get_tokenizer(), task='text_classification')
    >>> train_ds, val_ds = loader.get_train_test_split(test_size=0.2)
    >>>
    >>> # Create trainer
    >>> trainer = AdvancedTrainer(
    ...     model=manager.get_model(),
    ...     train_dataset=train_ds,
    ...     eval_dataset=val_ds,
    ...     output_dir='models/checkpoints',
    ...     num_epochs=10,
    ...     batch_size=8,
    ...     learning_rate=2e-5,
    ...     use_mixed_precision=True,
    ...     gradient_accumulation_steps=4
    ... )
    >>>
    >>> # Train
    >>> trainer.train()
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import get_linear_schedule_with_warmup

from domain.exceptions import TrainingError, ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """
    Training configuration.

    Attributes:
        output_dir: Directory for saving checkpoints and logs
        num_epochs: Number of training epochs
        batch_size: Batch size per device
        learning_rate: Learning rate
        weight_decay: Weight decay for regularization
        warmup_steps: Number of warmup steps for learning rate
        gradient_accumulation_steps: Number of steps to accumulate gradients
        max_grad_norm: Maximum gradient norm for clipping
        use_mixed_precision: Whether to use mixed precision (FP16)
        early_stopping_patience: Stop if no improvement for N epochs
        eval_steps: Evaluate every N steps
        save_steps: Save checkpoint every N steps
        logging_steps: Log metrics every N steps
        max_checkpoints: Maximum number of checkpoints to keep
    """
    output_dir: str
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_steps: int = 0
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    use_mixed_precision: bool = False
    early_stopping_patience: int = 3
    eval_steps: Optional[int] = None
    save_steps: Optional[int] = None
    logging_steps: int = 10
    max_checkpoints: int = 3
    seed: int = 42

    def __post_init__(self):
        """Validate configuration."""
        if self.num_epochs < 1:
            raise ConfigurationError("num_epochs must be at least 1")
        if self.batch_size < 1:
            raise ConfigurationError("batch_size must be at least 1")
        if self.learning_rate <= 0:
            raise ConfigurationError("learning_rate must be positive")
        if self.gradient_accumulation_steps < 1:
            raise ConfigurationError("gradient_accumulation_steps must be at least 1")


@dataclass
class TrainingState:
    """
    Training state for resuming.

    Attributes:
        epoch: Current epoch
        global_step: Total training steps
        best_metric: Best evaluation metric
        best_epoch: Epoch with best metric
        patience_counter: Steps without improvement
        is_training: Whether currently training
        start_time: Training start timestamp
        total_train_time: Total training time in seconds
    """
    epoch: int = 0
    global_step: int = 0
    best_metric: float = float('inf')
    best_epoch: int = 0
    patience_counter: int = 0
    is_training: bool = False
    start_time: float = 0.0
    total_train_time: float = 0.0


class AdvancedTrainer:
    """
    Advanced trainer with multi-GPU and mixed precision support.

    Features:
    - Multi-GPU training with DataParallel
    - Mixed precision (FP16) for faster training
    - Gradient accumulation
    - Early stopping
    - Learning rate scheduling
    - Gradient clipping
    - Checkpoint management

    Attributes:
        model: PyTorch model to train
        train_dataset: Training dataset
        eval_dataset: Evaluation dataset (optional)
        config: Training configuration
        device: Training device
        state: Training state

    Example:
        >>> trainer = AdvancedTrainer(
        ...     model=model,
        ...     train_dataset=train_ds,
        ...     eval_dataset=val_ds,
        ...     output_dir='models/checkpoints',
        ...     num_epochs=10
        ... )
        >>> trainer.train()
    """

    def __init__(
        self,
        model: nn.Module,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = 'models/checkpoints',
        num_epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
        weight_decay: float = 0.01,
        warmup_steps: int = 0,
        gradient_accumulation_steps: int = 1,
        max_grad_norm: float = 1.0,
        use_mixed_precision: bool = False,
        early_stopping_patience: int = 3,
        eval_steps: Optional[int] = None,
        save_steps: Optional[int] = None,
        logging_steps: int = 10,
        max_checkpoints: int = 3,
        seed: int = 42,
        metrics_callback: Optional[Callable] = None
    ):
        """
        Initialize AdvancedTrainer.

        Args:
            model: PyTorch model to train
            train_dataset: Training dataset
            eval_dataset: Evaluation dataset (optional)
            output_dir: Directory for checkpoints and logs
            num_epochs: Number of training epochs
            batch_size: Batch size per device
            learning_rate: Learning rate
            weight_decay: Weight decay for regularization
            warmup_steps: Number of warmup steps
            gradient_accumulation_steps: Steps to accumulate gradients
            max_grad_norm: Maximum gradient norm for clipping
            use_mixed_precision: Whether to use FP16
            early_stopping_patience: Stop if no improvement for N epochs
            eval_steps: Evaluate every N steps (default: once per epoch)
            save_steps: Save checkpoint every N steps (default: once per epoch)
            logging_steps: Log metrics every N steps
            max_checkpoints: Maximum checkpoints to keep
            seed: Random seed
            metrics_callback: Optional callback for custom metrics tracking
        """
        self.model = model
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.metrics_callback = metrics_callback

        # Create configuration
        self.config = TrainingConfig(
            output_dir=output_dir,
            num_epochs=num_epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            warmup_steps=warmup_steps,
            gradient_accumulation_steps=gradient_accumulation_steps,
            max_grad_norm=max_grad_norm,
            use_mixed_precision=use_mixed_precision,
            early_stopping_patience=early_stopping_patience,
            eval_steps=eval_steps,
            save_steps=save_steps,
            logging_steps=logging_steps,
            max_checkpoints=max_checkpoints,
            seed=seed
        )

        # Initialize training state
        self.state = TrainingState()

        # Set random seed
        self._set_seed(seed)

        # Setup device and model
        self.device = self._setup_device()
        self.model = self._setup_model()

        # Create output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.optimizer = None
        self.scheduler = None
        self.scaler = None  # For mixed precision
        self.train_dataloader = None
        self.eval_dataloader = None

        logger.info(
            f"AdvancedTrainer initialized: device={self.device}, "
            f"epochs={num_epochs}, batch_size={batch_size}, "
            f"mixed_precision={use_mixed_precision}"
        )

    def _set_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        import random
        import numpy as np

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def _setup_device(self) -> str:
        """
        Setup training device (CPU/GPU/Multi-GPU).

        Returns:
            Device string
        """
        if torch.cuda.is_available():
            device = "cuda"
            gpu_count = torch.cuda.device_count()
            logger.info(f"Using {gpu_count} GPU(s) for training")
        else:
            device = "cpu"
            logger.info("Using CPU for training")

        return device

    def _setup_model(self) -> nn.Module:
        """
        Setup model for training (move to device, enable multi-GPU).

        Returns:
            Configured model
        """
        # Move model to device
        self.model.to(self.device)

        # Enable multi-GPU if available
        if self.device == "cuda" and torch.cuda.device_count() > 1:
            self.model = nn.DataParallel(self.model)
            logger.info(f"Enabled DataParallel for {torch.cuda.device_count()} GPUs")

        return self.model

    def _create_dataloaders(self) -> None:
        """Create train and eval dataloaders."""
        self.train_dataloader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0,  # Windows compatibility
            pin_memory=self.device == "cuda"
        )

        if self.eval_dataset is not None:
            self.eval_dataloader = DataLoader(
                self.eval_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=0,
                pin_memory=self.device == "cuda"
            )

        logger.info(
            f"Created dataloaders: train_batches={len(self.train_dataloader)}, "
            f"eval_batches={len(self.eval_dataloader) if self.eval_dataloader else 0}"
        )

    def _create_optimizer(self) -> None:
        """Create optimizer with weight decay."""
        # Separate parameters with/without weight decay
        no_decay = ['bias', 'LayerNorm.weight', 'layer_norm.weight']
        optimizer_grouped_parameters = [
            {
                'params': [p for n, p in self.model.named_parameters()
                          if not any(nd in n for nd in no_decay)],
                'weight_decay': self.config.weight_decay
            },
            {
                'params': [p for n, p in self.model.named_parameters()
                          if any(nd in n for nd in no_decay)],
                'weight_decay': 0.0
            }
        ]

        self.optimizer = AdamW(
            optimizer_grouped_parameters,
            lr=self.config.learning_rate
        )

        logger.info(f"Created AdamW optimizer with lr={self.config.learning_rate}")

    def _create_scheduler(self, num_training_steps: int) -> None:
        """
        Create learning rate scheduler.

        Args:
            num_training_steps: Total training steps
        """
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=num_training_steps
        )

        logger.info(
            f"Created scheduler: warmup_steps={self.config.warmup_steps}, "
            f"total_steps={num_training_steps}"
        )

    def _create_scaler(self) -> None:
        """Create gradient scaler for mixed precision."""
        if self.config.use_mixed_precision and self.device == "cuda":
            self.scaler = torch.cuda.amp.GradScaler()
            logger.info("Enabled mixed precision training (FP16)")

    def train(self) -> Dict[str, Any]:
        """
        Run training loop.

        Returns:
            Training results with metrics

        Raises:
            TrainingError: If training fails
        """
        try:
            # Setup training components
            self._create_dataloaders()
            self._create_optimizer()

            # Calculate total steps
            num_training_steps = (
                len(self.train_dataloader)
                * self.config.num_epochs
                // self.config.gradient_accumulation_steps
            )

            self._create_scheduler(num_training_steps)
            self._create_scaler()

            # Set default eval/save steps if not provided
            if self.config.eval_steps is None:
                self.config.eval_steps = len(self.train_dataloader)
            if self.config.save_steps is None:
                self.config.save_steps = len(self.train_dataloader)

            # Start training
            self.state.is_training = True
            self.state.start_time = time.time()

            logger.info("=" * 60)
            logger.info("Starting training")
            logger.info(f"  Num examples: {len(self.train_dataset)}")
            logger.info(f"  Num epochs: {self.config.num_epochs}")
            logger.info(f"  Batch size: {self.config.batch_size}")
            logger.info(f"  Gradient accumulation steps: {self.config.gradient_accumulation_steps}")
            logger.info(f"  Total optimization steps: {num_training_steps}")
            logger.info("=" * 60)

            # Training loop
            for epoch in range(self.config.num_epochs):
                self.state.epoch = epoch

                logger.info(f"\nEpoch {epoch + 1}/{self.config.num_epochs}")

                # Train one epoch
                train_metrics = self._train_epoch()

                # Evaluate
                if self.eval_dataset is not None:
                    eval_metrics = self.evaluate()

                    # Check for improvement
                    current_metric = eval_metrics.get('eval_loss', float('inf'))
                    if current_metric < self.state.best_metric:
                        self.state.best_metric = current_metric
                        self.state.best_epoch = epoch
                        self.state.patience_counter = 0

                        # Save best model
                        self._save_checkpoint(is_best=True)
                        logger.info(f"New best model! Loss: {current_metric:.4f}")
                    else:
                        self.state.patience_counter += 1
                        logger.info(
                            f"No improvement for {self.state.patience_counter} epoch(s). "
                            f"Best: {self.state.best_metric:.4f}"
                        )

                    # Early stopping
                    if self.state.patience_counter >= self.config.early_stopping_patience:
                        logger.info("Early stopping triggered")
                        break

            # Training completed
            self.state.is_training = False
            self.state.total_train_time = time.time() - self.state.start_time

            logger.info("=" * 60)
            logger.info("Training completed!")
            logger.info(f"  Total time: {self.state.total_train_time:.2f}s")
            logger.info(f"  Best epoch: {self.state.best_epoch + 1}")
            logger.info(f"  Best metric: {self.state.best_metric:.4f}")
            logger.info("=" * 60)

            return {
                'best_metric': self.state.best_metric,
                'best_epoch': self.state.best_epoch,
                'total_time': self.state.total_train_time,
                'total_steps': self.state.global_step
            }

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            raise TrainingError(f"Training failed: {e}")

    def _train_epoch(self) -> Dict[str, float]:
        """
        Train for one epoch.

        Returns:
            Training metrics
        """
        self.model.train()

        total_loss = 0.0
        num_batches = 0

        for step, batch in enumerate(self.train_dataloader):
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Forward pass with mixed precision
            if self.scaler is not None:
                with torch.cuda.amp.autocast():
                    outputs = self.model(**batch)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    loss = loss / self.config.gradient_accumulation_steps

                # Backward pass with scaling
                self.scaler.scale(loss).backward()
            else:
                outputs = self.model(**batch)
                loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                loss = loss / self.config.gradient_accumulation_steps
                loss.backward()

            total_loss += loss.item()

            # Update weights
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                # Clip gradients
                if self.scaler is not None:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.max_grad_norm
                    )
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.max_grad_norm
                    )
                    self.optimizer.step()

                self.scheduler.step()
                self.optimizer.zero_grad()
                self.state.global_step += 1

                # Logging
                if self.state.global_step % self.config.logging_steps == 0:
                    avg_loss = total_loss / (num_batches + 1)
                    logger.info(
                        f"Step {self.state.global_step}: loss={avg_loss:.4f}, "
                        f"lr={self.scheduler.get_last_lr()[0]:.2e}"
                    )

                # Save checkpoint
                if self.state.global_step % self.config.save_steps == 0:
                    self._save_checkpoint()

            num_batches += 1

        avg_loss = total_loss / num_batches
        return {'train_loss': avg_loss}

    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate model on eval dataset.

        Returns:
            Evaluation metrics
        """
        if self.eval_dataloader is None:
            return {}

        self.model.eval()

        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in self.eval_dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}

                outputs = self.model(**batch)
                loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches

        logger.info(f"Evaluation: loss={avg_loss:.4f}")

        return {'eval_loss': avg_loss}

    def _save_checkpoint(self, is_best: bool = False) -> None:
        """
        Save model checkpoint.

        Args:
            is_best: Whether this is the best model
        """
        checkpoint_name = "best_model.pt" if is_best else f"checkpoint-{self.state.global_step}.pt"
        checkpoint_path = self.output_dir / checkpoint_name

        # Get model state dict (handle DataParallel)
        model_state = (
            self.model.module.state_dict()
            if hasattr(self.model, 'module')
            else self.model.state_dict()
        )

        torch.save({
            'epoch': self.state.epoch,
            'global_step': self.state.global_step,
            'model_state_dict': model_state,
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_metric': self.state.best_metric,
            'config': self.config
        }, checkpoint_path)

        logger.info(f"Saved checkpoint: {checkpoint_path}")

    def get_state(self) -> TrainingState:
        """Get current training state."""
        return self.state

    def get_config(self) -> TrainingConfig:
        """Get training configuration."""
        return self.config
