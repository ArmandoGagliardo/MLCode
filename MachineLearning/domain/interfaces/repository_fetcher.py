"""
Repository Fetcher Interface
==============================

Interface for fetching code repositories from various sources (GitHub, GitLab, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from domain.models.repository import Repository


class IRepositoryFetcher(ABC):
    """
    Interface for fetching repositories from code hosting platforms.

    Implementations can fetch from:
    - GitHub (API or web scraping)
    - GitLab
    - Bitbucket
    - Local filesystem

    Example:
        >>> fetcher = GitHubFetcher(api_token='...')
        >>> repos = fetcher.fetch_popular('python', count=10)
        >>> for repo in repos:
        ...     print(f"{repo.name}: {repo.stars} stars")
    """

    @abstractmethod
    def fetch_popular(
        self,
        language: str,
        count: int,
        min_stars: Optional[int] = None,
        **options
    ) -> List[Repository]:
        """
        Fetch popular repositories for a given language.

        Args:
            language: Programming language to filter by
            count: Number of repositories to fetch
            min_stars: Minimum star count (optional)
            **options: Additional platform-specific options:
                - sort_by: 'stars', 'forks', 'updated'
                - time_range: 'day', 'week', 'month', 'year', 'all'
                - topics: List of topics to filter by

        Returns:
            List of Repository objects

        Raises:
            FetchError: If fetching fails
            RateLimitError: If API rate limit is exceeded

        Example:
            >>> repos = fetcher.fetch_popular('python', count=50, min_stars=1000)
            >>> assert len(repos) <= 50
            >>> assert all(r.stars >= 1000 for r in repos)
        """
        pass

    @abstractmethod
    def fetch_by_topic(
        self,
        topic: str,
        count: int,
        language: Optional[str] = None
    ) -> List[Repository]:
        """
        Fetch repositories by topic/tag.

        Args:
            topic: Topic to search for (e.g., 'machine-learning', 'web-framework')
            count: Number of repositories to fetch
            language: Optional language filter

        Returns:
            List of Repository objects

        Example:
            >>> repos = fetcher.fetch_by_topic('machine-learning', count=20, language='python')
        """
        pass

    @abstractmethod
    def fetch_by_url(self, url: str) -> Repository:
        """
        Fetch a single repository by URL.

        Args:
            url: Repository URL

        Returns:
            Repository object

        Raises:
            FetchError: If repository not found or access denied
            ValidationError: If URL is invalid

        Example:
            >>> repo = fetcher.fetch_by_url('https://github.com/django/django')
            >>> assert repo.name == 'django'
        """
        pass

    @abstractmethod
    def fetch_from_user(
        self,
        username: str,
        count: Optional[int] = None
    ) -> List[Repository]:
        """
        Fetch repositories from a specific user/organization.

        Args:
            username: Username or organization name
            count: Maximum number of repositories (None = all)

        Returns:
            List of Repository objects

        Example:
            >>> repos = fetcher.fetch_from_user('django', count=10)
        """
        pass

    @abstractmethod
    def clone_repository(
        self,
        repository: Repository,
        target_path: str,
        depth: Optional[int] = 1
    ) -> bool:
        """
        Clone repository to local filesystem.

        Args:
            repository: Repository object to clone
            target_path: Local path to clone to
            depth: Git clone depth (1 = shallow clone, None = full history)

        Returns:
            True if cloning succeeded, False otherwise

        Raises:
            StorageError: If cloning fails

        Example:
            >>> success = fetcher.clone_repository(repo, '/tmp/repos/django', depth=1)
            >>> assert success
        """
        pass

    @abstractmethod
    def get_rate_limit(self) -> Dict[str, int]:
        """
        Get current API rate limit information.

        Returns:
            Dictionary with rate limit info:
            {
                'limit': int,      # Max requests per hour
                'remaining': int,  # Remaining requests
                'reset_at': int    # Unix timestamp when limit resets
            }

        Example:
            >>> limits = fetcher.get_rate_limit()
            >>> print(f"Remaining: {limits['remaining']}/{limits['limit']}")
        """
        pass

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if this fetcher supports the given language.

        Args:
            language: Programming language

        Returns:
            True if language is supported

        Example:
            >>> assert fetcher.supports_language('python')
        """
        pass
