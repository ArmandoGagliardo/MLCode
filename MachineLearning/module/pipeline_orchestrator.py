"""
Pipeline Orchestrator

Automatic orchestration of all improvements:
- Enhanced parser with metrics
- Training metrics tracking
- Model validation
- Checkpoint management
- Automatic reporting

This module is automatically called by main.py
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates all pipeline improvements automatically."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enable_enhanced_parser = self.config.get('use_enhanced_parser', True)
        self.enable_training_metrics = self.config.get('track_training_metrics', True)
        self.enable_validation = self.config.get('auto_validate_model', True)
        self.enable_checkpoint_management = self.config.get('manage_checkpoints', True)

        logger.info("[ORCHESTRATOR] Initialized")
        logger.info(f"  Enhanced Parser: {self.enable_enhanced_parser}")
        logger.info(f"  Training Metrics: {self.enable_training_metrics}")
        logger.info(f"  Auto Validation: {self.enable_validation}")
        logger.info(f"  Checkpoint Management: {self.enable_checkpoint_management}")

    def get_parser(self):
        """
        Get appropriate parser instance.

        Returns:
            Parser instance (enhanced or standard)
        """
        if self.enable_enhanced_parser:
            try:
                from module.preprocessing.universal_parser_enhanced import UniversalParserEnhanced
                parser = UniversalParserEnhanced(
                    enable_metrics=True,
                    enable_caching=True
                )
                logger.info("[PARSER] Using enhanced parser with metrics and caching")
                return parser
            except Exception as e:
                logger.warning(f"[PARSER] Failed to load enhanced parser: {e}")
                logger.info("[PARSER] Falling back to standard parser")

        # Fallback to standard parser
        from module.preprocessing.universal_parser_new import UniversalParser
        parser = UniversalParser()
        logger.info("[PARSER] Using standard parser")
        return parser

    def get_training_tracker(self, save_dir: str, experiment_name: str = "training"):
        """
        Get training metrics tracker if enabled.

        Args:
            save_dir: Directory to save metrics
            experiment_name: Experiment name

        Returns:
            TrainingMetricsTracker instance or None
        """
        if not self.enable_training_metrics:
            return None

        try:
            from module.model.training_metrics import TrainingMetricsTracker
            tracker = TrainingMetricsTracker(save_dir, experiment_name)
            logger.info(f"[METRICS] Training metrics tracker enabled: {save_dir}")
            return tracker
        except Exception as e:
            logger.warning(f"[METRICS] Failed to initialize tracker: {e}")
            return None

    def validate_model_after_training(
        self,
        model_path: str,
        quick: bool = False,
        save_report: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically validate model after training.

        Args:
            model_path: Path to trained model
            quick: Quick validation (skip benchmarks)
            save_report: Save validation report

        Returns:
            Validation summary or None
        """
        if not self.enable_validation:
            logger.info("[VALIDATION] Auto-validation disabled")
            return None

        try:
            from module.model.model_validator import ModelValidator

            logger.info(f"[VALIDATION] Starting auto-validation: {model_path}")

            validator = ModelValidator(model_path)
            result = validator.validate_all(quick=quick)

            # Print summary
            validator.print_summary()

            # Save report
            if save_report:
                report_dir = Path(model_path).parent / "validation_reports"
                report_dir.mkdir(parents=True, exist_ok=True)

                model_name = Path(model_path).name
                report_path = report_dir / f"validation_{model_name}.json"
                result.save(str(report_path))

                logger.info(f"[VALIDATION] Report saved: {report_path}")

            return result.to_dict()

        except Exception as e:
            logger.error(f"[VALIDATION] Auto-validation failed: {e}")
            return None

    def manage_checkpoints_after_training(
        self,
        checkpoint_dir: str,
        keep_best: int = 3,
        keep_latest: int = 2,
        export_best: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically manage checkpoints after training.

        Args:
            checkpoint_dir: Directory containing checkpoints
            keep_best: Number of best checkpoints to keep
            keep_latest: Number of latest checkpoints to keep
            export_best: Export best checkpoint as standalone model

        Returns:
            Management summary or None
        """
        if not self.enable_checkpoint_management:
            logger.info("[CHECKPOINTS] Auto-management disabled")
            return None

        try:
            from module.model.checkpoint_validator import CheckpointValidator

            logger.info(f"[CHECKPOINTS] Managing checkpoints: {checkpoint_dir}")

            validator = CheckpointValidator(checkpoint_dir)
            checkpoints = validator.scan_checkpoints()

            if not checkpoints:
                logger.warning("[CHECKPOINTS] No checkpoints found")
                return None

            # Print summary
            validator.print_summary()

            # Cleanup old checkpoints
            deleted = validator.cleanup_old_checkpoints(
                keep_best=keep_best,
                keep_latest=keep_latest,
                dry_run=False
            )

            logger.info(f"[CHECKPOINTS] Cleaned up {len(deleted)} old checkpoints")

            # Export best model
            best_path = None
            if export_best:
                export_dir = Path(checkpoint_dir).parent / "best_model"
                best_path = validator.export_best_model(str(export_dir))

                if best_path:
                    logger.info(f"[CHECKPOINTS] Best model exported: {export_dir}")

            return {
                'total_checkpoints': len(checkpoints),
                'deleted_count': len(deleted),
                'best_model_path': str(best_path) if best_path else None
            }

        except Exception as e:
            logger.error(f"[CHECKPOINTS] Auto-management failed: {e}")
            return None

    def finalize_training(
        self,
        model_path: str,
        checkpoint_dir: Optional[str] = None,
        metrics_tracker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive finalization after training.

        Args:
            model_path: Path to trained model
            checkpoint_dir: Directory with checkpoints (optional)
            metrics_tracker: TrainingMetricsTracker instance (optional)

        Returns:
            Finalization summary
        """
        logger.info("[FINALIZE] Starting training finalization...")

        summary = {
            'model_path': model_path,
            'validation': None,
            'checkpoints': None,
            'metrics': None,
            'success': True
        }

        # Save and plot metrics
        if metrics_tracker:
            try:
                metrics_tracker.save()
                metrics_tracker.plot_metrics()
                metrics_tracker.print_summary()
                summary['metrics'] = metrics_tracker.get_summary()
                logger.info("[FINALIZE] Training metrics saved and plotted")
            except Exception as e:
                logger.error(f"[FINALIZE] Failed to save metrics: {e}")
                summary['success'] = False

        # Validate model
        validation_result = self.validate_model_after_training(
            model_path=model_path,
            quick=False,
            save_report=True
        )

        if validation_result:
            summary['validation'] = validation_result
        else:
            logger.warning("[FINALIZE] Model validation skipped or failed")

        # Manage checkpoints
        if checkpoint_dir:
            checkpoint_result = self.manage_checkpoints_after_training(
                checkpoint_dir=checkpoint_dir,
                keep_best=3,
                keep_latest=2,
                export_best=True
            )

            if checkpoint_result:
                summary['checkpoints'] = checkpoint_result
            else:
                logger.warning("[FINALIZE] Checkpoint management skipped or failed")

        # Save finalization summary
        summary_path = Path(model_path).parent / "training_summary.json"
        try:
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"[FINALIZE] Summary saved: {summary_path}")
        except Exception as e:
            logger.error(f"[FINALIZE] Failed to save summary: {e}")

        logger.info("[FINALIZE] Training finalization complete")

        return summary

    def print_parser_metrics(self, parser):
        """
        Print parser metrics if available.

        Args:
            parser: Parser instance
        """
        if hasattr(parser, 'print_metrics'):
            try:
                parser.print_metrics()
            except Exception as e:
                logger.error(f"[PARSER] Failed to print metrics: {e}")


# Singleton instance
_orchestrator = None


def get_orchestrator(config: Optional[Dict[str, Any]] = None):
    """
    Get singleton orchestrator instance.

    Args:
        config: Configuration dictionary

    Returns:
        PipelineOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator(config)

    return _orchestrator


__all__ = ['PipelineOrchestrator', 'get_orchestrator']
