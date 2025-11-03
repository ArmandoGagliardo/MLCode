"""
Enhanced Universal Parser with Performance Improvements

Features:
- Parser instance caching
- Performance metrics tracking
- Input validation
- Better error handling
- Logging and debugging
"""

from tree_sitter import Language, Parser, Node
from .universal_parser_new import UniversalParser as BaseUniversalParser
from .parser_improvements import (
    ParserMetrics,
    ParserCache,
    InputValidator,
    CodeHasher,
    time_function
)
from typing import List, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)


class UniversalParserEnhanced(BaseUniversalParser):
    """
    Enhanced universal parser with caching, metrics, and validation.

    Improvements over base parser:
    - Caches Parser instances per language (performance)
    - Tracks detailed metrics (success rate, timing, errors)
    - Validates input before parsing (safety)
    - Better error handling and logging
    - Code hash computation for deduplication
    """

    def __init__(self, enable_metrics: bool = True, enable_caching: bool = True):
        """
        Initialize enhanced parser.

        Args:
            enable_metrics: Enable performance metrics tracking
            enable_caching: Enable parser instance caching
        """
        super().__init__()

        self.enable_metrics = enable_metrics
        self.enable_caching = enable_caching

        # Initialize enhancements
        if enable_metrics:
            self.metrics = ParserMetrics()
            logger.info("[INIT] Performance metrics enabled")

        if enable_caching:
            self.parser_cache = ParserCache(max_size=len(self.languages))
            logger.info("[INIT] Parser caching enabled")

        self.validator = InputValidator()

    def parse(self, code: str, language: str) -> List[Dict]:
        """
        Parse code with enhanced validation and metrics.

        Args:
            code: Source code to parse
            language: Programming language name

        Returns:
            List of dictionaries with extracted code units
        """
        start_time = time.time()

        # Normalize language name
        language = language.lower().strip()

        # Validate language
        is_valid_lang, lang_error = self.validator.validate_language(
            language,
            self.get_supported_languages()
        )

        if not is_valid_lang:
            logger.warning(f"[VALIDATION] {lang_error}")
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_parse(
                    language=language,
                    success=False,
                    duration_ms=duration_ms,
                    error=lang_error
                )
            return []

        # Validate code input
        is_valid_code, code_error = self.validator.validate_code(code, max_size_mb=10.0)

        if not is_valid_code:
            logger.warning(f"[VALIDATION] {code_error}")
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_parse(
                    language=language,
                    success=False,
                    duration_ms=duration_ms,
                    error=code_error
                )
            return []

        # Sanitize code
        code = self.validator.sanitize_code(code)

        # Get language object
        lang_obj = self.languages.get(language)
        if not lang_obj:
            error_msg = f"Language '{language}' not available"
            logger.warning(f"[PARSER] {error_msg}")
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_parse(
                    language=language,
                    success=False,
                    duration_ms=duration_ms,
                    error=error_msg
                )
            return []

        try:
            # Get or create parser instance
            parser = self._get_parser(language, lang_obj)

            # Parse code
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node

            # Check for parse errors
            if root.has_error:
                logger.debug(f"[PARSER] Parse tree has errors for {language}")

            # Extract units
            results = self._extract_units(root, code, language)

            # Count functions and classes
            functions_count = sum(1 for r in results if 'class' not in r.get('task_type', ''))
            classes_count = sum(1 for r in results if 'class' in r.get('task_type', ''))

            # Record successful parse
            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_parse(
                    language=language,
                    success=True,
                    duration_ms=duration_ms,
                    functions_count=functions_count,
                    classes_count=classes_count
                )

            logger.debug(
                f"[SUCCESS] Parsed {language}: "
                f"{functions_count} functions, {classes_count} classes "
                f"in {(time.time() - start_time) * 1000:.2f}ms"
            )

            return results

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ERROR] Failed to parse {language} code: {error_msg}")

            if self.enable_metrics:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_parse(
                    language=language,
                    success=False,
                    duration_ms=duration_ms,
                    error=error_msg
                )

            return []

    def _get_parser(self, language: str, lang_obj: Language) -> Parser:
        """
        Get parser instance (cached or new).

        Args:
            language: Language name
            lang_obj: Language object

        Returns:
            Parser instance
        """
        if self.enable_caching:
            # Try to get from cache
            cached_parser = self.parser_cache.get(language)
            if cached_parser:
                return cached_parser

            # Create new parser and cache it
            parser = Parser()
            parser.language = lang_obj
            self.parser_cache.put(language, parser)
            return parser
        else:
            # No caching - create new parser each time
            parser = Parser()
            parser.language = lang_obj
            return parser

    def parse_with_hash(self, code: str, language: str) -> tuple[List[Dict], str]:
        """
        Parse code and return results with code hash.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Tuple of (parse_results, code_hash)
        """
        results = self.parse(code, language)
        code_hash = CodeHasher.compute_hash(code)
        return results, code_hash

    def parse_batch(self, codes: List[tuple[str, str]], show_progress: bool = False) -> List[List[Dict]]:
        """
        Parse multiple code samples.

        Args:
            codes: List of (code, language) tuples
            show_progress: Show progress bar

        Returns:
            List of parse results
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(codes, desc="Parsing")
            except ImportError:
                iterator = codes
                logger.warning("[BATCH] tqdm not available, progress bar disabled")
        else:
            iterator = codes

        for code, language in iterator:
            result = self.parse(code, language)
            results.append(result)

        return results

    def get_metrics(self) -> Optional[ParserMetrics]:
        """Get performance metrics."""
        if self.enable_metrics:
            return self.metrics
        return None

    def print_metrics(self):
        """Print performance metrics summary."""
        if self.enable_metrics:
            self.metrics.print_summary()
        else:
            logger.warning("[METRICS] Metrics not enabled")

    def get_cache_stats(self) -> Optional[Dict]:
        """Get cache statistics."""
        if self.enable_caching:
            return self.parser_cache.get_stats()
        return None

    def clear_cache(self):
        """Clear parser cache."""
        if self.enable_caching:
            self.parser_cache.clear()
            logger.info("[CACHE] Cleared all cached parsers")

    def reset_metrics(self):
        """Reset metrics counters."""
        if self.enable_metrics:
            self.metrics = ParserMetrics()
            logger.info("[METRICS] Reset all metrics")


def create_parser(enhanced: bool = True, enable_metrics: bool = True, enable_caching: bool = True):
    """
    Factory function to create parser instance.

    Args:
        enhanced: Use enhanced parser with improvements
        enable_metrics: Enable performance metrics (enhanced only)
        enable_caching: Enable parser caching (enhanced only)

    Returns:
        Parser instance
    """
    if enhanced:
        return UniversalParserEnhanced(
            enable_metrics=enable_metrics,
            enable_caching=enable_caching
        )
    else:
        return BaseUniversalParser()


__all__ = ['UniversalParserEnhanced', 'create_parser']
