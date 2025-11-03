# Using `--train-adv` - Advanced Training Mode

## Overview

The `--train-adv` command provides advanced training with **automatic orchestration** of all improvements:

- ✅ Enhanced parser with caching and metrics
- ✅ Detailed training metrics tracking
- ✅ Automatic model validation
- ✅ Checkpoint management and cleanup
- ✅ Complete reporting and visualization
- ✅ Early stopping detection

## Basic Usage

### Simple Command (Use Defaults)

```bash
python main.py --train-adv code_generation
```

This will:
1. Use default dataset and model
2. Train with default epochs/batch size
3. Generate automatic experiment name
4. Track all metrics
5. Validate model after training
6. Clean up old checkpoints
7. Generate all reports

### With Custom Parameters

```bash
python main.py --train-adv code_generation \
  --dataset datasets/my_data.jsonl \
  --model Salesforce/codegen-350M-mono \
  --epochs 5 \
  --batch-size 8 \
  --learning-rate 2e-5 \
  --experiment my_experiment_v1
```

## Available Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `TASK` | Training task (required) | - | `code_generation` |
| `--dataset` | Dataset path | From config | `datasets/my_data.jsonl` |
| `--model` | Model name | From config | `Salesforce/codegen-350M-mono` |
| `--epochs` | Number of epochs | From config (3) | `5` |
| `--batch-size` | Batch size | From config (4) | `8` |
| `--learning-rate` | Learning rate | From config (5e-5) | `2e-5` |
| `--experiment` | Experiment name | Auto-generated | `my_experiment_v1` |

## Examples

### Example 1: Quick Training with Defaults

```bash
# Use all defaults
python main.py --train-adv code_generation
```

**Output:**
```
[*] ADVANCED TRAINING MODE
Features enabled:
  ✓ Enhanced parser with caching and metrics
  ✓ Detailed training metrics tracking
  ✓ Automatic model validation
  ✓ Checkpoint management and cleanup
  ✓ Complete reporting and visualization

[*] Step 1/6: Initializing orchestrator...
[*] Step 2/6: Setting up metrics tracking...
[*] Step 3/6: Loading dataset...
[*] Step 4/6: Initializing model and trainer...
[*] Step 5/6: Training for 3 epochs...

--- Epoch 1/3 ---
  Train Loss: 2.3456
  Val Loss: 2.4123
  Time: 120.34s
  [SAVE] Best checkpoint

--- Epoch 2/3 ---
  ...

[*] Step 6/6: Finalizing training...
[VALIDATION] Starting auto-validation
[OK] Model loaded successfully
[OK] Inference working
[CHECKPOINTS] Cleaned up 2 old checkpoints

[SUCCESS] Advanced training completed successfully! ✓
```

### Example 2: Custom Configuration

```bash
# Custom parameters
python main.py --train-adv code_generation \
  --epochs 10 \
  --batch-size 16 \
  --experiment production_v1
```

### Example 3: Custom Dataset

```bash
# Use your own dataset
python main.py --train-adv code_generation \
  --dataset dataset_storage/local_backup/code_generation/my_dataset.jsonl \
  --epochs 5
```

### Example 4: Different Model

```bash
# Use different base model
python main.py --train-adv code_generation \
  --model microsoft/CodeGPT-small-py \
  --epochs 3
```

## Output Files

After running `--train-adv`, you'll find these files:

```
models/code_generation/
├── pytorch_model.bin           # Final trained model
├── config.json                 # Model config
├── tokenizer files...          # Tokenizer files
├── checkpoints/                # Training checkpoints (cleaned)
│   ├── checkpoint-epoch-0.pt
│   ├── checkpoint-epoch-2.pt
│   └── checkpoint-epoch-4.pt
├── best_model/                 # Best checkpoint exported
│   ├── pytorch_model.bin
│   └── export_metadata.json
├── validation_reports/         # Validation results
│   └── validation_code_generation.json
├── code_generation_20250103_143022_metrics.json  # Training metrics
├── code_generation_20250103_143022_plots.png     # Visualization
└── training_summary.json                          # Overall summary
```

## Comparison: Standard vs Advanced Training

### Standard Training (`--train`)

```bash
python main.py --train code_generation
```

**Features:**
- ✅ Basic training
- ✅ Model saved
- ❌ No metrics tracking
- ❌ No validation
- ❌ No checkpoint management
- ❌ No reports

**Use when:** Quick testing, simple experiments

### Advanced Training (`--train-adv`)

```bash
python main.py --train-adv code_generation
```

**Features:**
- ✅ Advanced training
- ✅ Model saved
- ✅ **Automatic metrics tracking**
- ✅ **Automatic validation**
- ✅ **Checkpoint management**
- ✅ **Complete reports**
- ✅ **Early stopping**
- ✅ **Visualization**

**Use when:** Production training, experiments you want to track

## Understanding the Output

### Step 1: Orchestrator Initialization

```
[*] Step 1/6: Initializing orchestrator...
[ORCHESTRATOR] Initialized with all features enabled
```

Sets up automatic tracking and management.

### Step 2: Metrics Tracking

```
[*] Step 2/6: Setting up metrics tracking...
[METRICS] Tracker initialized: code_generation_20250103_143022
```

Creates experiment tracker for this training run.

