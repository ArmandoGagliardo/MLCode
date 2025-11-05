"""
Parser Service
==============

Application service that orchestrates code parsing with quality filtering
and duplicate detection.

This is a REFERENCE IMPLEMENTATION showing the OOP/Clean Architecture pattern.
"""

import logging
from typing import List, Optional
from domain.interfaces.parser import IParser
from domain.interfaces.quality_filter import IQualityFilter
from domain.interfaces.duplicate_manager import IDuplicateManager
from domain.models.code_sample import CodeSample, CodeType
from domain.exceptions import ParsingError, ValidationError
from domain.validation.validators import Validator

logger = logging.getLogger(__name__)


class ParserService:
    """
    Service for orchestrating code parsing pipeline.

    This service demonstrates the following patterns:
    - Dependency Injection: Dependencies injected via constructor
    - Single Responsibility: Only orchestrates, doesn't implement parsing/filtering
    - Interface Segregation: Depends on abstractions (IParser, etc.)
    - Open/Closed: Open for extension (new parsers), closed for modification

    Responsibilities:
    1. Parse code using injected parser
    2. Calculate quality scores for each sample
    3. Filter samples below quality threshold
    4. Detect and remove duplicates
    5. Return validated, unique, high-quality samples

    Example:
        >>> parser = TreeSitterParser()
        >>> quality_filter = RadonQualityFilter(min_score=60)
        >>> dedup_manager = ASTDuplicateManager()
        >>>
        >>> service = ParserService(parser, quality_filter, dedup_manager)
        >>> samples = service.parse_and_filter(code, 'python', min_quality=60.0)
        >>> print(f"Extracted {len(samples)} quality samples")
    """

    def __init__(
        self,
        parser: IParser,
        quality_filter: IQualityFilter,
        dedup_manager: IDuplicateManager
    ):
        """
        Initialize parser service with dependencies.

        Args:
            parser: Parser implementation (e.g., TreeSitterParser)
            quality_filter: Quality filter implementation (e.g., RadonQualityFilter)
            dedup_manager: Duplicate manager implementation (e.g., ASTDuplicateManager)

        Example:
            >>> service = ParserService(
            ...     parser=TreeSitterParser(),
            ...     quality_filter=RadonQualityFilter(),
            ...     dedup_manager=ASTDuplicateManager()
            ... )
        """
        self._parser = parser
        self._quality_filter = quality_filter
        self._dedup_manager = dedup_manager

        logger.info("ParserService initialized")
        logger.debug(f"Parser: {parser.__class__.__name__}")
        logger.debug(f"Quality Filter: {quality_filter.__class__.__name__}")
        logger.debug(f"Dedup Manager: {dedup_manager.__class__.__name__}")

    def parse_and_filter(
        self,
        code: str,
        language: str,
        min_quality: Optional[float] = None,
        **parse_options
    ) -> List[CodeSample]:
        """
        Parse code and filter by quality and uniqueness.

        This is the main workflow method that:
        1. Validates inputs
        2. Parses code
        3. Converts to CodeSample objects
        4. Filters by quality
        5. Removes duplicates

        Args:
            code: Source code to parse
            language: Programming language
            min_quality: Minimum quality score (uses filter's default if None)
            **parse_options: Additional options for parser:
                - extract_functions: bool
                - extract_classes: bool
                - extract_docstrings: bool
                - extract_context: bool

        Returns:
            List of validated, unique, high-quality CodeSample objects

        Raises:
            ValidationError: If inputs are invalid
            ParsingError: If parsing fails

        Example:
            >>> code = "def calculate_sum(a, b):\\n    return a + b"
            >>> samples = service.parse_and_filter(code, 'python', min_quality=60.0)
            >>> assert len(samples) >= 1
            >>> assert samples[0].name == 'calculate_sum'
        """
        # Step 1: Validation
        self._validate_inputs(code, language)

        # Step 2: Parse code
        logger.info(f"Parsing {language} code ({len(code)} chars)")
        parsed_items = self._parse_code(code, language, **parse_options)

        if not parsed_items:
            logger.warning(f"No items parsed from {language} code")
            return []

        logger.info(f"Parsed {len(parsed_items)} items")

        # Step 3: Convert to CodeSample objects
        samples = self._convert_to_samples(parsed_items, language)

        # Step 4: Filter by quality
        filtered_samples = self._filter_by_quality(samples, min_quality)

        # Step 5: Remove duplicates
        unique_samples = self._remove_duplicates(filtered_samples, language)

        logger.info(
            f"Pipeline complete: {len(parsed_items)} parsed → "
            f"{len(filtered_samples)} quality → {len(unique_samples)} unique"
        )

        return unique_samples

    def _validate_inputs(self, code: str, language: str) -> None:
        """Validate inputs before parsing"""
        try:
            Validator.validate_not_empty(code, "Code")
            Validator.validate_not_empty(language, "Language")

            # Check parser supports language
            if not self._parser.supports_language(language):
                supported = self._parser.get_supported_languages()
                raise ValidationError(
                    f"Language '{language}' not supported. "
                    f"Supported: {', '.join(supported)}"
                )

        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            raise

    def _parse_code(self, code: str, language: str, **options) -> List[dict]:
        """Parse code using injected parser"""
        try:
            return self._parser.parse(code, language, **options)
        except Exception as e:
            logger.error(f"Parsing failed: {e}", exc_info=True)
            raise ParsingError(f"Failed to parse {language} code: {e}")

    def _convert_to_samples(self, parsed_items: List[dict], language: str) -> List[CodeSample]:
        """Convert parsed items to CodeSample domain objects"""
        samples = []

        for item in parsed_items:
            try:
                # Determine code type
                item_type = item.get('type', 'function')
                code_type = CodeType(item_type) if item_type in ['function', 'class', 'file', 'method'] else CodeType.FUNCTION

                # Create CodeSample
                sample = CodeSample(
                    language=language,
                    code=item.get('code', item.get('body', '')),
                    code_type=code_type,
                    name=item.get('name', item.get('func_name', 'unknown')),
                    docstring=item.get('doc', item.get('docstring')),
                    signature=item.get('signature'),
                    imports=item.get('imports', []),
                    parent_class=item.get('parent_class'),
                    file_path=item.get('file_path'),
                )

                # Validate
                if not sample.is_valid():
                    errors = sample.validate()
                    logger.warning(f"Invalid sample '{sample.name}': {errors}")
                    continue

                samples.append(sample)

            except Exception as e:
                logger.warning(f"Failed to convert item to CodeSample: {e}")
                continue

        return samples

    def _filter_by_quality(
        self,
        samples: List[CodeSample],
        min_quality: Optional[float]
    ) -> List[CodeSample]:
        """Filter samples by quality score"""
        threshold = min_quality if min_quality is not None else self._quality_filter.get_min_score()

        filtered = []
        for sample in samples:
            try:
                # Calculate quality score
                score = self._quality_filter.calculate_score(sample.code, sample.language)
                sample.quality_score = score

                # Check threshold
                if score >= threshold:
                    filtered.append(sample)
                    logger.debug(f"✓ {sample.name}: {score:.1f} >= {threshold}")
                else:
                    logger.debug(f"✗ {sample.name}: {score:.1f} < {threshold}")

            except Exception as e:
                logger.warning(f"Quality check failed for '{sample.name}': {e}")
                continue

        logger.info(f"Quality filter: {len(samples)} → {len(filtered)} (threshold={threshold})")
        return filtered

    def _remove_duplicates(
        self,
        samples: List[CodeSample],
        language: str
    ) -> List[CodeSample]:
        """Remove duplicate samples"""
        unique = []
        duplicates = 0

        for sample in samples:
            if not self._dedup_manager.is_duplicate(sample.code, language):
                self._dedup_manager.add_item(sample.code, language)
                unique.append(sample)
            else:
                duplicates += 1
                logger.debug(f"Duplicate: {sample.name}")

        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicates")

        return unique

    def get_statistics(self) -> dict:
        """Get service statistics"""
        return {
            'parser': self._parser.__class__.__name__,
            'quality_filter': self._quality_filter.__class__.__name__,
            'dedup_manager': self._dedup_manager.__class__.__name__,
            'supported_languages': self._parser.get_supported_languages(),
            'min_quality_score': self._quality_filter.get_min_score(),
            'unique_items_tracked': self._dedup_manager.get_count(),
            'duplicates_found': self._dedup_manager.get_duplicate_count(),
        }
