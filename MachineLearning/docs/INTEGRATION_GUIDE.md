# Integration Guide: Pipeline Improvements

This guide shows how to integrate all new improvements into your existing workflows.

## Overview

All improvements are automatically orchestrated through the `PipelineOrchestrator` class. You don't need to manage individual components - just use the orchestrator.

## Quick Start

### 1. Data Extraction with Enhanced Parser

```python
from module.pipeline_orchestrator import get_orchestrator

# Get orchestrator
orchestrator = get_orchestrator()

# Get enhanced parser (automatic caching + metrics)
parser = orchestrator.get_parser()

# Use parser as normal
code = """
def calculate_sum(numbers):
    return sum(numbers)
"""

results = parser.parse(code, "python")

# Print metrics automatically
orchestrator.print_parser_metrics(parser)
```

**Output:**
```
[*] PARSER PERFORMANCE METRICS
Total Parses: 1
Successful: 1 (100.00%)
Functions Extracted: 1
Avg Time: 15.23ms
```

### 2. Training with Automatic Metrics Tracking

```python
from module.pipeline_orchestrator import get_orchestrator

# Get orchestrator
orchestrator = get_orchestrator()

# Get training metrics tracker
tracker = orchestrator.get_training_tracker(
    save_dir="models/my_model",
    experiment_name="code_gen_v1"
)

# During training loop
for epoch in range(num_epochs):
    # ... training code ...

    # Record epoch metrics (automatic saving)
    tracker.record_epoch(
        epoch=epoch,
        train_loss=avg_train_loss,
        val_loss=avg_val_loss,
        learning_rate=current_lr,
        epoch_time=epoch_duration,
        num_samples=len(train_dataset),
        gradient_norm=grad_norm
    )

    # Check if should stop early
    if tracker.should_stop_early(patience=5):
        print("[INFO] Early stopping triggered")
        break

# After training - finalize everything automatically
summary = orchestrator.finalize_training(
    model_path="models/my_model",
    checkpoint_dir="models/my_model/checkpoints",
    metrics_tracker=tracker
)
```

**What happens automatically:**
1. ✅ Metrics saved to JSON
2. ✅ Training plots generated
3. ✅ Model validated (architecture, inference, benchmarks)
4. ✅ Checkpoints cleaned up (keeps best 3 + latest 2)
5. ✅ Best model exported
6. ✅ Summary report saved

### 3. Integration in main.py

Add this to your main.py training function:

```python
def train_model(args):
    """Train model with automatic orchestration."""
    from module.pipeline_orchestrator import get_orchestrator

    # Initialize orchestrator
    config = {
        'use_enhanced_parser': True,
        'track_training_metrics': True,
        'auto_validate_model': True,
        'manage_checkpoints': True
    }
    orchestrator = get_orchestrator(config)

    # Get training tracker
    tracker = orchestrator.get_training_tracker(
        save_dir=f"models/{args.task}",
        experiment_name=args.experiment_name
    )

    # ... your existing training code ...

    # Record metrics during training
    if tracker:
        tracker.record_epoch(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            learning_rate=lr,
            epoch_time=epoch_time,
            num_samples=num_samples
        )

    # Finalize after training
    summary = orchestrator.finalize_training(
        model_path=f"models/{args.task}",
        checkpoint_dir=f"models/{args.task}/checkpoints",
        metrics_tracker=tracker
    )

    print(f"\n[SUCCESS] Training complete")
    print(f"Model: {summary['model_path']}")
    if summary['validation']:
        print(f"Validation: {'PASSED' if summary['validation']['passed'] else 'FAILED'}")
    if summary['checkpoints']:
        print(f"Checkpoints cleaned: {summary['checkpoints']['deleted_count']}")
```

### 4. Data Collection with Enhanced Parser

Update your data collection code:

```python
def collect_data(args):
    """Collect data with enhanced parser."""
    from module.pipeline_orchestrator import get_orchestrator

    # Get orchestrator and parser
    orchestrator = get_orchestrator()
    parser = orchestrator.get_parser()

    # ... your existing collection code ...

    # Use parser (metrics tracked automatically)
    for file_path in code_files:
        code = read_file(file_path)
        results = parser.parse(code, language)

        # Process results...

    # Print parser performance at the end
    print("\n[*] Parser Performance:")
    orchestrator.print_parser_metrics(parser)
```

**Output:**
```
[*] Parser Performance:
Total Parses: 1,234
Successful: 1,198 (97.08%)
Failed: 36
Functions Extracted: 5,432
Avg Time: 23.45ms

Per-Language Statistics:
  Python: 456 parses (98.5% success), 2,145 functions
  JavaScript: 342 parses (95.2% success), 1,876 functions
  ...
```

