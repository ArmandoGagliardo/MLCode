"""
Data Collection Service
=======================

Application service that orchestrates the collection of code samples from repositories.

This service demonstrates Clean Architecture and SOLID principles by:
- Orchestrating the complete data collection workflow
- Coordinating between fetching, parsing, and storage
- Managing the pipeline: fetch → clone → parse → filter → deduplicate → save
"""

import logging
from typing import List, Optional, Dict
from pathlib import Path
import tempfile
import shutil

from domain.interfaces.repository_fetcher import IRepositoryFetcher
from domain.interfaces.storage import IStorageProvider
from domain.models.repository import Repository
from domain.models.code_sample import CodeSample
from domain.models.results import CollectionResult
from domain.exceptions import FetchError, StorageError, ValidationError
from domain.validation.validators import Validator
from application.services.parser_service import ParserService

logger = logging.getLogger(__name__)


class DataCollectionService:
    """
    Service for orchestrating data collection from code repositories.

    This service demonstrates:
    - Service Orchestration: Coordinates multiple services and components
    - Dependency Injection: All dependencies injected via constructor
    - Single Responsibility: Only orchestrates, doesn't implement low-level logic
    - Open/Closed: Extensible through interface implementations

    Responsibilities:
    1. Fetch repositories from platform (GitHub, etc.)
    2. Clone repositories to local filesystem
    3. Parse code files using ParserService
    4. Save extracted samples to storage
    5. Track statistics and errors
    6. Clean up temporary files

    Workflow:
        Fetch Repos → Clone → Parse Files → Filter Quality → Save → Cleanup

    Example:
        >>> fetcher = GitHubFetcher(api_token='...')
        >>> parser_service = ParserService(parser, quality, dedup)
        >>> storage = LocalProvider(config)
        >>>
        >>> service = DataCollectionService(fetcher, parser_service, storage)
        >>> result = service.collect_from_language('python', count=10)
        >>> print(f"Collected {result.total_samples} samples from {result.repos_processed} repos")
    """

    def __init__(
        self,
        repo_fetcher: IRepositoryFetcher,
        parser_service: ParserService,
        storage_provider: IStorageProvider,
        temp_dir: Optional[str] = None,
        auto_cleanup: bool = True
    ):
        """
        Initialize data collection service with dependencies.

        Args:
            repo_fetcher: Repository fetcher implementation
            parser_service: Parser service for code extraction
            storage_provider: Storage provider for saving datasets
            temp_dir: Temporary directory for cloning (None = system temp)
            auto_cleanup: Automatically delete cloned repos after processing

        Example:
            >>> service = DataCollectionService(
            ...     repo_fetcher=GitHubFetcher(),
            ...     parser_service=ParserService(...),
            ...     storage_provider=LocalProvider(...),
            ...     auto_cleanup=True
            ... )
        """
        self._repo_fetcher = repo_fetcher
        self._parser_service = parser_service
        self._storage_provider = storage_provider
        self._temp_dir = temp_dir or tempfile.mkdtemp(prefix="code_collection_")
        self._auto_cleanup = auto_cleanup

        # Ensure temp directory exists
        Path(self._temp_dir).mkdir(parents=True, exist_ok=True)

        logger.info("DataCollectionService initialized")
        logger.debug(f"Repository Fetcher: {repo_fetcher.__class__.__name__}")
        logger.debug(f"Parser Service: {parser_service.__class__.__name__}")
        logger.debug(f"Storage Provider: {storage_provider.__class__.__name__}")
        logger.debug(f"Temp Directory: {self._temp_dir}")
        logger.debug(f"Auto Cleanup: {auto_cleanup}")

    def collect_from_language(
        self,
        language: str,
        count: int,
        min_stars: Optional[int] = None,
        min_quality: Optional[float] = None,
        max_file_size_mb: int = 10
    ) -> CollectionResult:
        """
        Collect code samples from popular repositories of a given language.

        This is the main workflow method that orchestrates:
        1. Fetch popular repositories
        2. Process each repository
        3. Aggregate results
        4. Return statistics

        Args:
            language: Programming language to collect
            count: Number of repositories to process
            min_stars: Minimum star count for repositories
            min_quality: Minimum quality score for code samples
            max_file_size_mb: Maximum file size to process (in MB)

        Returns:
            CollectionResult with statistics and samples

        Raises:
            ValidationError: If inputs are invalid
            FetchError: If fetching repositories fails

        Example:
            >>> result = service.collect_from_language(
            ...     language='python',
            ...     count=10,
            ...     min_stars=1000,
            ...     min_quality=70.0
            ... )
            >>> print(f"Success: {result.success}")
            >>> print(f"Samples: {result.total_samples}")
            >>> print(f"Errors: {len(result.errors)}")
        """
        # Step 1: Validate inputs
        self._validate_collection_inputs(language, count, min_stars)

        # Step 2: Fetch repositories
        logger.info(f"Fetching {count} {language} repositories (min_stars={min_stars})")
        repositories = self._fetch_repositories(language, count, min_stars)

        if not repositories:
            logger.warning(f"No repositories found for {language}")
            return CollectionResult(
                success=False,
                language=language,
                repos_requested=count,
                repos_processed=0,
                total_samples=0,
                errors=["No repositories found"]
            )

        logger.info(f"Fetched {len(repositories)} repositories")

        # Step 3: Process each repository
        all_samples: List[CodeSample] = []
        processed_count = 0
        errors = []

        for i, repo in enumerate(repositories, 1):
            try:
                logger.info(f"Processing repository {i}/{len(repositories)}: {repo.name}")

                samples = self._process_repository(
                    repository=repo,
                    min_quality=min_quality,
                    max_file_size_mb=max_file_size_mb
                )

                all_samples.extend(samples)
                processed_count += 1

                logger.info(f"✓ {repo.name}: {len(samples)} samples extracted")

            except Exception as e:
                error_msg = f"Failed to process {repo.name}: {e}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        # Step 4: Save to storage
        saved = False
        if all_samples:
            try:
                saved = self._save_samples(all_samples, language)
            except Exception as e:
                error_msg = f"Failed to save samples: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Step 5: Cleanup temp directory
        if self._auto_cleanup:
            self._cleanup_temp_dir()

        # Step 6: Build result
        result = CollectionResult(
            success=processed_count > 0 and saved,
            language=language,
            repos_requested=count,
            repos_processed=processed_count,
            repos_failed=len(repositories) - processed_count,
            total_samples=len(all_samples),
            samples=all_samples,
            errors=errors
        )

        logger.info(
            f"Collection complete: {processed_count}/{len(repositories)} repos, "
            f"{len(all_samples)} samples, {len(errors)} errors"
        )

        return result

    def collect_from_topic(
        self,
        topic: str,
        count: int,
        language: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> CollectionResult:
        """
        Collect code samples from repositories matching a topic.

        Args:
            topic: Topic to search for (e.g., 'machine-learning', 'web-framework')
            count: Number of repositories to process
            language: Optional language filter
            min_quality: Minimum quality score for code samples

        Returns:
            CollectionResult with statistics

        Example:
            >>> result = service.collect_from_topic(
            ...     topic='machine-learning',
            ...     count=20,
            ...     language='python'
            ... )
        """
        # Validate inputs
        Validator.validate_not_empty(topic, "Topic")
        Validator.validate_positive_int(count, "Count")

        # Fetch repositories by topic
        logger.info(f"Fetching {count} repositories for topic '{topic}'")
        repositories = self._repo_fetcher.fetch_by_topic(topic, count, language)

        if not repositories:
            return CollectionResult(
                success=False,
                language=language or 'mixed',
                repos_requested=count,
                repos_processed=0,
                total_samples=0,
                errors=[f"No repositories found for topic: {topic}"]
            )

        # Process repositories (similar to collect_from_language)
        all_samples = []
        processed_count = 0
        errors = []

        for repo in repositories:
            try:
                samples = self._process_repository(repo, min_quality)
                all_samples.extend(samples)
                processed_count += 1
            except Exception as e:
                errors.append(f"Failed to process {repo.name}: {e}")

        # Save and cleanup
        saved = False
        if all_samples:
            saved = self._save_samples(all_samples, language or topic)

        if self._auto_cleanup:
            self._cleanup_temp_dir()

        return CollectionResult(
            success=processed_count > 0 and saved,
            language=language or 'mixed',
            repos_requested=count,
            repos_processed=processed_count,
            total_samples=len(all_samples),
            samples=all_samples,
            errors=errors
        )

    def collect_from_url(
        self,
        repo_url: str,
        min_quality: Optional[float] = None
    ) -> CollectionResult:
        """
        Collect code samples from a single repository URL.

        Args:
            repo_url: Repository URL
            min_quality: Minimum quality score

        Returns:
            CollectionResult with statistics

        Example:
            >>> result = service.collect_from_url(
            ...     'https://github.com/django/django',
            ...     min_quality=70.0
            ... )
        """
        # Validate URL
        Validator.validate_url(repo_url)

        # Fetch repository metadata
        logger.info(f"Fetching repository: {repo_url}")
        repository = self._repo_fetcher.fetch_by_url(repo_url)

        # Process repository
        try:
            samples = self._process_repository(repository, min_quality)

            # Save samples
            saved = False
            if samples:
                saved = self._save_samples(samples, repository.language or 'unknown')

            if self._auto_cleanup:
                self._cleanup_temp_dir()

            return CollectionResult(
                success=True,
                language=repository.language or 'unknown',
                repos_requested=1,
                repos_processed=1,
                total_samples=len(samples),
                samples=samples,
                errors=[]
            )

        except Exception as e:
            error_msg = f"Failed to process {repo_url}: {e}"
            logger.error(error_msg, exc_info=True)

            return CollectionResult(
                success=False,
                language=repository.language or 'unknown',
                repos_requested=1,
                repos_processed=0,
                total_samples=0,
                errors=[error_msg]
            )

    def _validate_collection_inputs(
        self,
        language: str,
        count: int,
        min_stars: Optional[int]
    ) -> None:
        """Validate collection inputs"""
        try:
            Validator.validate_not_empty(language, "Language")
            Validator.validate_positive_int(count, "Count")

            if min_stars is not None:
                Validator.validate_positive_int(min_stars, "Min Stars")

            # Check if fetcher supports language
            if not self._repo_fetcher.supports_language(language):
                raise ValidationError(f"Language '{language}' not supported by fetcher")

        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            raise

    def _fetch_repositories(
        self,
        language: str,
        count: int,
        min_stars: Optional[int]
    ) -> List[Repository]:
        """Fetch repositories from platform"""
        try:
            return self._repo_fetcher.fetch_popular(
                language=language,
                count=count,
                min_stars=min_stars
            )
        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}", exc_info=True)
            raise FetchError(f"Failed to fetch {language} repositories: {e}")

    def _process_repository(
        self,
        repository: Repository,
        min_quality: Optional[float] = None,
        max_file_size_mb: int = 10
    ) -> List[CodeSample]:
        """Process a single repository: clone → parse → filter"""
        # Step 1: Clone repository
        repo_path = self._clone_repository(repository)

        # Step 2: Find code files
        code_files = self._find_code_files(repo_path, repository.language, max_file_size_mb)

        if not code_files:
            logger.warning(f"No code files found in {repository.name}")
            return []

        logger.debug(f"Found {len(code_files)} code files in {repository.name}")

        # Step 3: Parse files and collect samples
        all_samples = []
        for file_path in code_files:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                # Parse and filter using ParserService
                samples = self._parser_service.parse_and_filter(
                    code=code,
                    language=repository.language or self._detect_language(file_path),
                    min_quality=min_quality
                )

                # Add repository metadata to samples
                for sample in samples:
                    sample.file_path = str(file_path)
                    sample.repo_url = repository.url

                all_samples.extend(samples)

            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                continue

        return all_samples

    def _clone_repository(self, repository: Repository) -> str:
        """Clone repository to temp directory"""
        target_path = str(Path(self._temp_dir) / repository.name)

        logger.debug(f"Cloning {repository.url} to {target_path}")

        success = self._repo_fetcher.clone_repository(
            repository=repository,
            target_path=target_path,
            depth=1  # Shallow clone
        )

        if not success:
            raise StorageError(f"Failed to clone repository: {repository.url}")

        return target_path

    def _find_code_files(
        self,
        repo_path: str,
        language: Optional[str],
        max_file_size_mb: int
    ) -> List[str]:
        """Find all code files in repository"""
        code_files = []
        max_size_bytes = max_file_size_mb * 1024 * 1024

        # Extension mapping
        extensions = self._get_extensions_for_language(language)

        # Walk repository
        for file_path in Path(repo_path).rglob('*'):
            # Skip directories
            if not file_path.is_file():
                continue

            # Skip large files
            if file_path.stat().st_size > max_size_bytes:
                continue

            # Check extension
            if file_path.suffix.lower() in extensions:
                code_files.append(str(file_path))

        return code_files

    def _get_extensions_for_language(self, language: Optional[str]) -> List[str]:
        """Get file extensions for a programming language"""
        extension_map = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'c': ['.c', '.h'],
            'csharp': ['.cs'],
            'swift': ['.swift'],
            'kotlin': ['.kt'],
        }

        if language:
            return extension_map.get(language.lower(), [])
        else:
            # Return all extensions if no language specified
            return [ext for exts in extension_map.values() for ext in exts]

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()

        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
        }

        return ext_to_lang.get(ext, 'unknown')

    def _save_samples(self, samples: List[CodeSample], language: str) -> bool:
        """Save collected samples to storage"""
        try:
            # Convert samples to dict for JSON serialization
            samples_data = [sample.to_dict() for sample in samples]

            # Generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"collected_{language}_{timestamp}_{len(samples)}.json"

            # Save to storage
            import json
            import tempfile

            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(samples_data, f, indent=2)
                temp_file = f.name

            # Upload to storage
            remote_path = f"datasets/collected/{filename}"
            success = self._storage_provider.upload(temp_file, remote_path)

            # Cleanup temp file
            Path(temp_file).unlink()

            if success:
                logger.info(f"Saved {len(samples)} samples to {remote_path}")
            else:
                logger.error(f"Failed to save samples to {remote_path}")

            return success

        except Exception as e:
            logger.error(f"Failed to save samples: {e}", exc_info=True)
            raise StorageError(f"Failed to save samples: {e}")

    def _cleanup_temp_dir(self) -> None:
        """Cleanup temporary directory"""
        try:
            if Path(self._temp_dir).exists():
                shutil.rmtree(self._temp_dir)
                logger.debug(f"Cleaned up temp directory: {self._temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")

    def get_statistics(self) -> Dict:
        """Get service statistics"""
        return {
            'repo_fetcher': self._repo_fetcher.__class__.__name__,
            'parser_service': self._parser_service.__class__.__name__,
            'storage_provider': self._storage_provider.__class__.__name__,
            'temp_dir': self._temp_dir,
            'auto_cleanup': self._auto_cleanup,
        }
