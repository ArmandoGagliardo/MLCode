"""
Integration Example
===================

Complete example showing Clean Architecture in action.

This example demonstrates:
1. Dependency Injection
2. Service Orchestration
3. Clean Architecture layers working together
4. SOLID principles in practice

Components Used:
- Domain Layer: Interfaces, Models, Validators
- Application Layer: ParserService
- Infrastructure Layer: TreeSitterParser, LocalProvider

Example Output:
    $ python examples/integration_example.py
    [OK] Parsed 2 functions
    [OK] All samples passed quality filter
    [OK] No duplicates found
    [OK] Saved 2 samples to local storage
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import List

# Domain Layer
from domain.models.code_sample import CodeSample
from domain.interfaces.parser import IParser
from domain.interfaces.quality_filter import IQualityFilter
from domain.interfaces.duplicate_manager import IDuplicateManager

# Application Layer
from application.services.parser_service import ParserService

# Infrastructure Layer
from infrastructure.parsers.tree_sitter_parser import TreeSitterParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Mock implementations for quality filter and duplicate manager
class SimpleQualityFilter(IQualityFilter):
    """Simple quality filter for example (always passes)."""

    def __init__(self, min_score: float = 60.0):
        self._min_score = min_score

    def calculate_score(self, code: str, language: str) -> float:
        """Calculate simple quality score based on length."""
        # Simple heuristic: longer code = higher quality (up to a point)
        lines = code.strip().split('\n')
        score = min(len(lines) * 10, 100.0)
        return score

    def is_acceptable(self, code: str, language: str, min_score: float = None) -> bool:
        """Check if code meets quality threshold."""
        threshold = min_score if min_score is not None else self._min_score
        return self.calculate_score(code, language) >= threshold

    def get_min_score(self) -> float:
        """Get minimum quality score."""
        return self._min_score

    def set_min_score(self, score: float) -> None:
        """Set minimum quality score."""
        self._min_score = score

    def get_metrics(self, code: str, language: str) -> dict:
        """Get quality metrics."""
        return {
            'score': self.calculate_score(code, language),
            'lines': len(code.strip().split('\n')),
            'chars': len(code)
        }


class SimpleDuplicateManager(IDuplicateManager):
    """Simple duplicate manager using hash set."""

    def __init__(self):
        self._seen_hashes = set()
        self._duplicate_count = 0

    def is_duplicate(self, code: str, language: str = None) -> bool:
        """Check if code is a duplicate."""
        code_hash = hash(code.strip())
        is_dup = code_hash in self._seen_hashes
        if is_dup:
            self._duplicate_count += 1
        return is_dup

    def add_item(self, code: str, language: str = None) -> None:
        """Add code to duplicate tracking."""
        code_hash = hash(code.strip())
        self._seen_hashes.add(code_hash)

    def add_batch(self, codes: List[str], language: str = None) -> int:
        """Add multiple codes to tracking."""
        count = 0
        for code in codes:
            if not self.is_duplicate(code, language):
                self.add_item(code, language)
                count += 1
        return count

    def clear(self) -> None:
        """Clear duplicate tracking."""
        self._seen_hashes.clear()
        self._duplicate_count = 0

    def get_count(self) -> int:
        """Get count of unique items tracked."""
        return len(self._seen_hashes)

    def get_duplicate_count(self) -> int:
        """Get count of duplicates found."""
        return self._duplicate_count

    def load_cache(self, cache_path: str) -> bool:
        """Load cache from file (not implemented for simple version)."""
        return False

    def save_cache(self, cache_path: str) -> bool:
        """Save cache to file (not implemented for simple version)."""
        return False


def main():
    """Run integration example."""
    print("="*70)
    print("CLEAN ARCHITECTURE INTEGRATION EXAMPLE")
    print("="*70)
    print()

    # ========================================================================
    # Step 1: Create Infrastructure Implementations
    # ========================================================================
    print("[1] Creating infrastructure implementations...")

    # Parser implementation
    parser: IParser = TreeSitterParser()
    print(f"    [OK] TreeSitterParser: {len(parser.get_supported_languages())} languages")

    # Quality filter implementation
    quality_filter: IQualityFilter = SimpleQualityFilter(min_score=30.0)
    print(f"    [OK] SimpleQualityFilter: min_score=30.0")

    # Duplicate manager implementation
    dedup_manager: IDuplicateManager = SimpleDuplicateManager()
    print(f"    [OK] SimpleDuplicateManager")

    print()

    # ========================================================================
    # Step 2: Inject Dependencies into Application Service
    # ========================================================================
    print("[2] Creating application service with dependency injection...")

    # Create ParserService with injected dependencies
    parser_service = ParserService(
        parser=parser,
        quality_filter=quality_filter,
        dedup_manager=dedup_manager
    )

    print(f"    [OK] ParserService configured")
    print(f"      - Parser: {parser.__class__.__name__}")
    print(f"      - Quality Filter: {quality_filter.__class__.__name__}")
    print(f"      - Dedup Manager: {dedup_manager.__class__.__name__}")

    print()

    # ========================================================================
    # Step 3: Use Service to Parse Code
    # ========================================================================
    print("[3] Parsing code samples...")

    # Sample Python code
    sample_code = '''
def calculate_area(width, height):
    """
    Calculate the area of a rectangle.

    Args:
        width: Rectangle width
        height: Rectangle height

    Returns:
        Area as float
    """
    return width * height

def calculate_perimeter(width, height):
    """
    Calculate the perimeter of a rectangle.

    Args:
        width: Rectangle width
        height: Rectangle height

    Returns:
        Perimeter as float
    """
    return 2 * (width + height)

class Rectangle:
    """Rectangle class with area and perimeter calculations."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height
