"""
Training Metrics Tracker
=========================

Real-time metrics tracking and visualization during ML training.

This component provides:
- Real-time metric collection (loss, accuracy, learning rate, etc.)
- Metric history storage
- Statistics calculation (mean, std, min, max)
- Progress tracking
- Export to JSON/CSV for analysis

Example:
    >>> from infrastructure.training import TrainingMetricsTracker
    >>>
    >>> # Create tracker
    >>> tracker = TrainingMetricsTracker(
    ...     output_dir='models/logs',
    ...     experiment_name='codebert_classification'
    ... )
    >>>
    >>> # Log metrics during training
    >>> for epoch in range(num_epochs):
    ...     for batch_idx, batch in enumerate(train_loader):
    ...         loss = train_step(batch)
    ...         tracker.log_metric('train_loss', loss, step=global_step)
    ...
    ...     # Log epoch metrics
    ...     eval_loss = evaluate()
    ...     tracker.log_epoch_metric('eval_loss', eval_loss, epoch=epoch)
    >>>
    >>> # Get summary
    >>> summary = tracker.get_summary()
    >>> print(f"Best eval loss: {summary['best_eval_loss']}")
    >>>
    >>> # Export
    >>> tracker.export_to_json('metrics.json')
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import statistics

from domain.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class MetricEntry:
    """
    Single metric entry.

    Attributes:
        name: Metric name
        value: Metric value
        step: Global step
        epoch: Epoch number
        timestamp: Unix timestamp
    """
    name: str
    value: float
    step: int
    epoch: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MetricStatistics:
    """
    Statistics for a metric.

    Attributes:
        name: Metric name
        count: Number of values
        mean: Mean value
        std: Standard deviation
        min: Minimum value
        max: Maximum value
        last: Last recorded value
    """
    name: str
    count: int
    mean: float
    std: float
    min: float
    max: float
    last: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TrainingMetricsTracker:
    """
    Training metrics tracker for real-time monitoring.

    Features:
    - Real-time metric logging
    - History storage
    - Statistics calculation
    - Best metric tracking
    - Export to JSON/CSV

    Attributes:
        output_dir: Directory for saving logs
        experiment_name: Name of experiment
        metrics: Dictionary of metric histories
        epoch_metrics: Metrics aggregated by epoch
        best_metrics: Best values for each metric

    Example:
        >>> tracker = TrainingMetricsTracker(output_dir='logs', experiment_name='exp1')
        >>> tracker.log_metric('train_loss', 0.5, step=100)
        >>> tracker.log_epoch_metric('eval_accuracy', 0.85, epoch=0)
        >>> summary = tracker.get_summary()
    """

    def __init__(
        self,
        output_dir: str = 'models/logs',
        experiment_name: str = 'experiment',
        auto_save: bool = True,
        save_interval: int = 100
    ):
        """
        Initialize TrainingMetricsTracker.

        Args:
            output_dir: Directory for saving logs
            experiment_name: Name of experiment (used in filenames)
            auto_save: Whether to auto-save periodically
            save_interval: Save every N metric logs

        Raises:
            ConfigurationError: If output_dir cannot be created
        """
        self.output_dir = Path(output_dir)
        self.experiment_name = experiment_name
        self.auto_save = auto_save
        self.save_interval = save_interval

        # Create output directory
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create output directory: {e}")

        # Metric storage
        self.metrics: Dict[str, List[MetricEntry]] = defaultdict(list)
        self.epoch_metrics: Dict[int, Dict[str, float]] = defaultdict(dict)
        self.best_metrics: Dict[str, Dict[str, Any]] = {}

        # State
        self.start_time = time.time()
        self.log_count = 0
        self.current_epoch = 0

        logger.info(
            f"TrainingMetricsTracker initialized: output_dir={self.output_dir}, "
            f"experiment={self.experiment_name}"
        )

    def log_metric(
        self,
        name: str,
        value: Union[float, int],
        step: int,
        epoch: Optional[int] = None
    ) -> None:
        """
        Log a metric value.

        Args:
            name: Metric name (e.g., 'train_loss', 'eval_accuracy')
            value: Metric value
            step: Global step
            epoch: Optional epoch number

        Example:
            >>> tracker.log_metric('train_loss', 0.45, step=100, epoch=0)
            >>> tracker.log_metric('learning_rate', 2e-5, step=100)
        """
        entry = MetricEntry(
            name=name,
            value=float(value),
            step=step,
            epoch=epoch or self.current_epoch
        )

        self.metrics[name].append(entry)
        self.log_count += 1

        # Update best metric
        self._update_best_metric(name, float(value), step)

        # Auto-save
        if self.auto_save and self.log_count % self.save_interval == 0:
            self.save()

    def log_epoch_metric(
        self,
        name: str,
        value: Union[float, int],
        epoch: int
    ) -> None:
        """
        Log a metric for an entire epoch.

        Args:
            name: Metric name (e.g., 'eval_loss', 'eval_accuracy')
            value: Metric value
            epoch: Epoch number

        Example:
            >>> tracker.log_epoch_metric('eval_loss', 0.35, epoch=0)
            >>> tracker.log_epoch_metric('eval_accuracy', 0.92, epoch=0)
        """
        self.epoch_metrics[epoch][name] = float(value)
        self.current_epoch = epoch

        # Also log as regular metric
        self.log_metric(name, value, step=epoch, epoch=epoch)

    def log_metrics_batch(
        self,
        metrics: Dict[str, Union[float, int]],
        step: int,
        epoch: Optional[int] = None
    ) -> None:
        """
        Log multiple metrics at once.

        Args:
            metrics: Dictionary of metric name to value
            step: Global step
            epoch: Optional epoch number

        Example:
            >>> tracker.log_metrics_batch({
            ...     'train_loss': 0.45,
            ...     'train_accuracy': 0.88,
            ...     'learning_rate': 2e-5
            ... }, step=100, epoch=0)
        """
        for name, value in metrics.items():
            self.log_metric(name, value, step, epoch)

    def _update_best_metric(self, name: str, value: float, step: int) -> None:
        """
        Update best metric value.

        Args:
            name: Metric name
            value: Metric value
            step: Global step
        """
        # Determine if lower or higher is better
        # Convention: metrics with 'loss' or 'error' in name -> lower is better
        is_loss = 'loss' in name.lower() or 'error' in name.lower()

        if name not in self.best_metrics:
            self.best_metrics[name] = {
                'value': value,
                'step': step,
                'is_loss': is_loss
            }
        else:
            current_best = self.best_metrics[name]['value']
            if (is_loss and value < current_best) or (not is_loss and value > current_best):
                self.best_metrics[name] = {
                    'value': value,
                    'step': step,
                    'is_loss': is_loss
                }

    def get_metric_history(self, name: str) -> List[MetricEntry]:
        """
        Get history for a specific metric.

        Args:
            name: Metric name

        Returns:
            List of metric entries

        Example:
            >>> history = tracker.get_metric_history('train_loss')
            >>> for entry in history:
            ...     print(f"Step {entry.step}: {entry.value}")
        """
        return self.metrics.get(name, [])

    def get_metric_statistics(self, name: str) -> Optional[MetricStatistics]:
        """
        Get statistics for a specific metric.

        Args:
            name: Metric name

        Returns:
            MetricStatistics or None if metric not found

        Example:
            >>> stats = tracker.get_metric_statistics('train_loss')
            >>> print(f"Mean: {stats.mean:.4f}, Std: {stats.std:.4f}")
        """
        history = self.get_metric_history(name)
        if not history:
            return None

        values = [entry.value for entry in history]

        return MetricStatistics(
            name=name,
            count=len(values),
            mean=statistics.mean(values),
            std=statistics.stdev(values) if len(values) > 1 else 0.0,
            min=min(values),
            max=max(values),
            last=values[-1]
        )

    def get_all_statistics(self) -> Dict[str, MetricStatistics]:
        """
        Get statistics for all metrics.

        Returns:
            Dictionary of metric name to statistics

        Example:
            >>> all_stats = tracker.get_all_statistics()
            >>> for name, stats in all_stats.items():
            ...     print(f"{name}: mean={stats.mean:.4f}")
        """
        return {
            name: self.get_metric_statistics(name)
            for name in self.metrics.keys()
        }

    def get_best_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get best values for all metrics.

        Returns:
            Dictionary of metric name to best value info

        Example:
            >>> best = tracker.get_best_metrics()
            >>> print(f"Best eval loss: {best['eval_loss']['value']:.4f}")
        """
        return self.best_metrics.copy()

    def get_epoch_metrics(self, epoch: int) -> Dict[str, float]:
        """
        Get all metrics for a specific epoch.

        Args:
            epoch: Epoch number

        Returns:
            Dictionary of metric name to value

        Example:
            >>> epoch_0_metrics = tracker.get_epoch_metrics(0)
            >>> print(f"Eval loss: {epoch_0_metrics.get('eval_loss')}")
        """
        return self.epoch_metrics.get(epoch, {})

    def get_summary(self) -> Dict[str, Any]:
        """
        Get training summary with key metrics.

        Returns:
            Summary dictionary

        Example:
            >>> summary = tracker.get_summary()
            >>> print(json.dumps(summary, indent=2))
        """
        elapsed_time = time.time() - self.start_time

        summary = {
            'experiment_name': self.experiment_name,
            'start_time': self.start_time,
            'elapsed_time': elapsed_time,
            'total_logs': self.log_count,
            'current_epoch': self.current_epoch,
            'num_metrics': len(self.metrics),
            'metric_names': list(self.metrics.keys()),
            'best_metrics': self.best_metrics,
            'statistics': {
                name: stats.to_dict()
                for name, stats in self.get_all_statistics().items()
            }
        }

        return summary

    def save(self, filename: Optional[str] = None) -> None:
        """
        Save metrics to JSON file.

        Args:
            filename: Optional custom filename (default: <experiment_name>_metrics.json)

        Example:
            >>> tracker.save()  # Uses default filename
            >>> tracker.save('custom_metrics.json')
        """
        if filename is None:
            filename = f"{self.experiment_name}_metrics.json"

        filepath = self.output_dir / filename

        # Prepare data
        data = {
            'experiment_name': self.experiment_name,
            'start_time': self.start_time,
            'metrics': {
                name: [entry.to_dict() for entry in entries]
                for name, entries in self.metrics.items()
            },
            'epoch_metrics': {
                str(epoch): metrics
                for epoch, metrics in self.epoch_metrics.items()
            },
            'best_metrics': self.best_metrics,
            'summary': self.get_summary()
        }

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved metrics to {filepath}")

    def export_to_json(self, filename: str) -> None:
        """
        Export metrics to JSON file (alias for save).

        Args:
            filename: Output filename

        Example:
            >>> tracker.export_to_json('experiment_results.json')
        """
        self.save(filename)

    def export_to_csv(self, filename: str) -> None:
        """
        Export metrics to CSV file.

        Args:
            filename: Output filename

        Example:
            >>> tracker.export_to_csv('metrics.csv')
        """
        import csv

        filepath = self.output_dir / filename

        # Collect all entries
        all_entries = []
        for name, entries in self.metrics.items():
            for entry in entries:
                all_entries.append({
                    'metric_name': entry.name,
                    'value': entry.value,
                    'step': entry.step,
                    'epoch': entry.epoch,
                    'timestamp': entry.timestamp
                })

        # Sort by step
        all_entries.sort(key=lambda x: x['step'])

        # Write CSV
        if all_entries:
            fieldnames = ['metric_name', 'value', 'step', 'epoch', 'timestamp']
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_entries)

            logger.info(f"Exported metrics to {filepath}")

    def clear(self) -> None:
        """
        Clear all metrics.

        Example:
            >>> tracker.clear()  # Start fresh
        """
        self.metrics.clear()
        self.epoch_metrics.clear()
        self.best_metrics.clear()
        self.log_count = 0
        self.start_time = time.time()

        logger.info("Cleared all metrics")

    def __str__(self) -> str:
        """String representation."""
        return (
            f"TrainingMetricsTracker(experiment={self.experiment_name}, "
            f"metrics={len(self.metrics)}, logs={self.log_count})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"TrainingMetricsTracker(experiment_name='{self.experiment_name}', "
            f"output_dir='{self.output_dir}', metrics={list(self.metrics.keys())})"
        )
