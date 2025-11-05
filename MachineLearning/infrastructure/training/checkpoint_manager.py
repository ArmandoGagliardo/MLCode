"""
Checkpoint Manager
==================

Manages model checkpoints during training with automatic cleanup and recovery.

This component provides:
- Automatic checkpoint saving
- Best model tracking
- Checkpoint cleanup (keep only N best)
- Recovery from checkpoint
- Checkpoint metadata storage

Example:
    >>> from infrastructure.training import CheckpointManager
    >>>
    >>> # Create manager
    >>> manager = CheckpointManager(
    ...     checkpoint_dir='models/checkpoints',
    ...     max_checkpoints=3,
    ...     metric_name='eval_loss',
    ...     mode='min'
    ... )
    >>>
    >>> # Save checkpoint during training
    >>> for epoch in range(num_epochs):
    ...     train()
    ...     eval_loss = evaluate()
    ...     manager.save_checkpoint(
    ...         model=model,
    ...         optimizer=optimizer,
    ...         epoch=epoch,
    ...         metric_value=eval_loss
    ...     )
    >>>
    >>> # Load best checkpoint
    >>> checkpoint = manager.load_best_checkpoint()
    >>> model.load_state_dict(checkpoint['model_state_dict'])
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import torch
import torch.nn as nn

from domain.exceptions import CheckpointError, ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """
    Checkpoint metadata.

    Attributes:
        filename: Checkpoint filename
        epoch: Training epoch
        step: Global step
        metric_value: Metric value for this checkpoint
        metric_name: Name of metric
        timestamp: Creation timestamp
        is_best: Whether this is the best checkpoint
    """
    filename: str
    epoch: int
    step: int
    metric_value: float
    metric_name: str
    timestamp: float
    is_best: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CheckpointManager:
    """
    Checkpoint manager for model training.

    Features:
    - Automatic checkpoint saving
    - Best model tracking
    - Automatic cleanup (keep only N best)
    - Recovery from latest/best checkpoint
    - Metadata tracking

    Attributes:
        checkpoint_dir: Directory for storing checkpoints
        max_checkpoints: Maximum number of checkpoints to keep
        metric_name: Metric name for comparison
        mode: 'min' for loss metrics, 'max' for accuracy metrics
        checkpoints: List of checkpoint metadata

    Example:
        >>> manager = CheckpointManager(
        ...     checkpoint_dir='models/checkpoints',
        ...     max_checkpoints=3,
        ...     metric_name='eval_loss',
        ...     mode='min'
        ... )
        >>> manager.save_checkpoint(model, optimizer, epoch=0, metric_value=0.5)
    """

    def __init__(
        self,
        checkpoint_dir: str = 'models/checkpoints',
        max_checkpoints: int = 3,
        metric_name: str = 'eval_loss',
        mode: str = 'min'
    ):
        """
        Initialize CheckpointManager.

        Args:
            checkpoint_dir: Directory for storing checkpoints
            max_checkpoints: Maximum number of checkpoints to keep
            metric_name: Metric name for comparison (e.g., 'eval_loss', 'eval_accuracy')
            mode: 'min' (lower is better) or 'max' (higher is better)

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if mode not in ['min', 'max']:
            raise ConfigurationError(f"mode must be 'min' or 'max', got '{mode}'")

        if max_checkpoints < 1:
            raise ConfigurationError(f"max_checkpoints must be at least 1, got {max_checkpoints}")

        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.metric_name = metric_name
        self.mode = mode

        # Create checkpoint directory
        try:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create checkpoint directory: {e}")

        # Metadata file
        self.metadata_file = self.checkpoint_dir / 'checkpoints_metadata.json'

        # Load existing checkpoints
        self.checkpoints: List[CheckpointMetadata] = self._load_metadata()

        logger.info(
            f"CheckpointManager initialized: dir={self.checkpoint_dir}, "
            f"max={self.max_checkpoints}, metric={self.metric_name}, mode={self.mode}"
        )

    def _load_metadata(self) -> List[CheckpointMetadata]:
        """
        Load checkpoint metadata from file.

        Returns:
            List of checkpoint metadata
        """
        if not self.metadata_file.exists():
            return []

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            checkpoints = [
                CheckpointMetadata(**item) for item in data.get('checkpoints', [])
            ]

            logger.info(f"Loaded metadata for {len(checkpoints)} checkpoints")
            return checkpoints

        except Exception as e:
            logger.warning(f"Failed to load checkpoint metadata: {e}")
            return []

    def _save_metadata(self) -> None:
        """Save checkpoint metadata to file."""
        data = {
            'metric_name': self.metric_name,
            'mode': self.mode,
            'max_checkpoints': self.max_checkpoints,
            'checkpoints': [cp.to_dict() for cp in self.checkpoints]
        }

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved metadata for {len(self.checkpoints)} checkpoints")

    def save_checkpoint(
        self,
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        epoch: int = 0,
        step: int = 0,
        metric_value: Optional[float] = None,
        extra_state: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save a checkpoint.

        Args:
            model: PyTorch model
            optimizer: Optional optimizer
            scheduler: Optional learning rate scheduler
            epoch: Training epoch
            step: Global step
            metric_value: Metric value for this checkpoint
            extra_state: Optional extra state to save

        Returns:
            Path to saved checkpoint

        Example:
            >>> manager.save_checkpoint(
            ...     model=model,
            ...     optimizer=optimizer,
            ...     epoch=5,
            ...     metric_value=0.35
            ... )
        """
        import time

        # Generate filename
        filename = f"checkpoint_epoch{epoch}_step{step}.pt"
        checkpoint_path = self.checkpoint_dir / filename

        # Get model state dict (handle DataParallel)
        model_state = (
            model.module.state_dict()
            if hasattr(model, 'module')
            else model.state_dict()
        )

        # Prepare checkpoint data
        checkpoint_data = {
            'epoch': epoch,
            'step': step,
            'model_state_dict': model_state,
            'metric_name': self.metric_name,
            'metric_value': metric_value,
        }

        # Add optimizer state
        if optimizer is not None:
            checkpoint_data['optimizer_state_dict'] = optimizer.state_dict()

        # Add scheduler state
        if scheduler is not None:
            checkpoint_data['scheduler_state_dict'] = scheduler.state_dict()

        # Add extra state
        if extra_state is not None:
            checkpoint_data['extra_state'] = extra_state

        # Save checkpoint
        try:
            torch.save(checkpoint_data, checkpoint_path)
            logger.info(f"Saved checkpoint: {checkpoint_path}")
        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}")

        # Create metadata
        metadata = CheckpointMetadata(
            filename=filename,
            epoch=epoch,
            step=step,
            metric_value=metric_value if metric_value is not None else float('inf'),
            metric_name=self.metric_name,
            timestamp=time.time(),
            is_best=False
        )

        # Add to checkpoints
        self.checkpoints.append(metadata)

        # Check if this is the best checkpoint
        if self._is_best_checkpoint(metadata):
            # Mark previous best as not best
            for cp in self.checkpoints:
                cp.is_best = False
            # Mark this as best
            metadata.is_best = True

            # Save a copy as best_model.pt
            best_model_path = self.checkpoint_dir / 'best_model.pt'
            shutil.copy2(checkpoint_path, best_model_path)
            logger.info(f"New best model! Metric: {metric_value:.4f}")

        # Cleanup old checkpoints
        self._cleanup_checkpoints()

        # Save metadata
        self._save_metadata()

        return checkpoint_path

    def _is_best_checkpoint(self, metadata: CheckpointMetadata) -> bool:
        """
        Check if checkpoint is the best so far.

        Args:
            metadata: Checkpoint metadata

        Returns:
            True if this is the best checkpoint
        """
        if not self.checkpoints:
            return True

        # Get current best
        best_checkpoints = [cp for cp in self.checkpoints if cp.is_best]
        if not best_checkpoints:
            return True

        best_checkpoint = best_checkpoints[0]

        # Compare
        if self.mode == 'min':
            return metadata.metric_value < best_checkpoint.metric_value
        else:
            return metadata.metric_value > best_checkpoint.metric_value

    def _cleanup_checkpoints(self) -> None:
        """Remove old checkpoints, keeping only the N best."""
        if len(self.checkpoints) <= self.max_checkpoints:
            return

        # Sort checkpoints by metric value
        sorted_checkpoints = sorted(
            self.checkpoints,
            key=lambda cp: cp.metric_value,
            reverse=(self.mode == 'max')
        )

        # Keep best N checkpoints
        checkpoints_to_keep = sorted_checkpoints[:self.max_checkpoints]
        checkpoints_to_remove = sorted_checkpoints[self.max_checkpoints:]

        # Remove checkpoint files
        for cp in checkpoints_to_remove:
            checkpoint_path = self.checkpoint_dir / cp.filename
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                logger.info(f"Removed old checkpoint: {cp.filename}")

        # Update checkpoint list
        self.checkpoints = checkpoints_to_keep

    def load_checkpoint(self, filename: str) -> Dict[str, Any]:
        """
        Load a specific checkpoint.

        Args:
            filename: Checkpoint filename

        Returns:
            Checkpoint data

        Raises:
            CheckpointError: If checkpoint not found or cannot be loaded

        Example:
            >>> checkpoint = manager.load_checkpoint('checkpoint_epoch5_step1000.pt')
            >>> model.load_state_dict(checkpoint['model_state_dict'])
        """
        checkpoint_path = self.checkpoint_dir / filename

        if not checkpoint_path.exists():
            raise CheckpointError(f"Checkpoint not found: {filename}")

        try:
            checkpoint = torch.load(checkpoint_path, map_location='cpu')
            logger.info(f"Loaded checkpoint: {filename}")
            return checkpoint
        except Exception as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}")

    def load_best_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load the best checkpoint.

        Returns:
            Checkpoint data or None if no best checkpoint

        Example:
            >>> checkpoint = manager.load_best_checkpoint()
            >>> if checkpoint:
            ...     model.load_state_dict(checkpoint['model_state_dict'])
        """
        best_model_path = self.checkpoint_dir / 'best_model.pt'

        if not best_model_path.exists():
            logger.warning("No best model checkpoint found")
            return None

        try:
            checkpoint = torch.load(best_model_path, map_location='cpu')
            logger.info("Loaded best model checkpoint")
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to load best checkpoint: {e}")
            return None

    def load_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load the latest checkpoint.

        Returns:
            Checkpoint data or None if no checkpoints

        Example:
            >>> checkpoint = manager.load_latest_checkpoint()
            >>> if checkpoint:
            ...     model.load_state_dict(checkpoint['model_state_dict'])
        """
        if not self.checkpoints:
            logger.warning("No checkpoints found")
            return None

        # Get latest checkpoint (highest step)
        latest = max(self.checkpoints, key=lambda cp: cp.step)

        return self.load_checkpoint(latest.filename)

    def get_best_checkpoint_info(self) -> Optional[CheckpointMetadata]:
        """
        Get metadata for the best checkpoint.

        Returns:
            CheckpointMetadata or None if no best checkpoint

        Example:
            >>> info = manager.get_best_checkpoint_info()
            >>> print(f"Best epoch: {info.epoch}, metric: {info.metric_value:.4f}")
        """
        best_checkpoints = [cp for cp in self.checkpoints if cp.is_best]
        return best_checkpoints[0] if best_checkpoints else None

    def get_all_checkpoints(self) -> List[CheckpointMetadata]:
        """
        Get metadata for all checkpoints.

        Returns:
            List of checkpoint metadata

        Example:
            >>> for cp in manager.get_all_checkpoints():
            ...     print(f"Epoch {cp.epoch}: {cp.metric_value:.4f}")
        """
        return self.checkpoints.copy()

    def delete_checkpoint(self, filename: str) -> None:
        """
        Delete a specific checkpoint.

        Args:
            filename: Checkpoint filename

        Example:
            >>> manager.delete_checkpoint('checkpoint_epoch0_step0.pt')
        """
        checkpoint_path = self.checkpoint_dir / filename

        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"Deleted checkpoint: {filename}")

        # Remove from metadata
        self.checkpoints = [cp for cp in self.checkpoints if cp.filename != filename]
        self._save_metadata()

    def delete_all_checkpoints(self) -> None:
        """
        Delete all checkpoints.

        Example:
            >>> manager.delete_all_checkpoints()
        """
        for cp in self.checkpoints:
            checkpoint_path = self.checkpoint_dir / cp.filename
            if checkpoint_path.exists():
                checkpoint_path.unlink()

        # Delete best model
        best_model_path = self.checkpoint_dir / 'best_model.pt'
        if best_model_path.exists():
            best_model_path.unlink()

        self.checkpoints.clear()
        self._save_metadata()

        logger.info("Deleted all checkpoints")

    def __str__(self) -> str:
        """String representation."""
        return (
            f"CheckpointManager(dir={self.checkpoint_dir.name}, "
            f"checkpoints={len(self.checkpoints)}, "
            f"metric={self.metric_name}, mode={self.mode})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"CheckpointManager(checkpoint_dir='{self.checkpoint_dir}', "
            f"max_checkpoints={self.max_checkpoints}, "
            f"metric_name='{self.metric_name}', mode='{self.mode}')"
        )