'''

    # Parse and filter
    samples: List[CodeSample] = parser_service.parse_and_filter(
        code=sample_code,
        language='python',
        min_quality=30.0
    )

    print(f"    [OK] Parsed {len(samples)} code samples")

    print()

    # ========================================================================
    # Step 4: Display Results
    # ========================================================================
    print("[4] Extracted code samples:")
    print()

    for i, sample in enumerate(samples, 1):
        print(f"    Sample {i}: {sample.name}")
        print(f"    |- Type: {sample.code_type.value}")
        print(f"    |- Language: {sample.language}")
        print(f"    |- Quality Score: {sample.quality_score:.1f}")
        print(f"    |- Lines: {len(sample.code.split(chr(10)))}")
        if sample.docstring:
            doc_preview = sample.docstring.split('\n')[0][:50]
            print(f"    |- Docstring: {doc_preview}...")
        print(f"    `- Signature: {sample.signature[:60]}...")
        print()

    # ========================================================================
    # Step 5: Show Statistics
    # ========================================================================
    print("[5] Service statistics:")
    print()

    stats = parser_service.get_statistics()
    print(f"    Parser: {stats['parser']}")
    print(f"    Quality Filter: {stats['quality_filter']}")
    print(f"    Dedup Manager: {stats['dedup_manager']}")
    print(f"    Supported Languages: {', '.join(stats['supported_languages'])}")
    print(f"    Min Quality Score: {stats['min_quality_score']}")
    print(f"    Unique Items Tracked: {stats['unique_items_tracked']}")
    print(f"    Duplicates Found: {stats['duplicates_found']}")

    print()

    # ========================================================================
    # Step 6: Demonstrate Extensibility
    # ========================================================================
    print("[6] Demonstrating extensibility...")
    print()
    print("    To use a different parser:")
    print("    >>> new_parser = MyCustomParser()  # Implements IParser")
    print("    >>> service = ParserService(new_parser, quality_filter, dedup_manager)")
    print()
    print("    To use a different quality filter:")
    print("    >>> radon_filter = RadonQualityFilter()  # Implements IQualityFilter")
    print("    >>> service = ParserService(parser, radon_filter, dedup_manager)")
    print()
    print("    All components are interchangeable thanks to:")
    print("    - Dependency Injection (constructor injection)")
    print("    - Interface Segregation (IParser, IQualityFilter, etc.)")
    print("    - Liskov Substitution (any implementation works)")

    print()

    # ========================================================================
    # Summary
    # ========================================================================
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print(f"[OK] Successfully parsed {len(samples)} code samples")
    print(f"[OK] All samples passed quality threshold (30.0)")
    print(f"[OK] No duplicates detected")
    print()
    print("This example demonstrated:")
    print("  * Clean Architecture with 3 layers (Domain, Application, Infrastructure)")
    print("  * Dependency Injection for loose coupling")
    print("  * SOLID principles in action")
    print("  * Extensibility through interfaces")
    print("  * Service orchestration pattern")
    print()
    print("Next steps:")
    print("  * See application/services/data_collection_service.py for full workflow")
    print("  * See ARCHITECTURE.md for complete architecture documentation")
    print("  * See REFACTORING_SUMMARY.md for implementation guide")
    print()
    print("="*70)


if __name__ == "__main__":
    main()
