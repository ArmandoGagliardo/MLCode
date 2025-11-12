# End-to-End Pipeline Test - Clean Architecture v2.0

## Overview

Comprehensive test script that validates the entire ML pipeline in **< 5 minutes**.

Tests all Clean Architecture layers:
- ✅ Domain Layer (models, interfaces)
- ✅ Application Layer (services, use cases)
- ✅ Infrastructure Layer (training, validation, inference)
- ✅ Config Layer (container, dependency injection)

## Quick Start

```bash
# Basic run (10 samples, 2 epochs)
python test_e2e_pipeline.py

# With more samples
python test_e2e_pipeline.py --samples 20 --epochs 3

# Debug mode (keep temp files)
python test_e2e_pipeline.py --no-cleanup --verbose
```

## Test Phases

### Phase 0: Environment Setup (10s)
- Initialize DI Container
- Create temporary directories
- Configure logging

### Phase 1: Data Collection (60s)
- Generate 10 synthetic Python code samples
- Save to temporary JSON dataset
- Simple templates: add, multiply, greet, factorial, is_even

### Phase 2: Training (120s)
- Model: `microsoft/codebert-base` (125M parameters)
- Epochs: 2 (configurable)
- Batch size: 2 (configurable)
- Learning rate: 5e-5
- Max sequence length: 128 tokens

### Phase 3: Model Validation (30s)
- Uses `ModelValidator` from `infrastructure/validation/`
- Quick mode validation
- Checks: file existence, model loadable, inference works
- Collects metrics

### Phase 4: Inference Testing (20s)
- Initialize `InferenceService`
- Test 5 predictions
- Measure inference times
- Verify output format

### Phase 5: Cleanup (20s)
- Delete temporary dataset
- Delete model checkpoint
- Free disk space (~130MB)
- Generate final report

## Command Line Options

```bash
python test_e2e_pipeline.py [OPTIONS]

Options:
  --samples INT       Number of synthetic samples (default: 10)
  --epochs INT        Number of training epochs (default: 2)
  --batch-size INT    Training batch size (default: 2)
  --device {cpu,cuda} Device to use (default: cpu)
  --no-cleanup        Skip cleanup phase, keep temp files
  --verbose           Enable verbose logging
  -h, --help          Show help message
```

## Examples

### Standard Test
```bash
python test_e2e_pipeline.py
```

**Expected output:**
```
================================================================================
    CLEAN ARCHITECTURE v2.0 - END-TO-END PIPELINE TEST
================================================================================

[PHASE 0/6] Environment Setup
  ✓ Temporary directories created
  ✓ Logging configured

[PHASE 1/6] Data Collection
  → Creating synthetic dataset...
  ✓ 10 samples generated
  ✓ Dataset saved: /tmp/test_e2e_xxx/dataset.json
  → Duration: 5.2s

[PHASE 2/6] Training
  → Loading model: microsoft/codebert-base
  ✓ Model loaded (125,000,000 parameters)
  → Training epoch 1/2...
  → Training epoch 2/2...
  ✓ Training complete
  ✓ Model saved: /tmp/test_e2e_xxx/model
  → Duration: 98.7s

[PHASE 3/6] Validation
  → Running ModelValidator (quick mode)...
  ✓ Files Exist
  ✓ Model Loadable
  ✓ Tokenizer Loadable
  → Duration: 18.4s

[PHASE 4/6] Inference Testing
  → Testing prediction 1/5... ✓ (38ms)
  → Testing prediction 2/5... ✓ (35ms)
  → Testing prediction 3/5... ✓ (37ms)
  → Testing prediction 4/5... ✓ (39ms)
  → Testing prediction 5/5... ✓ (36ms)
  ✓ 5/5 predictions successful
  → Duration: 12.3s

[PHASE 5/6] Cleanup
  → Deleting temporary files...
  ✓ Deleted 45 files (130.2 MB)
  ✓ Deleted temp directory
  → Duration: 8.1s

================================================================================
                              TEST SUMMARY
================================================================================
Status: SUCCESS ✓
Total Duration: 142.7 seconds (2.4m)
Target: < 300 seconds (5 minutes) ✓

Architecture Components Tested:
  ✓ Domain Layer (models, interfaces)
  ✓ Application Layer (services, use cases)
  ✓ Infrastructure Layer (training, validation)
  ✓ Config Layer (container, DI)

Phase Results:
  ✓ Data Collection: SUCCESS (5.2s)
      Samples: 10
  ✓ Training: SUCCESS (98.7s)
      Final loss: 0.4123
  ✓ Validation: SUCCESS (18.4s)
      Checks: 3/3
  ✓ Inference: SUCCESS (12.3s)
      Predictions: 5/5 (avg 37.0ms)
  ✓ Cleanup: SUCCESS (8.1s)
      Space freed: 130.2 MB

Report saved: test_e2e_report_20251105_123456.json
```

### Extended Test
```bash
python test_e2e_pipeline.py --samples 20 --epochs 5 --verbose
```

More samples and epochs for thorough testing.

### Debug Mode
```bash
python test_e2e_pipeline.py --no-cleanup --verbose
```

Keeps temporary files for inspection. Useful for debugging.

### GPU Test (if available)
```bash
python test_e2e_pipeline.py --device cuda
```

Uses GPU for faster training.

## Output Files

### Test Log
**File:** `test_e2e.log`

Contains detailed execution logs:
```
[INFO] Created temp directory: /tmp/test_e2e_20251105_123456
[INFO] Dataset saved: /tmp/test_e2e_20251105_123456/dataset.json
[INFO] Model loaded with 125000000 parameters
[INFO] Training complete
[INFO] Validation passed: 3/3 checks
[INFO] Inference successful: 5/5 predictions
[INFO] Cleanup complete: 45 files deleted
```

