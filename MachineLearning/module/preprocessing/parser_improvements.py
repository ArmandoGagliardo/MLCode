"""
Parser Improvements Module

Enhancements for UniversalParser:
- Parser instance caching
- Performance metrics
- Enhanced error handling
- Input validation
"""

import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParserMetrics:
    """Metrics for parser performance tracking."""

    total_parses: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    total_time_ms: float = 0.0
    functions_extracted: int = 0
    classes_extracted: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    language_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def record_parse(
        self,
        language: str,
        success: bool,
        duration_ms: float,
        functions_count: int = 0,
        classes_count: int = 0,
        error: Optional[str] = None
    ):
        """Record a parse operation."""
        self.total_parses += 1
        self.total_time_ms += duration_ms

        if success:
            self.successful_parses += 1
            self.functions_extracted += functions_count
            self.classes_extracted += classes_count
        else:
            self.failed_parses += 1
            if error:
                self.errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'language': language,
                    'error': error,
                    'duration_ms': duration_ms
                })

        # Update language-specific stats
        if language not in self.language_stats:
            self.language_stats[language] = {
                'total': 0,
                'success': 0,
                'failed': 0,
                'functions': 0,
                'classes': 0,
                'total_time_ms': 0.0
            }

        stats = self.language_stats[language]
        stats['total'] += 1
        stats['total_time_ms'] += duration_ms

        if success:
            stats['success'] += 1
            stats['functions'] += functions_count
            stats['classes'] += classes_count
        else:
            stats['failed'] += 1

    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_parses == 0:
            return 0.0
        return (self.successful_parses / self.total_parses) * 100

    def get_avg_time_ms(self) -> float:
        """Calculate average parse time."""
        if self.total_parses == 0:
            return 0.0
        return self.total_time_ms / self.total_parses

    def get_language_success_rate(self, language: str) -> float:
        """Calculate success rate for specific language."""
        if language not in self.language_stats:
            return 0.0

        stats = self.language_stats[language]
        if stats['total'] == 0:
            return 0.0

        return (stats['success'] / stats['total']) * 100

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            'total_parses': self.total_parses,
            'successful': self.successful_parses,
            'failed': self.failed_parses,
            'success_rate': f"{self.get_success_rate():.2f}%",
            'functions_extracted': self.functions_extracted,
            'classes_extracted': self.classes_extracted,
            'avg_time_ms': f"{self.get_avg_time_ms():.2f}",
            'total_time_sec': f"{self.total_time_ms / 1000:.2f}",
            'languages': {
                lang: {
                    'parses': stats['total'],
                    'success_rate': f"{self.get_language_success_rate(lang):.2f}%",
                    'functions': stats['functions'],
                    'classes': stats['classes'],
                    'avg_time_ms': f"{stats['total_time_ms'] / stats['total']:.2f}" if stats['total'] > 0 else "0.00"
                }
                for lang, stats in self.language_stats.items()
            },
            'recent_errors': self.errors[-10:]  # Last 10 errors
        }

    def print_summary(self):
        """Print formatted metrics summary."""
        print("\n" + "="*70)
        print("[*] PARSER PERFORMANCE METRICS")
        print("="*70)

        print(f"\nOverall Statistics:")
        print(f"  Total Parses: {self.total_parses}")
        print(f"  Successful: {self.successful_parses} ({self.get_success_rate():.2f}%)")
        print(f"  Failed: {self.failed_parses}")
        print(f"  Functions Extracted: {self.functions_extracted}")
        print(f"  Classes Extracted: {self.classes_extracted}")
        print(f"  Avg Time: {self.get_avg_time_ms():.2f}ms")
        print(f"  Total Time: {self.total_time_ms / 1000:.2f}s")

        if self.language_stats:
            print(f"\nPer-Language Statistics:")
            for lang, stats in sorted(self.language_stats.items()):
                success_rate = self.get_language_success_rate(lang)
                avg_time = stats['total_time_ms'] / stats['total'] if stats['total'] > 0 else 0
                print(f"  {lang.capitalize()}:")
                print(f"    Parses: {stats['total']} (success: {success_rate:.1f}%)")
                print(f"    Extracted: {stats['functions']} functions, {stats['classes']} classes")
                print(f"    Avg Time: {avg_time:.2f}ms")

        if self.errors:
            print(f"\nRecent Errors ({len(self.errors)} total):")
            for error in self.errors[-5:]:
                print(f"  [{error['timestamp']}] {error['language']}: {error['error'][:80]}")

        print("\n" + "="*70 + "\n")


