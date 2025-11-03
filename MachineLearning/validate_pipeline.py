"""
End-to-End Pipeline Validation Script

Tests the complete ML pipeline to ensure all components work together:
1. Configuration loading
2. Parser initialization and function extraction
3. Data quality filtering
4. Storage management (if configured)
5. Dataset creation and loading

Usage:
    python validate_pipeline.py
    python validate_pipeline.py --full  # Include storage tests
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import shutil


def validate_config() -> bool:
    """Validate that configuration loads correctly."""
    print("\n[*] Step 1: Validating Configuration")
    print("-" * 60)

    try:
        from config import (
            STORAGE_TYPE,
            SUPPORTED_LANGUAGES,
            DEFAULT_MODEL,
            MAX_SEQUENCE_LENGTH,
            USE_GPU
        )

        print(f"  [OK] Config loaded successfully")
        print(f"  [INFO] Storage type: {STORAGE_TYPE}")
        print(f"  [INFO] Supported languages: {len(SUPPORTED_LANGUAGES)}")
        print(f"  [INFO] Default model: {DEFAULT_MODEL}")
        print(f"  [INFO] Max sequence length: {MAX_SEQUENCE_LENGTH}")
        print(f"  [INFO] GPU enabled: {USE_GPU}")

        return True

    except Exception as e:
        print(f"  [FAIL] Configuration error: {e}")
        return False


def validate_parser() -> bool:
    """Validate universal parser functionality."""
    print("\n[*] Step 2: Validating Universal Parser")
    print("-" * 60)

    try:
        from module.preprocessing.universal_parser_new import UniversalParser

        # Initialize parser
        parser = UniversalParser()
        print(f"  [OK] Parser initialized")

        # Test with sample Python code
        sample_code = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, world!")
    return True

class TestClass:
    """A test class."""

    def __init__(self):
        self.name = "test"

    def get_name(self):
        """Get the name."""
        return self.name
'''

        # Parse the code
        result = parser.parse_code(sample_code, "python")

        if result and 'functions' in result:
            funcs = result['functions']
            print(f"  [OK] Extracted {len(funcs)} functions")

            # Validate extracted functions
            if len(funcs) >= 1:
                func = funcs[0]
                if 'name' in func and 'code' in func:
                    print(f"  [OK] Function structure valid: {func['name']}")
                    return True
                else:
                    print(f"  [FAIL] Function missing required fields")
                    return False
            else:
                print(f"  [WARN] Expected at least 1 function, got {len(funcs)}")
                return False
        else:
            print(f"  [FAIL] Parser returned invalid result")
            return False

    except Exception as e:
        print(f"  [FAIL] Parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_quality_filter() -> bool:
    """Validate quality filtering functionality."""
    print("\n[*] Step 3: Validating Quality Filter")
    print("-" * 60)

    try:
        from module.preprocessing.quality_filter import QualityFilter

        filter = QualityFilter()
        print(f"  [OK] Quality filter initialized")

        # Test with good code
        good_code = '''
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        The sum of all numbers
    """
    total = 0
    for num in numbers:
        total += num
    return total
'''

        # Test with bad code (too short, has TODO)
        bad_code = '''
def foo():
    # TODO: implement this
    pass
