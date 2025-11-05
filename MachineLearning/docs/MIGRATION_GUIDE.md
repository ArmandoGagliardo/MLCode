# Migration Guide: main.py → CLI v2.0

## Overview

The monolithic `main.py` (1,400+ lines) has been **deprecated** and will be removed in **v3.0.0**.

The new Clean Architecture v2.0 introduces a modular CLI interface that follows industry best practices:

- **Cleaner separation of concerns** (Domain, Application, Infrastructure, Presentation)
- **Easier to test and maintain**
- **Better error handling and user feedback**
- **Extensible command structure**
- **Dependency injection for better testability**

---

## Quick Start

### Old Way (DEPRECATED)
```bash
python main.py --collect-data --language python --count 20
```

### New Way
```bash
python -m presentation.cli collect --language python --count 20
```

---

## Command Migration Map

### 1. Data Collection

#### Old: `--collect-data`
```bash
# Basic collection
python main.py --collect-data --language python --count 20

# From specific repository
python main.py --collect-data --repo https://github.com/user/repo

# From topic
python main.py --collect-data --topic machine-learning --count 50

# With minimum stars
python main.py --collect-data --language python --count 30 --min-stars 1000
```

#### New: `collect`
```bash
# Basic collection
python -m presentation.cli collect --language python --count 20

# From specific repository
python -m presentation.cli collect --url https://github.com/user/repo

# From topic
python -m presentation.cli collect --topic machine-learning --count 50

# With minimum stars (configured in use case)
python -m presentation.cli collect --language python --count 30 --min-stars 1000

# With output file
python -m presentation.cli collect --language python --output data/collected.json
```

---

### 2. Training

#### Old: `--train` / `--train-adv`
```bash
# Basic training
python main.py --train code_generation --dataset data/dataset.json

# Advanced training
python main.py --train-adv code_generation --epochs 10 --batch-size 16

# With custom model
python main.py --train code_generation --model transformer --epochs 20
```

#### New: `train`
```bash
# Basic training
python -m presentation.cli train --dataset data/dataset.json

# With configuration
python -m presentation.cli train --dataset data/dataset.json \
    --model transformer --epochs 10 --batch-size 16

# With learning rate
python -m presentation.cli train --dataset data/dataset.json \
    --epochs 20 --batch-size 32 --learning-rate 0.0001

# Resume from checkpoint
python -m presentation.cli train --dataset data/dataset.json \
    --resume models/checkpoint.pt
```

---

### 3. Dataset Building

#### Old: `--build-dataset`
```bash
# Build dataset
python main.py --build-dataset --data-source local --extraction-mode hybrid

# With context
python main.py --build-dataset --data-source the-stack --with-context

# From specific source
python main.py --build-dataset --extraction-mode functions --max-file-size 2000
```

#### New: `dataset build`
```bash
# Build dataset from collected samples
python -m presentation.cli dataset build \
    --input data/collected/ --output data/dataset.json

# With train/test split
python -m presentation.cli dataset build \
    --input data/collected/ --output data/dataset.json \
    --train-split 0.8

# With deduplication
python -m presentation.cli dataset build \
    --input data/collected/ --output data/dataset.json \
    --deduplicate

# Limit samples
python -m presentation.cli dataset build \
    --input data/collected/ --output data/dataset.json \
    --max-samples 10000 --min-samples 100
```

---

### 4. Dataset Information

#### Old: (No equivalent)
```bash
# No direct equivalent in old CLI
```

#### New: `dataset info`
```bash
# Show dataset information
python -m presentation.cli dataset info --dataset data/dataset.json

# Show detailed statistics
python -m presentation.cli dataset info --dataset data/dataset.json --detailed
```

---

### 5. Dataset Validation

#### Old: `--validate`
```bash
python main.py --validate
```

#### New: `dataset validate`
```bash
# Validate dataset integrity
python -m presentation.cli dataset validate --dataset data/dataset.json

# Validate with quality checks
python -m presentation.cli dataset validate --dataset data/dataset.json \
    --check-quality --min-quality 60.0
```

---

### 6. System Information

#### Old: `--stats`
```bash
python main.py --stats
```

#### New: `info`
```bash
# Show system information
python -m presentation.cli info

# Show configuration
python -m presentation.cli info --config

# Show dependencies
python -m presentation.cli info --deps
```

---

### 7. Health Check

#### Old: `--check-deps` / `--test-connection`
```bash
# Check dependencies
python main.py --check-deps

# Test storage connection
python main.py --test-connection
```