class ParserCache:
    """Cache for parser instances to avoid recreation."""

    def __init__(self, max_size: int = 10):
        """
        Initialize parser cache.

        Args:
            max_size: Maximum number of parsers to cache
        """
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = {}

    def get(self, language: str) -> Optional[Any]:
        """Get cached parser for language."""
        if language in self.cache:
            self.access_count[language] = self.access_count.get(language, 0) + 1
            logger.debug(f"[CACHE HIT] Parser for {language}")
            return self.cache[language]

        logger.debug(f"[CACHE MISS] Parser for {language}")
        return None

    def put(self, language: str, parser: Any):
        """Cache parser instance."""
        # If cache is full, remove least accessed item
        if len(self.cache) >= self.max_size:
            least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_used]
            del self.access_count[least_used]
            logger.debug(f"[CACHE EVICT] Removed {least_used} parser")

        self.cache[language] = parser
        self.access_count[language] = 0
        logger.debug(f"[CACHE ADD] Cached {language} parser")

    def clear(self):
        """Clear all cached parsers."""
        self.cache.clear()
        self.access_count.clear()
        logger.debug("[CACHE CLEAR] All parsers removed")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'languages': list(self.cache.keys()),
            'access_counts': self.access_count.copy()
        }


class InputValidator:
    """Validator for parser input."""

    @staticmethod
    def validate_code(code: str, max_size_mb: float = 10.0) -> tuple[bool, Optional[str]]:
        """
        Validate code input.

        Args:
            code: Source code to validate
            max_size_mb: Maximum allowed size in MB

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if code is string
        if not isinstance(code, str):
            return False, f"Code must be string, got {type(code).__name__}"

        # Check if code is empty
        if not code.strip():
            return False, "Code is empty or whitespace only"

        # Check size
        size_mb = len(code.encode('utf-8')) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Code too large: {size_mb:.2f}MB (max: {max_size_mb}MB)"

        # Check for null bytes
        if '\x00' in code:
            return False, "Code contains null bytes"

        return True, None

    @staticmethod
    def validate_language(language: str, supported: List[str]) -> tuple[bool, Optional[str]]:
        """
        Validate language parameter.

        Args:
            language: Language name
            supported: List of supported languages

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(language, str):
            return False, f"Language must be string, got {type(language).__name__}"

        if not language.strip():
            return False, "Language is empty"

        language_lower = language.lower().strip()

        if language_lower not in supported:
            return False, f"Language '{language}' not supported. Available: {', '.join(supported)}"

        return True, None

    @staticmethod
    def sanitize_code(code: str) -> str:
        """
        Sanitize code input.

        Args:
            code: Raw code input

        Returns:
            Sanitized code
        """
        # Remove null bytes
        code = code.replace('\x00', '')

        # Normalize line endings
        code = code.replace('\r\n', '\n').replace('\r', '\n')

        # Remove trailing whitespace from lines
        lines = code.split('\n')
        lines = [line.rstrip() for line in lines]
        code = '\n'.join(lines)

        return code


class CodeHasher:
    """Utility for computing code hashes."""

    @staticmethod
    def compute_hash(code: str, algorithm: str = 'sha256') -> str:
        """
        Compute hash of code.

        Args:
            code: Source code
            algorithm: Hash algorithm (sha256, md5, sha1)

        Returns:
            Hex digest of hash
        """
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()

        hasher.update(code.encode('utf-8'))
        return hasher.hexdigest()

    @staticmethod
    def compute_normalized_hash(code: str) -> str:
        """
        Compute hash of normalized code (whitespace-insensitive).

        Args:
            code: Source code

        Returns:
            Hash of normalized code
        """
        # Remove all whitespace for normalization
        normalized = ''.join(code.split())
        return CodeHasher.compute_hash(normalized)


def time_function(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms
    return wrapper


__all__ = [
    'ParserMetrics',
    'ParserCache',
    'InputValidator',
    'CodeHasher',
    'time_function'
]
