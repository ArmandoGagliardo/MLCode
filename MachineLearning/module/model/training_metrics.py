"""
Training Metrics Tracking System

Comprehensive tracking of training metrics:
- Loss tracking (training/validation)
- Learning rate monitoring
- Gradient statistics
- Memory usage
- Time per epoch/batch
- Model performance metrics
"""

import json
import time
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


@dataclass
class EpochMetrics:
    """Metrics for a single epoch."""

    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    learning_rate: float = 0.0
    train_time_seconds: float = 0.0
    samples_per_second: float = 0.0
    peak_memory_mb: float = 0.0
    gradient_norm: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BatchMetrics:
    """Metrics for a single batch."""

    step: int
    loss: float
    learning_rate: float
    time_seconds: float
    memory_mb: float = 0.0


class TrainingMetricsTracker:
    """Track and analyze training metrics."""

    def __init__(self, save_dir: str, experiment_name: str = "training"):
        """
        Initialize metrics tracker.

        Args:
            save_dir: Directory to save metrics
            experiment_name: Name of the experiment
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_name = experiment_name
        self.start_time = time.time()

        # Storage
        self.epoch_metrics: List[EpochMetrics] = []
        self.batch_metrics: List[BatchMetrics] = []

        # Best metrics tracking
        self.best_train_loss = float('inf')
        self.best_val_loss = float('inf')
        self.best_epoch = 0

        # Current state
        self.current_epoch = 0
        self.total_batches = 0

        logger.info(f"[INIT] Metrics tracker initialized: {self.save_dir}")

    def record_batch(
        self,
        step: int,
        loss: float,
        learning_rate: float,
        batch_time: float
    ):
        """
        Record batch-level metrics.

        Args:
            step: Global step number
            loss: Batch loss
            learning_rate: Current learning rate
            batch_time: Time to process batch (seconds)
        """
        memory_mb = 0.0
        if torch.cuda.is_available():
            memory_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

        metrics = BatchMetrics(
            step=step,
            loss=loss,
            learning_rate=learning_rate,
            time_seconds=batch_time,
            memory_mb=memory_mb
        )

        self.batch_metrics.append(metrics)
        self.total_batches += 1

    def record_epoch(
        self,
        epoch: int,
        train_loss: float,
        val_loss: Optional[float],
        learning_rate: float,
        epoch_time: float,
        num_samples: int,
        gradient_norm: Optional[float] = None
    ):
        """
        Record epoch-level metrics.

        Args:
            epoch: Epoch number
            train_loss: Average training loss
            val_loss: Average validation loss (if available)
            learning_rate: Learning rate at end of epoch
            epoch_time: Time for epoch (seconds)
            num_samples: Number of training samples
            gradient_norm: Gradient norm (if available)
        """
        peak_memory_mb = 0.0
        if torch.cuda.is_available():
            peak_memory_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

        samples_per_second = num_samples / epoch_time if epoch_time > 0 else 0.0

        metrics = EpochMetrics(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            learning_rate=learning_rate,
            train_time_seconds=epoch_time,
            samples_per_second=samples_per_second,
            peak_memory_mb=peak_memory_mb,
            gradient_norm=gradient_norm
        )

        self.epoch_metrics.append(metrics)
        self.current_epoch = epoch

        # Update best metrics
        if train_loss < self.best_train_loss:
            self.best_train_loss = train_loss
            self.best_epoch = epoch

        if val_loss is not None and val_loss < self.best_val_loss:
            self.best_val_loss = val_loss

        # Auto-save after each epoch
        self.save()

        val_loss_str = f"{val_loss:.4f}" if val_loss is not None else "N/A"
        logger.info(
            f"[EPOCH {epoch}] "
            f"Train Loss: {train_loss:.4f}, "
            f"Val Loss: {val_loss_str}, "
            f"LR: {learning_rate:.2e}, "
            f"Time: {epoch_time:.2f}s"
        )

    def get_epoch_metrics(self, epoch: int) -> Optional[EpochMetrics]:
        """Get metrics for specific epoch."""
        for metrics in self.epoch_metrics:
            if metrics.epoch == epoch:
                return metrics
        return None

    def get_latest_epoch_metrics(self) -> Optional[EpochMetrics]:
        """Get metrics for latest epoch."""
        if self.epoch_metrics:
            return self.epoch_metrics[-1]
        return None

    def get_moving_average(self, window: int = 5) -> List[float]:
        """Get moving average of training loss."""
        if len(self.epoch_metrics) < window:
            return [m.train_loss for m in self.epoch_metrics]

        moving_avg = []
        for i in range(len(self.epoch_metrics)):
            start = max(0, i - window + 1)
            end = i + 1
            window_losses = [m.train_loss for m in self.epoch_metrics[start:end]]
            moving_avg.append(sum(window_losses) / len(window_losses))

        return moving_avg

    def is_improving(self, patience: int = 3) -> bool:
        """
        Check if model is still improving.

        Args:
            patience: Number of epochs to look back

        Returns:
            True if improving, False otherwise
        """
        if len(self.epoch_metrics) < patience + 1:
            return True

        recent_losses = [m.val_loss or m.train_loss for m in self.epoch_metrics[-patience-1:]]

        # Check if recent losses are decreasing
        return recent_losses[-1] < recent_losses[0]

    def should_stop_early(self, patience: int = 5, min_delta: float = 1e-4) -> bool:
        """
        Check if training should stop early.

        Args:
            patience: Number of epochs without improvement
            min_delta: Minimum change to be considered improvement

        Returns:
            True if should stop, False otherwise
        """
        if len(self.epoch_metrics) < patience + 1:
            return False

        # Get validation or training loss
        recent_losses = [m.val_loss or m.train_loss for m in self.epoch_metrics[-patience-1:]]

        best_recent = min(recent_losses[:-1])
        current = recent_losses[-1]

        # No improvement if current loss is not better by min_delta
        return current >= (best_recent - min_delta)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        total_time = time.time() - self.start_time

        summary = {
            'experiment_name': self.experiment_name,
            'total_epochs': len(self.epoch_metrics),
            'total_batches': self.total_batches,
            'total_time_hours': total_time / 3600,
            'best_train_loss': self.best_train_loss,
            'best_val_loss': self.best_val_loss if self.best_val_loss != float('inf') else None,
            'best_epoch': self.best_epoch,
            'current_epoch': self.current_epoch
        }

        # Latest metrics
        if self.epoch_metrics:
            latest = self.epoch_metrics[-1]
            summary['latest_train_loss'] = latest.train_loss
            summary['latest_val_loss'] = latest.val_loss
            summary['latest_learning_rate'] = latest.learning_rate
            summary['avg_samples_per_second'] = sum(m.samples_per_second for m in self.epoch_metrics) / len(self.epoch_metrics)

        # Resource usage
        if self.epoch_metrics:
            summary['peak_memory_mb'] = max(m.peak_memory_mb for m in self.epoch_metrics)
            summary['avg_epoch_time'] = sum(m.train_time_seconds for m in self.epoch_metrics) / len(self.epoch_metrics)

        return summary

    def save(self):
        """Save metrics to JSON file."""
        data = {
            'experiment_name': self.experiment_name,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'epoch_metrics': [m.to_dict() for m in self.epoch_metrics],
            'batch_metrics': [asdict(m) for m in self.batch_metrics[-1000:]],  # Last 1000 batches
            'summary': self.get_summary()
        }

        output_path = self.save_dir / f"{self.experiment_name}_metrics.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"[SAVE] Metrics saved to {output_path}")

    def plot_metrics(self, save_path: Optional[str] = None):
        """Generate and save training plots."""
        if not self.epoch_metrics:
            logger.warning("[PLOT] No metrics to plot")
            return

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        epochs = [m.epoch for m in self.epoch_metrics]
        train_losses = [m.train_loss for m in self.epoch_metrics]
        val_losses = [m.val_loss for m in self.epoch_metrics if m.val_loss is not None]
        learning_rates = [m.learning_rate for m in self.epoch_metrics]

        # Plot 1: Loss curves
        axes[0, 0].plot(epochs, train_losses, label='Train Loss', marker='o')
        if val_losses:
            val_epochs = [m.epoch for m in self.epoch_metrics if m.val_loss is not None]
            axes[0, 0].plot(val_epochs, val_losses, label='Val Loss', marker='s')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].set_title('Training and Validation Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Plot 2: Learning rate
        axes[0, 1].plot(epochs, learning_rates, color='green', marker='o')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Learning Rate')
        axes[0, 1].set_title('Learning Rate Schedule')
        axes[0, 1].set_yscale('log')
        axes[0, 1].grid(True, alpha=0.3)

        # Plot 3: Samples per second
        samples_per_sec = [m.samples_per_second for m in self.epoch_metrics]
        axes[1, 0].plot(epochs, samples_per_sec, color='orange', marker='o')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Samples/Second')
        axes[1, 0].set_title('Training Throughput')
        axes[1, 0].grid(True, alpha=0.3)

        # Plot 4: Memory usage
        memory_usage = [m.peak_memory_mb for m in self.epoch_metrics]
        axes[1, 1].plot(epochs, memory_usage, color='red', marker='o')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Memory (MB)')
        axes[1, 1].set_title('Peak Memory Usage')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        # Save
        if save_path is None:
            save_path = self.save_dir / f"{self.experiment_name}_plots.png"

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"[PLOT] Metrics plots saved to {save_path}")

    def print_summary(self):
        """Print formatted summary."""
        summary = self.get_summary()

        print("\n" + "="*70)
        print("[*] TRAINING METRICS SUMMARY")
        print("="*70)

        print(f"\nExperiment: {summary['experiment_name']}")
        print(f"Total Epochs: {summary['total_epochs']}")
        print(f"Total Batches: {summary['total_batches']}")
        print(f"Total Time: {summary['total_time_hours']:.2f} hours")

        print(f"\nBest Metrics:")
        print(f"  Train Loss: {summary['best_train_loss']:.4f} (epoch {summary['best_epoch']})")
        if summary.get('best_val_loss'):
            print(f"  Val Loss: {summary['best_val_loss']:.4f}")

        if 'latest_train_loss' in summary:
            print(f"\nLatest Metrics:")
            print(f"  Train Loss: {summary['latest_train_loss']:.4f}")
            if summary.get('latest_val_loss'):
                print(f"  Val Loss: {summary['latest_val_loss']:.4f}")
            print(f"  Learning Rate: {summary['latest_learning_rate']:.2e}")

        if 'avg_samples_per_second' in summary:
            print(f"\nPerformance:")
            print(f"  Avg Samples/Sec: {summary['avg_samples_per_second']:.2f}")
            print(f"  Avg Epoch Time: {summary.get('avg_epoch_time', 0):.2f}s")
            print(f"  Peak Memory: {summary.get('peak_memory_mb', 0):.2f} MB")

        print("\n" + "="*70 + "\n")


__all__ = ['TrainingMetricsTracker', 'EpochMetrics', 'BatchMetrics']