#### New: `health`
```bash
# Check system health
python -m presentation.cli health

# Check with details
python -m presentation.cli health --verbose

# Check specific component
python -m presentation.cli health --component storage
```

---

### 8. Bulk Processing

#### Old: `--bulk-process`
```bash
python main.py --bulk-process --repos-file repo_list.txt --workers 4
```

#### New: Use `collect` with file input
```bash
# Read repositories from file and collect
# TODO: This feature is being redesigned in v2.1
# For now, process repos individually with collect command
```

---

### 9. The Stack Integration

#### Old: `--download-stack`
```bash
python main.py --download-stack \
    --stack-languages python javascript \
    --stack-count 50000 \
    --stack-min-stars 100 \
    --stack-min-quality 80
```

#### New: Planned for v2.1
```bash
# This feature is being redesigned for better integration
# Will be available as: python -m presentation.cli stack download ...
```

---

### 10. Domain Adaptive Training

#### Old: `--train-adaptive`
```bash
python main.py --train-adaptive \
    --base-model bigcode/santacoder \
    --adaptive-dataset data.jsonl \
    --adaptive-epochs 5 \
    --fp16 \
    --evaluate-model
```

#### New: Use `train` with base model
```bash
# Domain adaptive training
python -m presentation.cli train \
    --dataset data.jsonl \
    --model transformer \
    --epochs 5 \
    # Base model and advanced features coming in v2.1
```

---

### 11. Cloud Sync

#### Old: `--sync-cloud`
```bash
python main.py --sync-cloud download
python main.py --sync-cloud upload
```

#### New: Planned for v2.1
```bash
# Cloud sync is being redesigned
# Will be available as storage commands
```

---

### 12. Web UI

#### Old: `--ui`
```bash
python main.py --ui
```

#### New: Planned for v2.2
```bash
# Web UI is being redesigned as separate package
# Will be available as: python -m presentation.web
```

---

### 13. Interactive Pipeline

#### Old: `--pipeline`
```bash
python main.py --pipeline
```

#### New: Planned for v2.1
```bash
# Interactive mode coming soon
python -m presentation.cli interactive
```

---

## Global Options

### Verbosity

#### Old
```bash
# No built-in verbose mode
```

#### New
```bash
# Verbose mode
python -m presentation.cli --verbose collect --language python

# Quiet mode
python -m presentation.cli --quiet collect --language python
```

---

## Configuration

### Old: Environment Variables Only
```bash
export GITHUB_TOKEN="your_token"
export STORAGE_PATH="data/storage"
export MIN_QUALITY_SCORE=60.0
python main.py --collect-data --language python
```

### New: Environment Variables + DI Container
```bash
# Same environment variables
export GITHUB_TOKEN="your_token"
export STORAGE_PATH="data/storage"
export MIN_QUALITY_SCORE=60.0

# Or configure programmatically via Container
python -m presentation.cli collect --language python
```

---

## Architecture Benefits

### Old Architecture (Monolithic)
```
main.py (1,400 lines)
├── All imports at top
├── All logic in one file
├── Hard to test
├── Hard to maintain
└── Tight coupling
```

### New Architecture (Clean Architecture)
```
presentation/cli/
├── main.py              # CLI entry point
├── commands/
│   ├── collect.py       # Collection command
│   ├── train.py         # Training command
│   └── dataset.py       # Dataset commands
│
application/
├── services/            # Business logic
├── use_cases/           # Application operations
│   ├── collect_github_data.py
│   ├── train_model.py
│   └── build_dataset.py
│
infrastructure/          # External integrations
└── config/
    └── container.py     # Dependency injection
```

**Benefits:**
- ✅ **Testable**: Each layer can be tested independently
- ✅ **Maintainable**: Changes are isolated to specific layers
- ✅ **Extensible**: Easy to add new commands
- ✅ **Configurable**: Centralized dependency management
- ✅ **SOLID Principles**: Follows best practices

---

## Migration Checklist

- [ ] Update all scripts/CI that use `python main.py`
- [ ] Update documentation references
- [ ] Test new CLI commands for your workflows
- [ ] Update environment variables if needed
- [ ] Report any missing features as GitHub issues
- [ ] Remove `main.py` from your workflows before v3.0.0

---

## Getting Help

### Old Way
```bash
python main.py --help
```

### New Way
```bash
# Main help
python -m presentation.cli --help

# Command-specific help
python -m presentation.cli collect --help
python -m presentation.cli train --help
python -m presentation.cli dataset --help
python -m presentation.cli info --help
python -m presentation.cli health --help
```