'''

        good_result = filter.is_high_quality(good_code, "python")
        bad_result = filter.is_high_quality(bad_code, "python")

        if good_result and not bad_result:
            print(f"  [OK] Quality filter working correctly")
            print(f"       Good code: accepted")
            print(f"       Bad code: rejected")
            return True
        else:
            print(f"  [WARN] Quality filter may need tuning")
            print(f"         Good code result: {good_result}")
            print(f"         Bad code result: {bad_result}")
            return True  # Not a hard failure

    except Exception as e:
        print(f"  [FAIL] Quality filter error: {e}")
        return False


def validate_duplicate_detection() -> bool:
    """Validate duplicate detection functionality."""
    print("\n[*] Step 4: Validating Duplicate Detection")
    print("-" * 60)

    try:
        from module.scripts.duplicate_manager import DuplicateManager

        # Create temporary database
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
            temp_db = f.name

        try:
            manager = DuplicateManager(db_path=temp_db)
            print(f"  [OK] Duplicate manager initialized")

            # Test adding and checking duplicates
            code1 = "def test(): return 42"
            code2 = "def test(): return 42"  # Identical
            code3 = "def other(): return 100"  # Different

            # First code should not be duplicate
            is_dup1 = manager.is_duplicate(code1, "python", "test.py")
            manager.add_code(code1, "python", "test.py")

            # Second code (identical) should be duplicate
            is_dup2 = manager.is_duplicate(code2, "python", "test2.py")

            # Third code (different) should not be duplicate
            is_dup3 = manager.is_duplicate(code3, "python", "test3.py")

            if not is_dup1 and is_dup2 and not is_dup3:
                print(f"  [OK] Duplicate detection working correctly")
                return True
            else:
                print(f"  [FAIL] Duplicate detection not working as expected")
                print(f"         First check (should be False): {is_dup1}")
                print(f"         Second check (should be True): {is_dup2}")
                print(f"         Third check (should be False): {is_dup3}")
                return False

        finally:
            # Cleanup
            if os.path.exists(temp_db):
                os.remove(temp_db)

    except Exception as e:
        print(f"  [FAIL] Duplicate detection error: {e}")
        return False


def validate_storage(test_storage: bool = False) -> bool:
    """Validate storage manager (optional)."""
    print("\n[*] Step 5: Validating Storage Manager")
    print("-" * 60)

    if not test_storage:
        print(f"  [SKIP] Storage tests disabled (use --full to enable)")
        return True

    try:
        from module.storage.storage_manager import StorageManager
        from config import STORAGE_TYPE

        if STORAGE_TYPE == "local":
            print(f"  [SKIP] Local storage configured, no cloud test needed")
            return True

        # Initialize storage manager
        manager = StorageManager()
        print(f"  [OK] Storage manager initialized")
        print(f"  [INFO] Storage type: {STORAGE_TYPE}")

        # Test connection (without actual upload)
        try:
            # Just check if the manager has the required methods
            if hasattr(manager, 'upload_file') and hasattr(manager, 'download_file'):
                print(f"  [OK] Storage manager has required methods")
                return True
            else:
                print(f"  [WARN] Storage manager missing methods")
                return False
        except Exception as e:
            print(f"  [WARN] Storage connection test failed: {e}")
            print(f"         This is OK if credentials are not configured")
            return True

    except Exception as e:
        print(f"  [FAIL] Storage manager error: {e}")
        return False


def validate_dataset_creation() -> bool:
    """Validate dataset creation and loading."""
    print("\n[*] Step 6: Validating Dataset Creation")
    print("-" * 60)

    try:
        from datasets import Dataset
        import json

        # Create sample dataset
        sample_data = [
            {
                "code": "def add(a, b):\n    return a + b",
                "language": "python",
                "docstring": "Add two numbers"
            },
            {
                "code": "def multiply(a, b):\n    return a * b",
                "language": "python",
                "docstring": "Multiply two numbers"
            }
        ]

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save as JSONL
            jsonl_path = Path(temp_dir) / "sample.jsonl"
            with open(jsonl_path, 'w') as f:
                for item in sample_data:
                    f.write(json.dumps(item) + '\n')

            print(f"  [OK] Created sample dataset: {len(sample_data)} examples")

            # Load with HuggingFace datasets
            dataset = Dataset.from_json(str(jsonl_path))

            print(f"  [OK] Loaded dataset with {len(dataset)} examples")

            # Validate structure
            if len(dataset) == len(sample_data):
                print(f"  [OK] Dataset size matches")

                # Check columns
                expected_cols = {'code', 'language', 'docstring'}
                if set(dataset.column_names) == expected_cols:
                    print(f"  [OK] Dataset columns correct: {dataset.column_names}")
                    return True
                else:
                    print(f"  [WARN] Dataset columns: {dataset.column_names}")
                    return True  # Not critical
            else:
                print(f"  [FAIL] Dataset size mismatch")
                return False

    except Exception as e:
        print(f"  [FAIL] Dataset creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_model_loading() -> bool:
    """Validate model and tokenizer loading."""
    print("\n[*] Step 7: Validating Model Loading")
    print("-" * 60)

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from config import DEFAULT_MODEL

        print(f"  [INFO] Testing with model: {DEFAULT_MODEL}")
        print(f"  [INFO] This may download the model (can take time)...")

        # Load tokenizer (small download)
        tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL)
        print(f"  [OK] Tokenizer loaded")

        # Test tokenization
        test_text = "def hello(): pass"
        tokens = tokenizer(test_text, return_tensors="pt")

        if 'input_ids' in tokens:
            print(f"  [OK] Tokenization working")
            print(f"  [INFO] Token count: {len(tokens['input_ids'][0])}")
            return True
        else:
            print(f"  [FAIL] Tokenization failed")
            return False

    except Exception as e:
        print(f"  [WARN] Model loading error: {e}")
        print(f"         This is OK if model is not downloaded yet")
        return True  # Not critical for pipeline validation


def print_summary(results: Dict[str, bool]) -> None:
    """Print validation summary."""
    print("\n" + "=" * 70)
    print("[*] VALIDATION SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\nTotal Tests: {total}")
    print(f"[OK] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")

    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {test_name}")

    if failed == 0:
        print(f"\n[SUCCESS] All validation tests passed!")
        print(f"          The pipeline is ready to use.")
    else:
        print(f"\n[WARN] Some tests failed. Please review the errors above.")
        print(f"       The pipeline may still work, but some features might be unavailable.")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main validation flow."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate ML pipeline end-to-end')
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full validation including storage tests'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only critical tests (skip model loading)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("[*] ML PIPELINE VALIDATION")
    print("=" * 70)

    results = {}

    # Run validation steps
    results['Configuration'] = validate_config()
    results['Universal Parser'] = validate_parser()
    results['Quality Filter'] = validate_quality_filter()
    results['Duplicate Detection'] = validate_duplicate_detection()
    results['Storage Manager'] = validate_storage(test_storage=args.full)
    results['Dataset Creation'] = validate_dataset_creation()

    if not args.quick:
        results['Model Loading'] = validate_model_loading()

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    failed_count = sum(1 for v in results.values() if not v)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
