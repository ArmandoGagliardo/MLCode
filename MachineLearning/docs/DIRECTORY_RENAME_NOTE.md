# Directory Rename: datasets → dataset_storage

## What Changed

The root `datasets/` directory has been renamed to `dataset_storage/` to avoid conflicts with the HuggingFace `datasets` Python package.

### Before
```
MachineLearning/
├── datasets/              # ← Conflicts with HuggingFace package
│   ├── local_backup/
│   ├── raw/
│   └── security/
```

### After
```
MachineLearning/
├── dataset_storage/       # ← No conflicts!
│   ├── local_backup/
│   ├── raw/
│   └── security/
```

## Why?

When you try to `from datasets import load_dataset`, Python was importing from the local `datasets/` directory instead of the HuggingFace package, causing import errors.

## What Was Updated

All references updated automatically:

1. **config.py**
   - `datasets/local_backup` → `dataset_storage/local_backup`
   - `datasets/code_generation` → `dataset_storage/code_generation`

2. **main.py**
   - All path references updated

3. **bulk_processor.py**
   - All path references updated

4. **cleanup_temp_repos.py**
   - All path references updated

5. **Documentation**
   - All `.md` files updated
   - Examples use new path

6. **.gitignore**
   - Updated to ignore `dataset_storage/`

## Migration Guide

If you have existing scripts or configurations:

### Update Custom Scripts

Replace:
```python
dataset_path = "datasets/local_backup/code_generation/my_data.jsonl"
```

With:
```python
dataset_path = "dataset_storage/local_backup/code_generation/my_data.jsonl"
```

### Update Command Line Args

Replace:
```bash
python main.py --train-adv code_generation \
  --dataset datasets/local_backup/code_generation/data.jsonl
```

With:
```bash
python main.py --train-adv code_generation \
  --dataset dataset_storage/local_backup/code_generation/data.jsonl
```

## Verification

Check that everything works:

```bash
# 1. Verify directory exists
ls dataset_storage/local_backup/code_generation/

# 2. Test import (should work now)
python -c "from datasets import load_dataset; print('OK')"

# 3. Test training
python main.py --train-adv code_generation
```

## Impact

- ✅ **No data loss** - directory just renamed
- ✅ **All scripts updated** - automatic migration
- ✅ **HuggingFace datasets** - now imports correctly
- ✅ **Backward compatible** - old code just needs path update

## Sample Dataset Location

The sample dataset is now at:
```
dataset_storage/local_backup/code_generation/sample_dataset.jsonl
```

Previously:
```
datasets/local_backup/code_generation/sample_dataset.jsonl
```

## Note

This is a **one-time change** to fix the import conflict. Future references should use `dataset_storage/` path.
