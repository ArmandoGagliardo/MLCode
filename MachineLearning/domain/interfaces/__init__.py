"""
Domain Interfaces
=================

Abstract Base Classes (ABC) that define contracts for implementations.

These interfaces follow the Dependency Inversion Principle:
high-level modules depend on abstractions, not concrete implementations.
"""

from domain.interfaces.parser import IParser
from domain.interfaces.storage import IStorageProvider
from domain.interfaces.quality_filter import IQualityFilter
from domain.interfaces.duplicate_manager import IDuplicateManager
from domain.interfaces.repository_fetcher import IRepositoryFetcher

__all__ = [
    'IParser',
    'IStorageProvider',
    'IQualityFilter',
    'IDuplicateManager',
    'IRepositoryFetcher',
]