### Test Report
**File:** `test_e2e_report_20251105_123456.json`

JSON report with complete test results:
```json
{
  "run_id": "e2e_20251105_123456",
  "status": "SUCCESS",
  "total_duration": 142.7,
  "phases": {
    "data_collection": {
      "status": "SUCCESS",
      "duration_seconds": 5.2,
      "samples_collected": 10,
      "dataset_size_kb": 2.4
    },
    "training": {
      "status": "SUCCESS",
      "duration_seconds": 98.7,
      "num_epochs": 2,
      "train_samples": 8,
      "val_samples": 2,
      "final_train_loss": 0.4123,
      "model_size_mb": 130.5
    },
    "validation": {
      "status": "SUCCESS",
      "duration_seconds": 18.4,
      "checks_total": 3,
      "checks_passed": 3,
      "checks_failed": 0
    },
    "inference": {
      "status": "SUCCESS",
      "duration_seconds": 12.3,
      "test_samples": 5,
      "successful_predictions": 5,
      "avg_inference_time_ms": 37.0
    },
    "cleanup": {
      "status": "SUCCESS",
      "duration_seconds": 8.1,
      "files_deleted": 45,
      "space_freed_mb": 130.2
    }
  },
  "system_info": {
    "python_version": "3.9.7",
    "platform": "Windows-10-10.0.22000-SP0",
    "machine": "AMD64"
  }
}
```

## Requirements

### Python Dependencies
```bash
pip install torch transformers datasets
```

### Hardware Requirements
- **CPU**: Any modern CPU (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 500MB free space (temporary files)
- **GPU** (optional): CUDA-compatible GPU for faster training

### Software Requirements
- Python 3.8+
- Git (for version control)
- Virtual environment (recommended)

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution:**
```bash
pip install torch transformers datasets
```

Or use virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install torch transformers datasets
```

### Issue: "CUDA out of memory"

**Solution:**
```bash
# Use CPU instead
python test_e2e_pipeline.py --device cpu

# Or reduce batch size
python test_e2e_pipeline.py --batch-size 1
```

### Issue: "Test takes too long (> 5 minutes)"

**Solution:**
```bash
# Reduce samples and epochs
python test_e2e_pipeline.py --samples 5 --epochs 1

# Check system resources
# Training on CPU is slower than GPU
```

### Issue: "Permission denied" during cleanup

**Solution:**
```bash
# Run with elevated permissions (if needed)
sudo python test_e2e_pipeline.py  # Linux/Mac

# Or skip cleanup and manually delete later
python test_e2e_pipeline.py --no-cleanup
```

## Architecture Validation

The test validates the following Clean Architecture principles:

### Layer Independence
- ✅ Domain layer has no external dependencies
- ✅ Application layer depends only on Domain
- ✅ Infrastructure implements Domain interfaces
- ✅ Presentation depends on Application

### SOLID Principles
- ✅ Single Responsibility: Each component has one purpose
- ✅ Open/Closed: Extended via interfaces, not modification
- ✅ Liskov Substitution: Interfaces properly implemented
- ✅ Interface Segregation: Minimal, focused interfaces
- ✅ Dependency Inversion: Depend on abstractions

### Dependency Injection
- ✅ Container pattern used throughout
- ✅ No hard-coded dependencies
- ✅ Easy to swap implementations

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: E2E Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install torch transformers datasets
      - name: Run E2E test
        run: |
          python test_e2e_pipeline.py --samples 5 --epochs 1
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test_e2e_report_*.json
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'pip install torch transformers datasets'
            }
        }
        stage('E2E Test') {
            steps {
                sh 'python test_e2e_pipeline.py'
            }
        }
        stage('Archive') {
            steps {
                archiveArtifacts 'test_e2e_report_*.json'
            }
        }
    }
}
```

## Performance Benchmarks

### Expected Timing (CPU)
- Data Collection: 5-10s
- Training: 90-120s
- Validation: 15-30s
- Inference: 10-20s
- Cleanup: 5-15s
- **Total**: 125-195s (2-3 minutes)

### Expected Timing (GPU)
- Data Collection: 5-10s
- Training: 30-60s (3x faster)
- Validation: 10-20s
- Inference: 5-10s
- Cleanup: 5-15s
- **Total**: 55-115s (1-2 minutes)

## Maintenance

### Updating Test Data
Edit the `templates` list in `_phase_data_collection()` method:
```python
templates = [
    {
        "input": "Write a function to...",
        "output": "def function_name():\n    ...",
        "func_name": "function_name",
        "language": "python"
    },
    # Add more templates
]
```

### Changing Model
Edit `_phase_training()` method:
```python
model_name = "microsoft/codebert-base"  # Change to different model
```

### Adjusting Parameters
Modify default values in `E2ETestRunner.__init__()`:
```python
def __init__(self, num_samples=10, num_epochs=2, ...):
    ...
```

## Contributing

To add new test phases:

1. Add phase method:
```python
def _phase_new_feature(self) -> Dict[str, Any]:
    start = time.time()
    try:
        # Test logic
        return {"status": "SUCCESS", "duration_seconds": time.time() - start}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}
```

2. Add to `run()` method:
```python
self.results["phases"]["new_feature"] = self._phase_new_feature()
```

3. Update documentation

## License

Part of the Clean Architecture v2.0 Machine Learning project.

## Support

For issues, questions, or contributions:
- Check existing issues in the repository
- Review Clean Architecture v2.0 documentation
- Consult changesets for migration history

---

**Last Updated:** 2025-11-05
**Version:** 1.0.0
**Status:** Production Ready ✅
