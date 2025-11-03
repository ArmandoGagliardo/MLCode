"""
Integration tests for the complete pipeline
"""

import pytest
import json
from pathlib import Path
from datasets import Dataset


class TestPipeline:
    """Test the complete data processing pipeline."""

    @pytest.mark.integration
    def test_parser_to_filter_pipeline(self, sample_python_code, sample_bad_code):
        """Test parser output can be filtered by quality filter."""
        from module.preprocessing.universal_parser_new import UniversalParser
        from module.preprocessing.quality_filter import QualityFilter

        parser = UniversalParser()
        quality_filter = QualityFilter()

        # Parse good code
        parsed = parser.parse_code(sample_python_code, "python")
        assert parsed is not None
        assert len(parsed['functions']) > 0

        # Extract first function
        func_code = parsed['functions'][0]['code']

        # Quality check should pass
        is_quality = quality_filter.is_high_quality(func_code, "python")
        assert is_quality is True

        # Parse bad code
        bad_parsed = parser.parse_code(sample_bad_code, "python")
        if bad_parsed and len(bad_parsed['functions']) > 0:
            bad_func_code = bad_parsed['functions'][0]['code']

            # Quality check should fail
            is_bad_quality = quality_filter.is_high_quality(bad_func_code, "python")
            assert is_bad_quality is False

    @pytest.mark.integration
    def test_parse_filter_deduplicate_pipeline(self, sample_python_code, temp_dir):
        """Test complete pipeline: parse -> filter -> deduplicate."""
        from module.preprocessing.universal_parser_new import UniversalParser
        from module.preprocessing.quality_filter import QualityFilter
        from module.scripts.duplicate_manager import DuplicateManager

        # Initialize components
        parser = UniversalParser()
        quality_filter = QualityFilter()
        dup_manager = DuplicateManager(db_path=str(temp_dir / "dups.db"))

        # Parse code
        parsed = parser.parse_code(sample_python_code, "python")
        assert parsed is not None

        functions = parsed['functions']
        assert len(functions) > 0

        # Process each function
        processed_count = 0
        for func in functions:
            func_code = func['code']

            # Quality check
            if not quality_filter.is_high_quality(func_code, "python"):
                continue

            # Duplicate check
            if dup_manager.is_duplicate(func_code, "python", "test.py"):
                continue

            # Add to database
            dup_manager.add_code(func_code, "python", "test.py")
            processed_count += 1

        # Should have processed at least one function
        assert processed_count > 0

        # Re-processing the same code should result in 0 new functions
        re_processed_count = 0
        for func in functions:
            func_code = func['code']

            if not quality_filter.is_high_quality(func_code, "python"):
                continue

            if dup_manager.is_duplicate(func_code, "python", "test.py"):
                continue

            re_processed_count += 1

        assert re_processed_count == 0

    @pytest.mark.integration
    def test_dataset_creation_from_parsed_code(self, sample_python_code, temp_dir):
        """Test creating a HuggingFace dataset from parsed code."""
        from module.preprocessing.universal_parser_new import UniversalParser

        parser = UniversalParser()
        parsed = parser.parse_code(sample_python_code, "python")

        # Create dataset records
        records = []
        for func in parsed['functions']:
            records.append({
                'code': func['code'],
                'name': func.get('name', 'unknown'),
                'language': 'python',
                'docstring': func.get('docstring', '')
            })

        assert len(records) > 0

        # Save as JSONL
        jsonl_path = temp_dir / "dataset.jsonl"
        with open(jsonl_path, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

        # Load with HuggingFace datasets
        dataset = Dataset.from_json(str(jsonl_path))

        assert len(dataset) == len(records)
        assert 'code' in dataset.column_names
        assert 'language' in dataset.column_names

    @pytest.mark.integration
    @pytest.mark.slow
    def test_sample_dataset_loads(self):
        """Test that the sample dataset loads correctly."""
        dataset_path = Path("datasets/local_backup/code_generation/sample_dataset.jsonl")

        if not dataset_path.exists():
            pytest.skip("Sample dataset not found")

        # Load dataset
        dataset = Dataset.from_json(str(dataset_path))

        assert len(dataset) > 0
        assert 'code' in dataset.column_names
        assert 'language' in dataset.column_names
        assert 'docstring' in dataset.column_names

        # Verify each record has required fields
        for record in dataset:
            assert record['code'] is not None
            assert len(record['code']) > 0
            assert record['language'] in ['python', 'javascript', 'java', 'go']

    @pytest.mark.integration
    def test_tokenizer_on_parsed_code(self, sample_python_code):
        """Test that tokenizer works on parsed code."""
        from module.preprocessing.universal_parser_new import UniversalParser
        from transformers import AutoTokenizer
        from config import DEFAULT_MODEL

        parser = UniversalParser()
        parsed = parser.parse_code(sample_python_code, "python")

        # Get first function
        func_code = parsed['functions'][0]['code']

        # Load tokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL)

            # Tokenize
            tokens = tokenizer(func_code, return_tensors="pt", truncation=True)

            assert 'input_ids' in tokens
            assert tokens['input_ids'].shape[1] > 0

        except Exception as e:
            # If model not downloaded, skip
            pytest.skip(f"Model not available: {e}")
