"""
Build Dataset Use Case
======================

Use case for building datasets from collected code samples.

This use case orchestrates:
1. Loading collected samples from multiple sources
2. Combining and deduplicating
3. Splitting into train/test sets
4. Formatting for training
5. Saving to output format
"""

import logging
import json
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BuildDatasetRequest:
    """Request object for dataset building."""
    input_path: str
    output_path: str
    format: str = 'json'
    train_split: float = 0.8
    shuffle: bool = True
    min_samples: int = 10
    max_samples: Optional[int] = None
    filter_duplicates: bool = True


@dataclass
class BuildDatasetResponse:
    """Response object for dataset building."""
    success: bool
    output_path: Optional[str] = None
    total_samples: int = 0
    train_samples: int = 0
    test_samples: int = 0
    languages: Dict[str, int] = None
    errors: list = None

    def __post_init__(self):
        if self.languages is None:
            self.languages = {}
        if self.errors is None:
            self.errors = []


class BuildDatasetUseCase:
    """
    Use case for building datasets from collected samples.

    This use case:
    - Loads samples from multiple JSON files
    - Combines and deduplicates
    - Splits train/test
    - Validates quality
    - Saves in requested format

    Example:
        >>> use_case = BuildDatasetUseCase()
        >>>
        >>> request = BuildDatasetRequest(
        ...     input_path='data/collected',
        ...     output_path='data/dataset.json',
        ...     train_split=0.8
        ... )
        >>> response = use_case.execute(request)
        >>>
        >>> if response.success:
        ...     print(f"Dataset: {response.total_samples} samples")
        ...     print(f"Train: {response.train_samples}, Test: {response.test_samples}")
    """

    def __init__(self):
        """Initialize build dataset use case."""
        logger.debug("BuildDatasetUseCase initialized")

    def execute(self, request: BuildDatasetRequest) -> BuildDatasetResponse:
        """
        Execute the dataset building use case.

        Args:
            request: Build request parameters

        Returns:
            BuildDatasetResponse with build results

        Example:
            >>> request = BuildDatasetRequest(
            ...     input_path='data/collected',
            ...     output_path='data/dataset.json',
            ...     train_split=0.8,
            ...     shuffle=True
            ... )
            >>> response = use_case.execute(request)
        """
        logger.info(f"Executing BuildDatasetUseCase: {request}")

        try:
            # Step 1: Validate inputs
            self._validate_request(request)

            # Step 2: Load samples from input
            all_samples = self._load_samples(request.input_path)
            logger.info(f"Loaded {len(all_samples)} samples")

            if len(all_samples) < request.min_samples:
                raise ValueError(
                    f"Not enough samples: {len(all_samples)} < {request.min_samples}"
                )

            # Step 3: Filter duplicates if requested
            if request.filter_duplicates:
                all_samples = self._deduplicate_samples(all_samples)
                logger.info(f"After deduplication: {len(all_samples)} samples")

            # Step 4: Limit samples if max specified
            if request.max_samples and len(all_samples) > request.max_samples:
                all_samples = all_samples[:request.max_samples]
                logger.info(f"Limited to {request.max_samples} samples")

            # Step 5: Shuffle if requested
            if request.shuffle:
                random.shuffle(all_samples)
                logger.debug("Samples shuffled")

            # Step 6: Split train/test
            split_idx = int(len(all_samples) * request.train_split)
            train_samples = all_samples[:split_idx]
            test_samples = all_samples[split_idx:]

            logger.info(f"Split: {len(train_samples)} train, {len(test_samples)} test")

            # Step 7: Calculate statistics
            languages = self._calculate_language_stats(all_samples)

            # Step 8: Save dataset
            self._save_dataset(
                train_samples=train_samples,
                test_samples=test_samples,
                output_path=request.output_path,
                format=request.format,
                metadata={
                    'total_samples': len(all_samples),
                    'train_samples': len(train_samples),
                    'test_samples': len(test_samples),
                    'train_split': request.train_split,
                    'languages': languages,
                    'shuffle': request.shuffle,
                    'deduplicated': request.filter_duplicates
                }
            )

            logger.info(f"Dataset saved to: {request.output_path}")

            return BuildDatasetResponse(
                success=True,
                output_path=request.output_path,
                total_samples=len(all_samples),
                train_samples=len(train_samples),
                test_samples=len(test_samples),
                languages=languages
            )

        except Exception as e:
            logger.error(f"Dataset building failed: {e}", exc_info=True)
            return BuildDatasetResponse(
                success=False,
                errors=[str(e)]
            )

    def _validate_request(self, request: BuildDatasetRequest) -> None:
        """Validate build request."""
        input_path = Path(request.input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input path not found: {request.input_path}")

        if request.train_split <= 0 or request.train_split >= 1:
            raise ValueError(f"Invalid train_split: {request.train_split}")

        if request.format not in ['json', 'jsonl', 'parquet']:
            raise ValueError(f"Unsupported format: {request.format}")

        logger.debug("Request validation passed")

    def _load_samples(self, input_path: str) -> List[Dict]:
        """Load samples from input path (file or directory)."""
        input_path_obj = Path(input_path)
        all_samples = []

        if input_path_obj.is_file():
            # Single file
            samples = self._load_json_file(input_path_obj)
            all_samples.extend(samples)
        else:
            # Directory - find all JSON files
            json_files = list(input_path_obj.rglob('*.json'))
            # Exclude cache files
            json_files = [f for f in json_files if 'cache' not in f.name.lower()]

            for json_file in json_files:
                try:
                    samples = self._load_json_file(json_file)
                    all_samples.extend(samples)
                    logger.debug(f"Loaded {len(samples)} from {json_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to load {json_file}: {e}")

        return all_samples

    def _load_json_file(self, file_path: Path) -> List[Dict]:
        """Load samples from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Handle different formats
            if 'samples' in data:
                return data['samples']
            elif 'train' in data and 'test' in data:
                return data['train'] + data['test']
            else:
                # Treat dict as single sample
                return [data]
        else:
            return []

    def _deduplicate_samples(self, samples: List[Dict]) -> List[Dict]:
        """Remove duplicate samples based on code hash."""
        seen_hashes = set()
        unique_samples = []

        for sample in samples:
            # Generate hash from code content
            code = sample.get('output', sample.get('code', ''))
            code_hash = hash(code.strip().lower().replace(' ', '').replace('\n', ''))

            if code_hash not in seen_hashes:
                seen_hashes.add(code_hash)
                unique_samples.append(sample)

        logger.info(f"Removed {len(samples) - len(unique_samples)} duplicates")
        return unique_samples

    def _calculate_language_stats(self, samples: List[Dict]) -> Dict[str, int]:
        """Calculate language distribution."""
        languages = {}
        for sample in samples:
            lang = sample.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1
        return languages

    def _save_dataset(
        self,
        train_samples: List[Dict],
        test_samples: List[Dict],
        output_path: str,
        format: str,
        metadata: Dict
    ) -> None:
        """Save dataset to output file."""
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            dataset = {
                'train': train_samples,
                'test': test_samples,
                'metadata': metadata
            }
            with open(output_path_obj, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2)

        elif format == 'jsonl':
            # Save as JSON Lines
            with open(output_path_obj, 'w', encoding='utf-8') as f:
                for sample in train_samples:
                    sample['split'] = 'train'
                    f.write(json.dumps(sample) + '\n')
                for sample in test_samples:
                    sample['split'] = 'test'
                    f.write(json.dumps(sample) + '\n')

        elif format == 'parquet':
            # TODO: Implement parquet support
            logger.warning("Parquet format not yet implemented, using JSON")
            self._save_dataset(train_samples, test_samples, output_path, 'json', metadata)

    def __str__(self) -> str:
        """String representation."""
        return "BuildDatasetUseCase()"