---

## Common Workflows

### Workflow 1: Collect Data and Train Model

#### Old
```bash
# Step 1: Collect
python main.py --collect-data --language python --count 100

# Step 2: Build dataset (manual)
# No direct command, had to use custom scripts

# Step 3: Train
python main.py --train code_generation --dataset data/dataset.json --epochs 10
```

#### New
```bash
# Step 1: Collect
python -m presentation.cli collect --language python --count 100 \
    --output data/collected.json

# Step 2: Build dataset
python -m presentation.cli dataset build \
    --input data/collected.json \
    --output data/dataset.json \
    --train-split 0.8

# Step 3: Validate dataset
python -m presentation.cli dataset validate --dataset data/dataset.json

# Step 4: Train
python -m presentation.cli train --dataset data/dataset.json \
    --model transformer --epochs 10 --batch-size 16
```

---

### Workflow 2: Quick Collection Test

#### Old
```bash
python main.py --collect-data --repo https://github.com/user/repo
```

#### New
```bash
python -m presentation.cli collect --url https://github.com/user/repo
```

---

### Workflow 3: System Health Check

#### Old
```bash
python main.py --check-deps
python main.py --test-connection
python main.py --stats
```

#### New
```bash
# All-in-one health check
python -m presentation.cli health --verbose

# System information
python -m presentation.cli info --config --deps
```

---

## Programmatic Usage

### Old: Import main.py functions
```python
# This was discouraged and difficult
from main import some_function
```

### New: Import use cases and services
```python
from config.container import Container
from application.use_cases import CollectGitHubDataUseCase, CollectGitHubDataRequest

# Get configured dependencies
container = Container()
use_case = container.collect_github_data_use_case()

# Execute use case
request = CollectGitHubDataRequest(
    language='python',
    count=10,
    min_quality=70.0
)
result = use_case.execute(request)

if result.success:
    print(f"Collected {result.total_samples} samples")
```

---

## Feature Status

| Feature | Old main.py | New CLI v2.0 | Status |
|---------|-------------|--------------|--------|
| Data Collection | ✅ | ✅ | Complete |
| Training | ✅ | ⚠️ | Structure complete, training logic TODO |
| Dataset Building | ⚠️ | ✅ | Improved |
| Dataset Validation | ⚠️ | ✅ | New feature |
| Dataset Info | ❌ | ✅ | New feature |
| System Info | ✅ | ✅ | Improved |
| Health Check | ⚠️ | ✅ | Improved |
| Bulk Processing | ✅ | 📅 | Planned v2.1 |
| The Stack Integration | ✅ | 📅 | Planned v2.1 |
| Adaptive Training | ✅ | 📅 | Planned v2.1 |
| Cloud Sync | ✅ | 📅 | Planned v2.1 |
| Web UI | ✅ | 📅 | Planned v2.2 |
| Interactive Pipeline | ✅ | 📅 | Planned v2.1 |

**Legend:**
- ✅ Complete
- ⚠️ Partial/Placeholder
- ❌ Not available
- 📅 Planned for future release

---

## Reporting Issues

If you encounter any issues during migration or need a feature that's not yet available:

1. Check this guide for workarounds
2. Check `ARCHITECTURE.md` for architectural details
3. Check `PRESENTATION_LAYER_COMPLETE.md` for CLI documentation
4. Open an issue on GitHub with:
   - Old command you were using
   - What you're trying to achieve
   - Any error messages

---

## Timeline

- **v2.0.0** (Current) - New CLI with core features, main.py deprecated
- **v2.1.0** (Q1 2026) - Bulk processing, Stack integration, Adaptive training
- **v2.2.0** (Q2 2026) - Web UI, Advanced features
- **v3.0.0** (Q3 2026) - **main.py removed**, full feature parity

---

## Additional Resources

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
- [PRESENTATION_LAYER_COMPLETE.md](PRESENTATION_LAYER_COMPLETE.md) - Complete CLI guide
- [README_v2.0.md](README_v2.0.md) - Getting started with v2.0
- [CLEAN_ARCHITECTURE_COMPLETE.md](CLEAN_ARCHITECTURE_COMPLETE.md) - Clean Architecture details

---

## Questions?

For questions or help with migration:
- Check the documentation above
- Review example commands in `presentation/cli/commands/`
- Look at use case implementations in `application/use_cases/`
- Check the DI container in `config/container.py`

---

**Last Updated:** 2025-11-05
**Version:** 2.0.0
**Status:** main.py deprecated, will be removed in v3.0.0