## Configuration Options

You can configure the orchestrator behavior:

```python
config = {
    # Parser settings
    'use_enhanced_parser': True,  # Use enhanced parser with metrics

    # Training settings
    'track_training_metrics': True,  # Track detailed metrics
    'auto_validate_model': True,  # Validate after training
    'manage_checkpoints': True,  # Auto-cleanup checkpoints
}

orchestrator = get_orchestrator(config)
```

## Manual Operations

If you need manual control:

### Validate Model Manually

```bash
python evaluate_model.py --model models/my_model/
python evaluate_model.py --model models/my_model/ --quick
```

### Manage Checkpoints Manually

```python
from module.model.checkpoint_validator import CheckpointValidator

validator = CheckpointValidator("models/my_model/checkpoints")
checkpoints = validator.scan_checkpoints()
validator.print_summary()

# Cleanup
deleted = validator.cleanup_old_checkpoints(keep_best=3, keep_latest=2)

# Export best
validator.export_best_model("models/my_model/best")
```

### View Metrics Manually

```python
from module.model.training_metrics import TrainingMetricsTracker

tracker = TrainingMetricsTracker("models/my_model", "experiment")
# ... training ...
tracker.print_summary()
tracker.plot_metrics()
```

## Example: Complete Training Script

```python
#!/usr/bin/env python
"""
Complete training example with orchestration
"""

import sys
from pathlib import Path
from module.pipeline_orchestrator import get_orchestrator

def main():
    # Initialize orchestrator
    orchestrator = get_orchestrator({
        'use_enhanced_parser': True,
        'track_training_metrics': True,
        'auto_validate_model': True,
        'manage_checkpoints': True
    })

    # Get training tracker
    tracker = orchestrator.get_training_tracker(
        save_dir="models/code_gen",
        experiment_name="experiment_1"
    )

    print("[*] Starting training with orchestration...")

    # Training loop
    for epoch in range(10):
        # Simulate training
        train_loss = 2.5 - (epoch * 0.2)  # Decreasing loss
        val_loss = 2.6 - (epoch * 0.18)

        # Record metrics
        if tracker:
            tracker.record_epoch(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                learning_rate=1e-4 * (0.9 ** epoch),
                epoch_time=120.5,
                num_samples=10000
            )

        print(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        # Check early stopping
        if tracker and tracker.should_stop_early(patience=3):
            print("[INFO] Early stopping")
            break

    # Finalize
    print("\n[*] Finalizing training...")
    summary = orchestrator.finalize_training(
        model_path="models/code_gen",
        checkpoint_dir="models/code_gen/checkpoints",
        metrics_tracker=tracker
    )

    print("\n[SUCCESS] Training complete!")
    print(f"Metrics: {summary.get('metrics', {}).get('total_epochs')} epochs")
    print(f"Best train loss: {summary.get('metrics', {}).get('best_train_loss', 'N/A')}")

if __name__ == "__main__":
    main()
```

## Benefits

### Automatic Benefits:
1. **Performance Tracking**: All parser operations tracked
2. **Training Monitoring**: Detailed metrics with plots
3. **Quality Assurance**: Automatic model validation
4. **Space Management**: Old checkpoints cleaned automatically
5. **Best Model Selection**: Best checkpoint exported automatically
6. **Reports**: JSON reports generated for all operations

### No Extra Code Required:
- Just use `get_orchestrator()` and call appropriate methods
- All metrics, validation, and cleanup happen automatically
- Comprehensive reports generated without extra work

## Troubleshooting

### Orchestrator Not Loading

```python
# Check if orchestrator is initialized
orchestrator = get_orchestrator()
if orchestrator:
    print("Orchestrator ready")
```

### Parser Metrics Not Showing

```python
# Make sure you're using the enhanced parser
parser = orchestrator.get_parser()
print(f"Parser type: {type(parser).__name__}")

# Should print: UniversalParserEnhanced
```

### Validation Failing

```bash
# Run manual validation for detailed errors
python evaluate_model.py --model models/my_model/ --verbose
```

## See Also

- [validate_pipeline.py](validate_pipeline.py) - End-to-end pipeline validation
- [evaluate_model.py](evaluate_model.py) - Manual model evaluation
- [tests/integration/](tests/integration/) - Integration tests
- [IMPROVEMENTS_v0.8.1.md](IMPROVEMENTS_v0.8.1.md) - Full changelog

## Support

For issues or questions:
1. Check logs in `ml_system.log`
2. Run `python validate_pipeline.py`
3. Run tests: `pytest tests/integration/`
