# Example: How to Integrate Orchestrator in main.py

This document shows exactly where and how to add orchestrator integration to main.py.

## Changes Required

### 1. Add Import at Top

```python
# At the top of main.py, after existing imports:
from module.pipeline_orchestrator import get_orchestrator
```

### 2. Initialize Orchestrator in main()

```python
def main():
    """Main entry point."""
    args = parse_args()

    # ADD THIS: Initialize orchestrator
    orchestrator = get_orchestrator({
        'use_enhanced_parser': True,
        'track_training_metrics': True,
        'auto_validate_model': True,
        'manage_checkpoints': True
    })
    logger.info("[MAIN] Pipeline orchestrator initialized")

    # Rest of your existing code...
```

### 3. Integrate in Training Function

Find your training function and modify it like this:

```python
def train_model(args):
    """Train ML model with automatic orchestration."""

    # ADD THIS: Get orchestrator
    from module.pipeline_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()

    # ADD THIS: Get training tracker
    experiment_name = f"{args.task}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tracker = orchestrator.get_training_tracker(
        save_dir=f"models/{args.task}",
        experiment_name=experiment_name
    )

    # Your existing model setup code...
    model_manager = ModelManager(task=args.task, model_name=args.model_name)
    trainer = AdvancedTrainer(model_manager, use_gpu=True)

    # MODIFY: Add tracker to training loop
    print("\n[*] Starting training with metrics tracking...")

    # Example training loop modification:
    for epoch in range(num_epochs):
        epoch_start = time.time()

        # Your existing training code
        train_loss = trainer.train_epoch(...)  # Your training code
        val_loss = trainer.validate(...)       # Your validation code

        epoch_time = time.time() - epoch_start

        # ADD THIS: Record metrics
        if tracker:
            tracker.record_epoch(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                learning_rate=trainer.get_current_lr(),
                epoch_time=epoch_time,
                num_samples=len(train_dataset)
            )

        # ADD THIS: Check early stopping
        if tracker and tracker.should_stop_early(patience=5):
            logger.info("[TRAINING] Early stopping triggered")
            print("\n[*] Early stopping - no improvement for 5 epochs")
            break

    # ADD THIS: Finalize training
    print("\n[*] Finalizing training...")
    summary = orchestrator.finalize_training(
        model_path=f"models/{args.task}",
        checkpoint_dir=f"models/{args.task}/checkpoints" if has_checkpoints else None,
        metrics_tracker=tracker
    )

    # ADD THIS: Print summary
    if summary['validation'] and summary['validation']['passed']:
        print("\n[SUCCESS] Model trained and validated successfully!")
    else:
        print("\n[WARNING] Model trained but validation had issues")

    return summary
```

### 4. Integrate in Data Collection

Find your data collection function:

```python
def collect_data(args):
    """Collect data with enhanced parser."""

    # ADD THIS: Get enhanced parser from orchestrator
    from module.pipeline_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    parser = orchestrator.get_parser()

    # Your existing collection code...
    processor = GitHubRepoProcessor(
        language=args.language,
        # REPLACE: parser=UniversalParser()
        # WITH:
        parser=parser  # Use orchestrator's parser
    )

    # Your existing processing code...
    results = processor.process_repository(repo_url)

    # ADD THIS: Print parser metrics at the end
    print("\n[*] Data Collection Complete")
    orchestrator.print_parser_metrics(parser)

    return results
```

## Complete Example Function

Here's a complete example of an orchestrated training function:

