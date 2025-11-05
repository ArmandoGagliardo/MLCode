"""
GitHub Repository Fetcher
==========================

Concrete implementation of IRepositoryFetcher for GitHub API.
"""

import os
import logging
import subprocess
import requests
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

from domain.interfaces.repository_fetcher import IRepositoryFetcher
from domain.models.repository import Repository
from domain.exceptions import FetchError, RateLimitError, AuthenticationError, ValidationError
from domain.validation.validators import URLValidator
from infrastructure.utils.retry import retry

logger = logging.getLogger(__name__)


class GitHubFetcher(IRepositoryFetcher):
    """
    GitHub API implementation of IRepositoryFetcher.

    Features:
    - GitHub REST API v3 integration
    - Authentication support (token-based)
    - Rate limit handling
    - Retry logic for network failures
    - Repository cloning with git

    Authentication:
        Set GITHUB_TOKEN environment variable for:
        - Higher rate limits (5000/hour vs 60/hour)
        - Access to private repositories
        - Better reliability

    Example:
        >>> fetcher = GitHubFetcher(api_token='ghp_...')
        >>> repos = fetcher.fetch_popular('python', count=10, min_stars=1000)
        >>> for repo in repos:
        ...     print(f"{repo.name}: {repo.stars} stars")
    """

    # GitHub API configuration
    API_BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    # Rate limits
    AUTHENTICATED_RATE_LIMIT = 5000  # per hour
    UNAUTHENTICATED_RATE_LIMIT = 60  # per hour

    # Supported languages (GitHub language identifiers)
    SUPPORTED_LANGUAGES = [
        'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
        'csharp', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
        'scala', 'r', 'matlab', 'shell', 'dart', 'julia', 'haskell'
    ]

    def __init__(self, api_token: Optional[str] = None, timeout: int = 30):
        """
        Initialize GitHub fetcher.

        Args:
            api_token: GitHub personal access token (optional, uses env var if None)
            timeout: Request timeout in seconds

        Example:
            >>> # Use environment variable
            >>> fetcher = GitHubFetcher()
            >>>
            >>> # Or provide token directly
            >>> fetcher = GitHubFetcher(api_token='ghp_...')
        """
        # Get token from parameter or environment
        self._api_token = api_token or os.getenv('GITHUB_TOKEN')
        self._timeout = timeout

        # Setup session
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': self.API_VERSION,
        })

        # Add authentication if token available
        if self._api_token:
            self._session.headers['Authorization'] = f'Bearer {self._api_token}'
            logger.info("GitHubFetcher initialized with authentication")
        else:
            logger.warning(
                "GitHubFetcher initialized WITHOUT authentication. "
                "Rate limit: 60 requests/hour. Set GITHUB_TOKEN for 5000/hour."
            )

        # Cache for rate limit info
        self._rate_limit_cache: Optional[Dict] = None

        logger.debug(f"GitHub API base URL: {self.API_BASE_URL}")
        logger.debug(f"Request timeout: {self._timeout}s")

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def fetch_popular(
        self,
        language: str,
        count: int,
        min_stars: Optional[int] = None,
        **options
    ) -> List[Repository]:
        """
        Fetch popular repositories for a given language.

        Uses GitHub Search API to find repositories sorted by stars.

        Args:
            language: Programming language
            count: Number of repositories to fetch
            min_stars: Minimum star count
            **options:
                - sort_by: 'stars', 'forks', 'updated' (default: 'stars')
                - time_range: 'day', 'week', 'month' (optional)
                - topics: List of topics to filter by

        Returns:
            List of Repository objects

        Raises:
            ValidationError: If inputs invalid
            FetchError: If fetching fails
            RateLimitError: If rate limit exceeded

        Example:
            >>> repos = fetcher.fetch_popular('python', count=50, min_stars=1000)
            >>> assert len(repos) <= 50
            >>> assert all(r.stars >= 1000 for r in repos)
        """
        # Validate inputs
        if not self.supports_language(language):
            raise ValidationError(f"Language '{language}' not supported by GitHub")

        if count <= 0 or count > 1000:
            raise ValidationError("Count must be between 1 and 1000")

        if min_stars is not None and min_stars < 0:
            raise ValidationError("min_stars must be non-negative")

        # Build search query
        query_parts = [f"language:{language}"]

        if min_stars:
            query_parts.append(f"stars:>={min_stars}")

        # Add topics filter
        topics = options.get('topics', [])
        for topic in topics:
            query_parts.append(f"topic:{topic}")

        # Add time range filter
        time_range = options.get('time_range')
        if time_range:
            created_date = self._get_date_for_range(time_range)
            if created_date:
                query_parts.append(f"created:>={created_date}")

        query = " ".join(query_parts)

        # Determine sort order
        sort_by = options.get('sort_by', 'stars')
        if sort_by not in ['stars', 'forks', 'updated']:
            sort_by = 'stars'

        logger.info(f"Searching GitHub: query='{query}', sort={sort_by}, count={count}")

        # Fetch repositories (GitHub API returns max 100 per page)
        all_repos = []
        per_page = min(count, 100)
        pages_needed = (count + per_page - 1) // per_page

        for page in range(1, pages_needed + 1):
            repos = self._search_repositories(
                query=query,
                sort=sort_by,
                per_page=per_page,
                page=page
            )

            all_repos.extend(repos)

            # Stop if we have enough
            if len(all_repos) >= count:
                break

        # Limit to requested count
        result = all_repos[:count]
        logger.info(f"Fetched {len(result)} repositories")

        return result

    def fetch_by_topic(
        self,
        topic: str,
        count: int,
        language: Optional[str] = None
    ) -> List[Repository]:
        """
        Fetch repositories by topic/tag.

        Args:
            topic: Topic to search for
            count: Number of repositories
            language: Optional language filter

        Returns:
            List of Repository objects

        Example:
            >>> repos = fetcher.fetch_by_topic('machine-learning', count=20, language='python')
        """
        # Build query
        query = f"topic:{topic}"
        if language:
            query += f" language:{language}"

        logger.info(f"Fetching repositories by topic: {topic}")

        return self._fetch_by_query(query, count, sort='stars')

    def fetch_by_url(self, url: str) -> Repository:
        """
        Fetch a single repository by URL.

        Args:
            url: Repository URL (e.g., https://github.com/owner/repo)

        Returns:
            Repository object

        Raises:
            ValidationError: If URL invalid
            FetchError: If repository not found

        Example:
            >>> repo = fetcher.fetch_by_url('https://github.com/django/django')
            >>> assert repo.name == 'django'
        """
        # Validate URL
        URLValidator.validate_url(url)

        # Extract owner and repo name
        owner, repo_name = self._parse_github_url(url)

        logger.info(f"Fetching repository: {owner}/{repo_name}")

        # Make API request
        api_url = f"{self.API_BASE_URL}/repos/{owner}/{repo_name}"

        try:
            response = self._session.get(api_url, timeout=self._timeout)
            self._check_rate_limit(response)

            if response.status_code == 404:
                raise FetchError(f"Repository not found: {owner}/{repo_name}")
            elif response.status_code == 403:
                raise AuthenticationError("Access denied. Check token permissions.")

            response.raise_for_status()

            data = response.json()
            return self._parse_repository(data)

        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch repository: {e}")

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
        logger.info(f"Fetching repositories from user: {username}")

        # Build API URL
        api_url = f"{self.API_BASE_URL}/users/{username}/repos"

        all_repos = []
        page = 1
        per_page = 100

        while True:
            try:
                response = self._session.get(
                    api_url,
                    params={'per_page': per_page, 'page': page, 'sort': 'stars'},
                    timeout=self._timeout
                )

                self._check_rate_limit(response)
                response.raise_for_status()

                repos_data = response.json()

                if not repos_data:
                    break

                # Parse repositories
                for repo_data in repos_data:
                    repo = self._parse_repository(repo_data)
                    all_repos.append(repo)

                    # Check if we have enough
                    if count and len(all_repos) >= count:
                        return all_repos[:count]

                page += 1

            except requests.RequestException as e:
                raise FetchError(f"Failed to fetch user repositories: {e}")

        return all_repos[:count] if count else all_repos

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
            True if cloning succeeded

        Raises:
            FetchError: If cloning fails

        Example:
            >>> success = fetcher.clone_repository(repo, '/tmp/repos/django', depth=1)
            >>> assert success
        """
        # Create target directory if needed
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Remove if already exists
        if target.exists():
            import shutil
            shutil.rmtree(target)

        logger.info(f"Cloning {repository.url} to {target_path}")

        # Build git command
        cmd = ['git', 'clone']

        # Add depth for shallow clone
        if depth:
            cmd.extend(['--depth', str(depth)])

        # Add URL and target path
        cmd.extend([repository.url, target_path])

        # Prepare environment with authentication
        env = os.environ.copy()
        if self._api_token:
            # Use token for authentication
            env['GIT_ASKPASS'] = 'echo'
            env['GIT_USERNAME'] = 'x-access-token'
            env['GIT_PASSWORD'] = self._api_token

        try:
            # Run git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                env=env
            )

            if result.returncode != 0:
                error_msg = result.stderr.lower()
                if 'repository not found' in error_msg:
                    raise FetchError(f"Repository not found: {repository.url}")
                elif 'authentication failed' in error_msg:
                    raise AuthenticationError("Git authentication failed")
                else:
                    raise FetchError(f"Git clone failed: {result.stderr}")

            logger.info(f"Successfully cloned {repository.name}")
            return True

        except subprocess.TimeoutExpired:
            raise FetchError(f"Clone timeout for {repository.url}")
        except Exception as e:
            raise FetchError(f"Failed to clone repository: {e}")

    def get_rate_limit(self) -> Dict[str, int]:
        """
        Get current API rate limit information.

        Returns:
            Dictionary with rate limit info

        Example:
            >>> limits = fetcher.get_rate_limit()
            >>> print(f"Remaining: {limits['remaining']}/{limits['limit']}")
        """
        try:
            response = self._session.get(
                f"{self.API_BASE_URL}/rate_limit",
                timeout=self._timeout
            )
            response.raise_for_status()

            data = response.json()
            core_limits = data['resources']['core']

            return {
                'limit': core_limits['limit'],
                'remaining': core_limits['remaining'],
                'reset_at': core_limits['reset'],
            }

        except Exception as e:
            logger.error(f"Failed to get rate limit: {e}")
            # Return cached value if available
            if self._rate_limit_cache:
                return self._rate_limit_cache

            # Return default
            return {
                'limit': self.AUTHENTICATED_RATE_LIMIT if self._api_token else self.UNAUTHENTICATED_RATE_LIMIT,
                'remaining': 0,
                'reset_at': 0,
            }

    def supports_language(self, language: str) -> bool:
        """
        Check if this fetcher supports the given language.

        Args:
            language: Programming language

        Returns:
            True if language is supported

        Example:
            >>> assert fetcher.supports_language('python')
            >>> assert not fetcher.supports_language('cobol')
        """
        return language.lower() in self.SUPPORTED_LANGUAGES

    # Private helper methods

    def _search_repositories(
        self,
        query: str,
        sort: str = 'stars',
        per_page: int = 100,
        page: int = 1
    ) -> List[Repository]:
        """Search repositories using GitHub Search API."""
        api_url = f"{self.API_BASE_URL}/search/repositories"

        params = {
            'q': query,
            'sort': sort,
            'order': 'desc',
            'per_page': per_page,
            'page': page,
        }

        try:
            response = self._session.get(api_url, params=params, timeout=self._timeout)

            # Check rate limit
            self._check_rate_limit(response)

            response.raise_for_status()

            data = response.json()
            items = data.get('items', [])

            # Parse repositories
            return [self._parse_repository(item) for item in items]

        except requests.RequestException as e:
            raise FetchError(f"GitHub search failed: {e}")

    def _fetch_by_query(self, query: str, count: int, sort: str = 'stars') -> List[Repository]:
        """Fetch repositories by search query."""
        all_repos = []
        per_page = min(count, 100)
        pages_needed = (count + per_page - 1) // per_page

        for page in range(1, pages_needed + 1):
            repos = self._search_repositories(query, sort, per_page, page)
            all_repos.extend(repos)

            if len(all_repos) >= count:
                break

        return all_repos[:count]

    def _parse_repository(self, data: Dict) -> Repository:
        """Parse GitHub API response to Repository model."""
        return Repository(
            name=data['name'],
            url=data['html_url'],
            clone_url=data['clone_url'],
            description=data.get('description', ''),
            language=data.get('language', '').lower() if data.get('language') else None,
            stars=data.get('stargazers_count', 0),
            forks=data.get('forks_count', 0),
            owner=data['owner']['login'],
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
        )

    def _parse_github_url(self, url: str) -> tuple:
        """Parse GitHub URL to extract owner and repo name."""
        # Remove trailing .git if present
        url = url.rstrip('/').replace('.git', '')

        # Extract owner and repo
        parts = url.split('github.com/')[-1].split('/')

        if len(parts) < 2:
            raise ValidationError(f"Invalid GitHub URL: {url}")

        return parts[0], parts[1]

    def _check_rate_limit(self, response: requests.Response) -> None:
        """Check rate limit from response headers."""
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset_time = response.headers.get('X-RateLimit-Reset')

        if remaining:
            remaining = int(remaining)
            reset_time = int(reset_time) if reset_time else 0

            # Cache rate limit info
            self._rate_limit_cache = {
                'remaining': remaining,
                'reset_at': reset_time,
            }

            # Warn if low
            if remaining < 10:
                logger.warning(f"GitHub API rate limit low: {remaining} remaining")

            # Raise if exhausted
            if remaining == 0:
                reset_datetime = datetime.fromtimestamp(reset_time)
                raise RateLimitError(
                    f"GitHub API rate limit exceeded. Resets at {reset_datetime}",
                    details={'reset_at': reset_time}
                )

    def _get_date_for_range(self, time_range: str) -> Optional[str]:
        """Get ISO date string for time range filter."""
        from datetime import timedelta

        now = datetime.now()

        ranges = {
            'day': timedelta(days=1),
            'week': timedelta(weeks=1),
            'month': timedelta(days=30),
            'year': timedelta(days=365),
        }

        delta = ranges.get(time_range)
        if not delta:
            return None

        date = now - delta
        return date.strftime('%Y-%m-%d')
