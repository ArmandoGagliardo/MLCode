# Test Suite

Comprehensive test suite for the Machine Learning project.

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_parser.py      # Parser tests
│   ├── test_quality_filter.py  # Quality filter tests
│   ├── test_duplicate_manager.py  # Duplicate detection tests
│   └── test_config.py      # Configuration tests
└── integration/            # Integration tests
    └── test_pipeline.py    # End-to-end pipeline tests
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

### Run specific test file
```bash
pytest tests/unit/test_parser.py
```

### Run tests with specific markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run with coverage (if pytest-cov installed)
```bash
pytest --cov=module --cov-report=html
```

## Test Markers

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for multiple components
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.requires_gpu` - Tests requiring GPU/CUDA
- `@pytest.mark.requires_network` - Tests requiring network access
- `@pytest.mark.requires_storage` - Tests requiring cloud storage

## Test Coverage

### Current Tests

**Unit Tests (4 files):**
1. **test_parser.py** - 8 tests
   - Parser initialization
   - Python function/class parsing
   - JavaScript parsing
   - Edge cases (empty code, invalid language, malformed code)

2. **test_quality_filter.py** - 8 tests
   - Filter initialization
   - Good code acceptance
   - Bad code rejection (short, TODO, FIXME, no docstring)
   - Empty code handling

3. **test_duplicate_manager.py** - 6 tests
   - Manager initialization
   - First code not duplicate
   - Identical code detection
   - Different code distinction
   - Multiple code tracking

4. **test_config.py** - 6 tests
   - Configuration imports
   - Supported languages
   - Default model
   - Sequence length
   - Storage type
   - GPU setting

**Integration Tests (1 file):**
5. **test_pipeline.py** - 6 tests
   - Parser + Quality Filter integration
   - Parse + Filter + Deduplicate pipeline
   - Dataset creation from parsed code
   - Sample dataset loading
   - Tokenizer integration

**Total: ~34 tests covering critical components**

## Writing New Tests

### Using Fixtures

The `conftest.py` provides shared fixtures:

```python
def test_example(sample_python_code, temp_dir):
    # sample_python_code contains example Python code
    # temp_dir is a temporary directory (auto-cleaned)
    pass
```

### Adding New Fixtures

Add new fixtures to `conftest.py`:

```python
@pytest.fixture
def my_fixture():
    return "some value"
```

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Continuous Integration

To add CI/CD testing (GitHub Actions example):

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest -v
```

## Next Steps

Areas that need more test coverage:

1. Model training components
2. Storage manager (cloud operations)
3. GitHub crawler
4. Web text crawler
5. Specific language parsers
6. Advanced trainer
7. Model manager
8. UI components

To add tests for these, create new test files following the existing patterns.