```python
def train_with_orchestration(
    task: str,
    dataset_path: str,
    model_name: str = "Salesforce/codegen-350M-mono",
    num_epochs: int = 3,
    batch_size: int = 4
):
    """
    Complete training function with orchestration.

    This is a complete example showing all integration points.
    """
    from module.pipeline_orchestrator import get_orchestrator
    from module.model.model_manager import ModelManager
    from module.model.training_model_advanced import AdvancedTrainer
    from datasets import load_dataset
    import time

    print("="*70)
    print("[*] TRAINING WITH AUTOMATIC ORCHESTRATION")
    print("="*70)

    # 1. Initialize orchestrator
    orchestrator = get_orchestrator()
    logger.info("[SETUP] Orchestrator initialized")

    # 2. Get training metrics tracker
    experiment_name = f"{task}_{time.strftime('%Y%m%d_%H%M%S')}"
    tracker = orchestrator.get_training_tracker(
        save_dir=f"models/{task}",
        experiment_name=experiment_name
    )
    logger.info(f"[SETUP] Metrics tracker: {experiment_name}")

    # 3. Load dataset
    print("\n[*] Loading dataset...")
    dataset = load_dataset('json', data_files=dataset_path, split='train')
    train_size = int(0.9 * len(dataset))
    train_dataset = dataset.select(range(train_size))
    val_dataset = dataset.select(range(train_size, len(dataset)))

    logger.info(f"[DATA] Train: {len(train_dataset)}, Val: {len(val_dataset)}")

    # 4. Initialize model and trainer
    print("\n[*] Initializing model...")
    model_manager = ModelManager(task=task, model_name=model_name)
    trainer = AdvancedTrainer(model_manager, use_gpu=True)

    # 5. Training loop with metrics
    print(f"\n[*] Training for {num_epochs} epochs...")
    best_val_loss = float('inf')

    for epoch in range(num_epochs):
        epoch_start = time.time()

        print(f"\n--- Epoch {epoch + 1}/{num_epochs} ---")

        # Train
        train_loss = trainer.train_epoch(
            train_dataset,
            batch_size=batch_size
        )

        # Validate
        val_loss = trainer.validate(
            val_dataset,
            batch_size=batch_size
        )

        epoch_time = time.time() - epoch_start

        # Get learning rate
        current_lr = trainer.optimizer.param_groups[0]['lr']

        # Print progress
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}")
        print(f"Time: {epoch_time:.2f}s")

        # Record metrics
        if tracker:
            tracker.record_epoch(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                learning_rate=current_lr,
                epoch_time=epoch_time,
                num_samples=len(train_dataset)
            )

        # Save checkpoint if improved
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            checkpoint_path = f"models/{task}/checkpoints/checkpoint-epoch-{epoch}.pt"
            trainer.save_checkpoint(checkpoint_path, epoch, val_loss)
            print(f"[SAVE] Checkpoint saved: {checkpoint_path}")

        # Check early stopping
        if tracker and tracker.should_stop_early(patience=3, min_delta=0.01):
            print("\n[INFO] Early stopping - no significant improvement")
            break

    # 6. Save final model
    print("\n[*] Saving final model...")
    model_save_path = f"models/{task}/final_model"
    trainer.save_model(model_save_path)

    # 7. Finalize with orchestrator
    print("\n[*] Finalizing training...")
    summary = orchestrator.finalize_training(
        model_path=model_save_path,
        checkpoint_dir=f"models/{task}/checkpoints",
        metrics_tracker=tracker
    )

    # 8. Print final summary
    print("\n" + "="*70)
    print("[*] TRAINING SUMMARY")
    print("="*70)

    if summary.get('metrics'):
        metrics = summary['metrics']
        print(f"\nTraining Metrics:")
        print(f"  Total Epochs: {metrics.get('total_epochs', 'N/A')}")
        print(f"  Best Train Loss: {metrics.get('best_train_loss', 'N/A'):.4f}")
        print(f"  Best Val Loss: {metrics.get('best_val_loss', 'N/A'):.4f}")
        print(f"  Total Time: {metrics.get('total_time_hours', 0):.2f} hours")

    if summary.get('validation'):
        validation = summary['validation']
        status = "PASSED ✓" if validation['passed'] else "FAILED ✗"
        print(f"\nModel Validation: {status}")

        if not validation['passed']:
            print(f"  Errors: {len(validation.get('errors', []))}")
            for error in validation.get('errors', [])[:3]:
                print(f"    - {error}")

    if summary.get('checkpoints'):
        ckpt_info = summary['checkpoints']
        print(f"\nCheckpoint Management:")
        print(f"  Total Checkpoints: {ckpt_info.get('total_checkpoints', 0)}")
        print(f"  Cleaned Up: {ckpt_info.get('deleted_count', 0)}")
        if ckpt_info.get('best_model_path'):
            print(f"  Best Model: {ckpt_info['best_model_path']}")

    print("\n" + "="*70)

    if summary.get('validation', {}).get('passed', False):
        print("\n[SUCCESS] Training completed successfully!")
        return 0
    else:
        print("\n[WARNING] Training completed with validation issues")
        return 1
```

## Testing the Integration

After making changes, test with:

```bash
# 1. Test data collection
python main.py --collect-data --language python --count 10

# 2. Test training
python main.py --train code_generation --epochs 2

# 3. Check generated reports
ls models/code_generation/validation_reports/
ls models/code_generation/*_metrics.json
ls models/code_generation/*_plots.png
```

## Expected Output

After training with orchestration, you should see:

```
[*] Starting training with metrics tracking...

--- Epoch 1/3 ---
Train Loss: 2.3456
Val Loss: 2.4123
Time: 120.34s
[SAVE] Checkpoint saved

--- Epoch 2/3 ---
...

[*] Finalizing training...
[VALIDATION] Starting auto-validation
[OK] Model loaded successfully
[OK] Tokenizer loaded
[OK] Inference working
[OK] Benchmark complete

[CHECKPOINTS] Managing checkpoints
[CHECKPOINTS] Cleaned up 2 old checkpoints
[CHECKPOINTS] Best model exported: models/code_generation/best_model

[*] TRAINING SUMMARY
Training Metrics:
  Total Epochs: 3
  Best Train Loss: 2.1234
  Best Val Loss: 2.2345
  Total Time: 0.52 hours

Model Validation: PASSED ✓

Checkpoint Management:
  Total Checkpoints: 5
  Cleaned Up: 2
  Best Model: models/code_generation/best_model

[SUCCESS] Training completed successfully!
```

## Files Created Automatically

After orchestrated training:

```
models/
└── code_generation/
    ├── final_model/
    │   ├── pytorch_model.bin
    │   ├── config.json
    │   └── tokenizer files...
    ├── best_model/
    │   ├── pytorch_model.bin  # Best checkpoint
    │   └── export_metadata.json
    ├── checkpoints/
    │   ├── checkpoint-epoch-0.pt
    │   ├── checkpoint-epoch-2.pt  # Only best kept
    │   └── checkpoint-epoch-4.pt
    ├── validation_reports/
    │   └── validation_code_generation.json
    ├── code_generation_experiment_metrics.json
    ├── code_generation_experiment_plots.png
    └── training_summary.json
```

## Next Steps

1. Add orchestrator initialization to your main()
2. Integrate tracker in training functions
3. Use enhanced parser in data collection
4. Test with small dataset first
5. Review generated reports
6. Adjust configuration as needed

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for more details.
