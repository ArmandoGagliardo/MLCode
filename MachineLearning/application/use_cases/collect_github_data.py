"""
Collect GitHub Data Use Case
=============================

Use case for collecting code samples from GitHub repositories.

This use case orchestrates:
1. Repository fetching from GitHub
2. Code parsing and extraction
3. Quality filtering
4. Duplicate detection
5. Storage persistence
"""

import logging
from typing import Optional
from dataclasses import dataclass

from application.services import DataCollectionService
from domain.models.results import CollectionResult

logger = logging.getLogger(__name__)


@dataclass
class CollectGitHubDataRequest:
    """Request object for GitHub data collection."""
    language: Optional[str] = None
    count: int = 10
    min_stars: Optional[int] = None
    min_quality: float = 60.0
    url: Optional[str] = None
    topic: Optional[str] = None


class CollectGitHubDataUseCase:
    """
    Use case for collecting code samples from GitHub.

    This use case demonstrates the Use Case pattern:
    - Single responsibility: GitHub data collection
    - Dependency injection: Services injected
    - Result object: Returns CollectionResult
    - Error handling: Graceful error handling

    Example:
        >>> service = DataCollectionService(...)
        >>> use_case = CollectGitHubDataUseCase(service)
        >>>
        >>> request = CollectGitHubDataRequest(language='python', count=10)
        >>> result = use_case.execute(request)
        >>>
        >>> if result.success:
        ...     print(f"Collected {result.total_samples} samples")
    """

    def __init__(self, data_collection_service: DataCollectionService):
        """
        Initialize use case with dependencies.

        Args:
            data_collection_service: Service for data collection operations

        Example:
            >>> service = DataCollectionService(fetcher, parser_service, storage)
            >>> use_case = CollectGitHubDataUseCase(service)
        """
        self._data_collection_service = data_collection_service
        logger.debug("CollectGitHubDataUseCase initialized")

    def execute(self, request: CollectGitHubDataRequest) -> CollectionResult:
        """
        Execute the GitHub data collection use case.

        Args:
            request: Collection request parameters

        Returns:
            CollectionResult with statistics and samples

        Example:
            >>> request = CollectGitHubDataRequest(
            ...     language='python',
            ...     count=10,
            ...     min_stars=1000,
            ...     min_quality=70.0
            ... )
            >>> result = use_case.execute(request)
        """
        logger.info(f"Executing CollectGitHubDataUseCase: {request}")

        try:
            # Determine collection mode and execute
            if request.url:
                # Mode 1: Collect from specific URL
                logger.debug(f"Mode: Single URL ({request.url})")
                result = self._data_collection_service.collect_from_url(
                    repo_url=request.url,
                    min_quality=request.min_quality
                )

            elif request.topic:
                # Mode 2: Collect by topic
                logger.debug(f"Mode: By topic ({request.topic})")
                result = self._data_collection_service.collect_from_topic(
                    topic=request.topic,
                    count=request.count,
                    language=request.language,
                    min_quality=request.min_quality
                )

            elif request.language:
                # Mode 3: Collect by language
                logger.debug(f"Mode: By language ({request.language})")
                result = self._data_collection_service.collect_from_language(
                    language=request.language,
                    count=request.count,
                    min_stars=request.min_stars,
                    min_quality=request.min_quality
                )

            else:
                # No valid mode specified
                from domain.exceptions import ValidationError
                raise ValidationError("Must specify language, URL, or topic")

            logger.info(f"Use case completed: {result.total_samples} samples collected")
            return result

        except Exception as e:
            logger.error(f"Use case failed: {e}", exc_info=True)
            # Return failed result instead of raising
            return CollectionResult(
                success=False,
                language=request.language or 'unknown',
                repos_requested=request.count,
                repos_processed=0,
                total_samples=0,
                errors=[str(e)]
            )

    def __str__(self) -> str:
        """String representation."""
        return f"CollectGitHubDataUseCase(service={self._data_collection_service.__class__.__name__})"