### Step 3: Dataset Loading

```
[*] Step 3/6: Loading dataset...
    Total samples: 1000
    Training: 900 (90%)
    Validation: 100 (10%)
```

Loads and splits your dataset.

### Step 4: Model Initialization

```
[*] Step 4/6: Initializing model and trainer...
    Trainer: AdvancedTrainer (generation)
```

Loads model and prepares for training.

### Step 5: Training Loop

```
[*] Step 5/6: Training for 3 epochs...

--- Epoch 1/3 ---
  Train Loss: 2.3456
  Val Loss: 2.4123
  Time: 120.34s
  [SAVE] Best checkpoint: checkpoint-epoch-0.pt
```

Trains with automatic metrics recording.

### Step 6: Finalization

```
[*] Step 6/6: Finalizing training...
[VALIDATION] Starting auto-validation
[OK] All validation checks passed
[CHECKPOINTS] Cleaned up 2 old checkpoints
[CHECKPOINTS] Best model exported
```

Automatic validation, cleanup, and reporting.

## Viewing Results

### 1. Training Metrics (JSON)

```bash
cat models/code_generation/code_generation_*_metrics.json
```

Contains:
- Epoch-level metrics (loss, LR, time, throughput)
- Best epoch information
- Training statistics

### 2. Visualization (PNG)

```bash
# Open the plots
open models/code_generation/code_generation_*_plots.png
```

Shows 4 plots:
- Training/Validation loss curves
- Learning rate schedule
- Training throughput (samples/sec)
- Peak memory usage

### 3. Validation Report (JSON)

```bash
cat models/code_generation/validation_reports/validation_code_generation.json
```

Contains:
- File integrity checks
- Model architecture validation
- Inference test results
- Performance benchmarks

### 4. Training Summary (JSON)

```bash
cat models/code_generation/training_summary.json
```

Contains:
- Complete training overview
- Validation status
- Checkpoint information
- All metrics in one place

## Early Stopping

Advanced training includes automatic early stopping:

```
[INFO] Early stopping triggered - no improvement for 5 epochs
```

This happens when validation loss doesn't improve for 5 consecutive epochs.

**Configure:** Edit `train_advanced_impl.py`, look for:
```python
if tracker.should_stop_early(patience=5, min_delta=0.001):
```

## Tips

### 1. Monitor Training

Watch the training progress live:

```bash
# In another terminal
watch -n 1 'tail -20 models/code_generation/code_generation_*_metrics.json'
```

### 2. Compare Experiments

Use different `--experiment` names:

```bash
python main.py --train-adv code_generation --experiment baseline
python main.py --train-adv code_generation --experiment larger_batch --batch-size 16
python main.py --train-adv code_generation --experiment higher_lr --learning-rate 1e-4
```

Then compare the metrics files.

### 3. Resume from Best

The best model is automatically exported to `best_model/`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("models/code_generation/best_model")
tokenizer = AutoTokenizer.from_pretrained("models/code_generation/best_model")
```

### 4. Check Validation Details

```bash
# Pretty print validation report
python -m json.tool models/code_generation/validation_reports/validation_code_generation.json
```

## Troubleshooting

### Issue: Training Fails Immediately

**Check:**
1. Dataset exists: `ls dataset_storage/local_backup/code_generation/`
2. Dependencies: `python check_dependencies.py`
3. GPU available: `python -c "import torch; print(torch.cuda.is_available())"`

### Issue: Out of Memory

**Solution:** Reduce batch size:
```bash
python main.py --train-adv code_generation --batch-size 2
```

### Issue: Training Too Slow

**Solutions:**
- Increase batch size (if memory allows)
- Use smaller dataset for testing
- Use smaller model

### Issue: Validation Fails

**Check:**
```bash
# Run manual validation
python evaluate_model.py --model models/code_generation/ --verbose
```

## Advanced Usage

### Custom Validation Prompts

Create `prompts.txt`:
```
def calculate_sum(numbers):
function reverseString(str) {
class DataProcessor {
```

Then:
```bash
python evaluate_model.py --model models/code_generation/ --prompts prompts.txt
```

### Manual Checkpoint Management

```python
from module.model.checkpoint_validator import CheckpointValidator

validator = CheckpointValidator("models/code_generation/checkpoints")
checkpoints = validator.scan_checkpoints()
validator.print_summary()

# Export specific checkpoint
best = validator.get_best_checkpoint()
validator.export_best_model("models/my_best_model")
```

## Integration with Existing Workflows

### Before (Standard Training)

```bash
# Old way
python main.py --train code_generation
# Done - model saved, no other info
```

### After (Advanced Training)

```bash
# New way
python main.py --train-adv code_generation
# Done - model saved + validated + metrics + plots + reports
```

**Same interface, 10x more value!**

## Next Steps

1. Try advanced training: `python main.py --train-adv code_generation`
2. Review generated reports
3. Compare with standard training
4. Use for all production training

## See Also

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Full orchestrator guide
- [PARSER_AND_ML_IMPROVEMENTS.md](PARSER_AND_ML_IMPROVEMENTS.md) - All improvements
- [evaluate_model.py](evaluate_model.py) - Manual model evaluation
- [tests/integration/](tests/integration/) - Integration tests
