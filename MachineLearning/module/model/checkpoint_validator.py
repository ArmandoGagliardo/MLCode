"""
Checkpoint Validation and Management

Validate and manage training checkpoints:
- Checkpoint integrity checks
- Metadata validation
- Automatic cleanup of old checkpoints
- Best checkpoint selection
- Checkpoint recovery
"""

import json
import torch
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CheckpointInfo:
    """Information about a training checkpoint."""

    path: Path
    epoch: int
    step: int
    train_loss: float
    val_loss: Optional[float] = None
    timestamp: str = ""
    file_size_mb: float = 0.0
    valid: bool = True
    error: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)


class CheckpointValidator:
    """Validator for training checkpoints."""

    def __init__(self, checkpoint_dir: str):
        """
        Initialize checkpoint validator.

        Args:
            checkpoint_dir: Directory containing checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoints: List[CheckpointInfo] = []

    def scan_checkpoints(self) -> List[CheckpointInfo]:
        """
        Scan directory for checkpoints.

        Returns:
            List of CheckpointInfo objects
        """
        if not self.checkpoint_dir.exists():
            logger.warning(f"[SCAN] Checkpoint directory does not exist: {self.checkpoint_dir}")
            return []

        checkpoint_files = list(self.checkpoint_dir.glob("checkpoint-*.pt")) + \
                          list(self.checkpoint_dir.glob("checkpoint-*.pth")) + \
                          list(self.checkpoint_dir.glob("epoch_*.pt"))

        logger.info(f"[SCAN] Found {len(checkpoint_files)} checkpoint files")

        checkpoints = []
        for ckpt_path in checkpoint_files:
            info = self.validate_checkpoint(ckpt_path)
            checkpoints.append(info)

        self.checkpoints = sorted(checkpoints, key=lambda x: x.epoch)

        return self.checkpoints

    def validate_checkpoint(self, checkpoint_path: Path) -> CheckpointInfo:
        """
        Validate a single checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            CheckpointInfo object
        """
        logger.debug(f"[VALIDATE] Checking {checkpoint_path.name}")

        # Get file size
        file_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)

        try:
            # Load checkpoint
            checkpoint = torch.load(checkpoint_path, map_location='cpu')

            # Extract metadata
            epoch = checkpoint.get('epoch', -1)
            step = checkpoint.get('step', checkpoint.get('global_step', -1))
            train_loss = checkpoint.get('train_loss', checkpoint.get('loss', float('inf')))
            val_loss = checkpoint.get('val_loss', checkpoint.get('eval_loss', None))
            timestamp = checkpoint.get('timestamp', '')

            # Validate required fields
            required_keys = ['model_state_dict']
            missing_keys = [key for key in required_keys if key not in checkpoint]

            if missing_keys:
                error_msg = f"Missing keys: {', '.join(missing_keys)}"
                logger.warning(f"[INVALID] {checkpoint_path.name}: {error_msg}")
                return CheckpointInfo(
                    path=checkpoint_path,
                    epoch=epoch,
                    step=step,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    timestamp=timestamp,
                    file_size_mb=file_size_mb,
                    valid=False,
                    error=error_msg
                )

            # Valid checkpoint
            logger.debug(f"[OK] {checkpoint_path.name}: epoch {epoch}, loss {train_loss:.4f}")

            return CheckpointInfo(
                path=checkpoint_path,
                epoch=epoch,
                step=step,
                train_loss=train_loss,
                val_loss=val_loss,
                timestamp=timestamp,
                file_size_mb=file_size_mb,
                valid=True
            )

        except Exception as e:
            error_msg = f"Failed to load: {str(e)}"
            logger.error(f"[ERROR] {checkpoint_path.name}: {error_msg}")

            return CheckpointInfo(
                path=checkpoint_path,
                epoch=-1,
                step=-1,
                train_loss=float('inf'),
                file_size_mb=file_size_mb,
                valid=False,
                error=error_msg
            )

    def get_best_checkpoint(self, metric: str = 'val_loss') -> Optional[CheckpointInfo]:
        """
        Get the best checkpoint based on a metric.

        Args:
            metric: Metric to use ('val_loss' or 'train_loss')

        Returns:
            CheckpointInfo for best checkpoint or None
        """
        valid_checkpoints = [ckpt for ckpt in self.checkpoints if ckpt.valid]

        if not valid_checkpoints:
            logger.warning("[BEST] No valid checkpoints found")
            return None

        # Filter checkpoints with the metric
        if metric == 'val_loss':
            candidates = [ckpt for ckpt in valid_checkpoints if ckpt.val_loss is not None]
            if not candidates:
                logger.warning("[BEST] No checkpoints with validation loss, using train_loss")
                metric = 'train_loss'
                candidates = valid_checkpoints
        else:
            candidates = valid_checkpoints

        # Find best
        best = min(candidates, key=lambda x: x.val_loss if metric == 'val_loss' else x.train_loss)

        logger.info(f"[BEST] Best checkpoint (by {metric}): {best.path.name}")
        logger.info(f"       Epoch: {best.epoch}, Loss: {best.val_loss if metric == 'val_loss' else best.train_loss:.4f}")

        return best

    def get_latest_checkpoint(self) -> Optional[CheckpointInfo]:
        """
        Get the most recent checkpoint.

        Returns:
            CheckpointInfo for latest checkpoint or None
        """
        valid_checkpoints = [ckpt for ckpt in self.checkpoints if ckpt.valid]

        if not valid_checkpoints:
            return None

        latest = max(valid_checkpoints, key=lambda x: x.epoch)

        logger.info(f"[LATEST] Latest checkpoint: {latest.path.name} (epoch {latest.epoch})")

        return latest

    def cleanup_old_checkpoints(
        self,
        keep_best: int = 3,
        keep_latest: int = 2,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Remove old checkpoints, keeping only the best and most recent.

        Args:
            keep_best: Number of best checkpoints to keep
            keep_latest: Number of latest checkpoints to keep
            dry_run: If True, don't actually delete files

        Returns:
            List of deleted checkpoint paths
        """
        logger.info(f"[CLEANUP] Cleaning up checkpoints (keep_best={keep_best}, keep_latest={keep_latest})")

        valid_checkpoints = [ckpt for ckpt in self.checkpoints if ckpt.valid]

        if not valid_checkpoints:
            logger.info("[CLEANUP] No valid checkpoints to clean")
            return []

        # Identify checkpoints to keep
        keep_paths = set()

        # Keep best by validation loss
        best_by_val = sorted(
            [c for c in valid_checkpoints if c.val_loss is not None],
            key=lambda x: x.val_loss
        )[:keep_best]
        keep_paths.update(c.path for c in best_by_val)

        # Keep best by train loss
        best_by_train = sorted(valid_checkpoints, key=lambda x: x.train_loss)[:keep_best]
        keep_paths.update(c.path for c in best_by_train)

        # Keep latest
        latest = sorted(valid_checkpoints, key=lambda x: x.epoch)[-keep_latest:]
        keep_paths.update(c.path for c in latest)

        # Identify checkpoints to delete
        delete_paths = [c.path for c in valid_checkpoints if c.path not in keep_paths]

        if not delete_paths:
            logger.info("[CLEANUP] No checkpoints to delete")
            return []

        logger.info(f"[CLEANUP] Will delete {len(delete_paths)} checkpoints")
        for path in delete_paths:
            logger.info(f"           - {path.name}")

        if dry_run:
            logger.info("[CLEANUP] Dry run - no files deleted")
            return delete_paths

        # Delete files
        deleted = []
        for path in delete_paths:
            try:
                path.unlink()
                deleted.append(path)
                logger.debug(f"[DELETE] {path.name}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to delete {path.name}: {e}")

        logger.info(f"[CLEANUP] Deleted {len(deleted)} checkpoints")

        # Update checkpoint list
        self.checkpoints = [c for c in self.checkpoints if c.path not in deleted]

        return deleted

    def export_best_model(
        self,
        output_dir: str,
        metric: str = 'val_loss',
        copy_config: bool = True
    ) -> Optional[Path]:
        """
        Export the best checkpoint as a standalone model.

        Args:
            output_dir: Directory to export model to
            metric: Metric to use for selecting best checkpoint
            copy_config: Also copy config files if available

        Returns:
            Path to exported model or None
        """
        best = self.get_best_checkpoint(metric)

        if not best:
            logger.error("[EXPORT] No valid checkpoint found")
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Copy checkpoint
        dest_path = output_path / "pytorch_model.bin"

        try:
            logger.info(f"[EXPORT] Exporting {best.path.name} to {dest_path}")
            shutil.copy2(best.path, dest_path)

            # Copy config files if requested
            if copy_config:
                config_files = ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'vocab.json']

                for config_file in config_files:
                    source = self.checkpoint_dir / config_file
                    if source.exists():
                        dest = output_path / config_file
                        shutil.copy2(source, dest)
                        logger.debug(f"[COPY] {config_file}")

            # Create metadata file
            metadata = {
                'source_checkpoint': str(best.path),
                'epoch': best.epoch,
                'step': best.step,
                'train_loss': best.train_loss,
                'val_loss': best.val_loss,
                'export_timestamp': datetime.now().isoformat(),
                'metric_used': metric
            }

            metadata_path = output_path / "export_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"[EXPORT] Model exported successfully to {output_path}")

            return dest_path

        except Exception as e:
            logger.error(f"[ERROR] Export failed: {e}")
            return None

    def print_summary(self):
        """Print checkpoint summary."""
        print("\n" + "="*70)
        print("[*] CHECKPOINT SUMMARY")
        print("="*70)

        print(f"\nDirectory: {self.checkpoint_dir}")
        print(f"Total Checkpoints: {len(self.checkpoints)}")

        valid_count = sum(1 for c in self.checkpoints if c.valid)
        invalid_count = len(self.checkpoints) - valid_count

        print(f"Valid: {valid_count}")
        print(f"Invalid: {invalid_count}")

        if valid_count > 0:
            total_size = sum(c.file_size_mb for c in self.checkpoints if c.valid)
            print(f"Total Size: {total_size:.2f} MB")

            print(f"\nCheckpoints:")
            for ckpt in self.checkpoints:
                if ckpt.valid:
                    val_loss_str = f"{ckpt.val_loss:.4f}" if ckpt.val_loss else "N/A"
                    print(f"  [OK] Epoch {ckpt.epoch:3d} | "
                          f"Train: {ckpt.train_loss:.4f} | "
                          f"Val: {val_loss_str} | "
                          f"{ckpt.file_size_mb:.1f} MB | "
                          f"{ckpt.path.name}")
                else:
                    print(f"  [FAIL] {ckpt.path.name} - {ckpt.error}")

            # Show best checkpoint
            best = self.get_best_checkpoint()
            if best:
                print(f"\nBest Checkpoint: {best.path.name}")
                print(f"  Epoch: {best.epoch}")
                print(f"  Val Loss: {best.val_loss if best.val_loss else 'N/A'}")

        print("\n" + "="*70 + "\n")


__all__ = ['CheckpointValidator', 'CheckpointInfo']
