"""
Dependency Injection Container
===============================

Centralized configuration and dependency management.

This container:
- Creates and wires all dependencies
- Manages component lifecycle
- Provides singleton instances
- Supports configuration injection

Example:
    >>> from config.container import Container
    >>> container = Container()
    >>>
    >>> # Get fully configured service
    >>> parser_service = container.parser_service()
    >>> collection_service = container.data_collection_service()
"""

import os
import logging
from typing import Optional

# Domain Layer
from domain.interfaces.parser import IParser
from domain.interfaces.storage import IStorageProvider
from domain.interfaces.quality_filter import IQualityFilter
from domain.interfaces.duplicate_manager import IDuplicateManager
from domain.interfaces.repository_fetcher import IRepositoryFetcher

# Application Layer
from application.services.parser_service import ParserService
from application.services.data_collection_service import DataCollectionService
from application.services.storage_service import StorageService
from application.services.inference_service import InferenceService

# Infrastructure Layer
from infrastructure.parsers.tree_sitter_parser import TreeSitterParser
from infrastructure.quality.heuristic_quality_filter import HeuristicQualityFilter
from infrastructure.duplicate.ast_duplicate_manager import ASTDuplicateManager
from infrastructure.github.github_fetcher import GitHubFetcher
# Storage providers are now created via StorageFactory

logger = logging.getLogger(__name__)


class Container:
    """
    Dependency Injection Container.

    Manages creation and wiring of all application components.
    Implements singleton pattern for services.

    Example:
        >>> container = Container()
        >>> service = container.parser_service()
        >>> # Service is fully wired with all dependencies
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize container with optional configuration.

        Args:
            config: Configuration dictionary (uses env vars if None)

        Example:
            >>> container = Container({'min_quality': 70.0})
        """
        self._config = config or self._load_config_from_env()
        self._instances = {}  # Singleton cache

        logger.debug("DI Container initialized")

    def _load_config_from_env(self) -> dict:
        """Load configuration from environment variables."""
        return {
            # GitHub
            'github_token': os.getenv('GITHUB_TOKEN'),

            # Local storage
            'storage_base_path': os.getenv('STORAGE_PATH', 'data/storage'),
            'cache_path': os.getenv('CACHE_PATH', 'data/cache'),
            'temp_dir': os.getenv('TEMP_DIR', 'data/temp'),

            # Storage provider selection
            'storage_provider': os.getenv('STORAGE_PROVIDER', 'local'),

            # AWS S3
            'aws_bucket_name': os.getenv('AWS_BUCKET_NAME'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),

            # DigitalOcean Spaces
            'do_spaces_name': os.getenv('DO_SPACES_NAME'),
            'do_spaces_key': os.getenv('DO_SPACES_KEY'),
            'do_spaces_secret': os.getenv('DO_SPACES_SECRET'),
            'do_spaces_region': os.getenv('DO_SPACES_REGION', 'nyc3'),

            # Wasabi
            'wasabi_bucket': os.getenv('WASABI_BUCKET'),
            'wasabi_access_key': os.getenv('WASABI_ACCESS_KEY'),
            'wasabi_secret_key': os.getenv('WASABI_SECRET_KEY'),
            'wasabi_region': os.getenv('WASABI_REGION', 'us-east-1'),

            # Backblaze B2
            'backblaze_bucket': os.getenv('BACKBLAZE_BUCKET'),
            'backblaze_key_id': os.getenv('BACKBLAZE_KEY_ID'),
            'backblaze_application_key': os.getenv('BACKBLAZE_APPLICATION_KEY'),
            'backblaze_endpoint': os.getenv('BACKBLAZE_ENDPOINT'),

            # Cloudflare R2
            'cloudflare_r2_bucket': os.getenv('CLOUDFLARE_R2_BUCKET'),
            'cloudflare_r2_account_id': os.getenv('CLOUDFLARE_R2_ACCOUNT_ID'),
            'cloudflare_r2_access_key': os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
            'cloudflare_r2_secret_key': os.getenv('CLOUDFLARE_R2_SECRET_KEY'),

            # Quality settings
            'min_quality_score': float(os.getenv('MIN_QUALITY_SCORE', '60.0')),
        }

    # ========================================================================
    # Infrastructure Layer - Implementations
    # ========================================================================

    def parser(self) -> IParser:
        """
        Get parser instance (TreeSitterParser).

        Returns:
            IParser implementation

        Example:
            >>> parser = container.parser()
            >>> results = parser.parse(code, 'python')
        """
        if 'parser' not in self._instances:
            self._instances['parser'] = TreeSitterParser()
            logger.debug("Created TreeSitterParser instance")
        return self._instances['parser']

    def quality_filter(self) -> IQualityFilter:
        """
        Get quality filter instance (HeuristicQualityFilter).

        Returns:
            IQualityFilter implementation

        Example:
            >>> filter = container.quality_filter()
            >>> score = filter.calculate_score(code, 'python')
        """
        if 'quality_filter' not in self._instances:
            min_score = self._config.get('min_quality_score', 60.0)
            self._instances['quality_filter'] = HeuristicQualityFilter(min_score=min_score)
            logger.debug(f"Created HeuristicQualityFilter (min_score={min_score})")
        return self._instances['quality_filter']

    def duplicate_manager(self) -> IDuplicateManager:
        """
        Get duplicate manager instance (ASTDuplicateManager).

        Returns:
            IDuplicateManager implementation

        Example:
            >>> dedup = container.duplicate_manager()
            >>> is_dup = dedup.is_duplicate(code, 'python')
        """
        if 'duplicate_manager' not in self._instances:
            cache_path = self._config.get('cache_path')
            if cache_path:
                cache_path = f"{cache_path}/duplicates.json"
            self._instances['duplicate_manager'] = ASTDuplicateManager(cache_path=cache_path)
            logger.debug(f"Created ASTDuplicateManager (cache={cache_path})")
        return self._instances['duplicate_manager']

    def repository_fetcher(self) -> IRepositoryFetcher:
        """
        Get repository fetcher instance (GitHubFetcher).

        Returns:
            IRepositoryFetcher implementation

        Example:
            >>> fetcher = container.repository_fetcher()
            >>> repos = fetcher.fetch_popular('python', count=10)
        """
        if 'repository_fetcher' not in self._instances:
            github_token = self._config.get('github_token')
            self._instances['repository_fetcher'] = GitHubFetcher(api_token=github_token)
            logger.debug(f"Created GitHubFetcher (authenticated={bool(github_token)})")
        return self._instances['repository_fetcher']

    def storage_provider(self) -> IStorageProvider:
        """
        Get storage provider instance.

        Creates provider based on STORAGE_PROVIDER environment variable.
        Supports: local, s3, digitalocean, wasabi, backblaze, cloudflare.

        Returns:
            IStorageProvider implementation

        Example:
            >>> # Local storage (default)
            >>> storage = container.storage_provider()
            >>>
            >>> # S3 storage (set STORAGE_PROVIDER=s3 in env)
            >>> storage = container.storage_provider()
            >>> storage.upload(local_path, remote_path)
        """
        if 'storage_provider' not in self._instances:
            from infrastructure.storage.storage_factory import StorageProviderFactory

            provider_type = self._config.get('storage_provider', 'local').lower()

            # Build configuration based on provider type
            if provider_type == 'local':
                config = {
                    'provider_type': 'local',
                    'base_path': self._config.get('storage_base_path', 'data/storage')
                }
            elif provider_type in ['s3', 'aws']:
                config = {
                    'provider_type': 's3',
                    'bucket_name': self._config.get('aws_bucket_name'),
                    'access_key_id': self._config.get('aws_access_key_id'),
                    'secret_access_key': self._config.get('aws_secret_access_key'),
                    'region': self._config.get('aws_region', 'us-east-1')
                }
            elif provider_type in ['digitalocean', 'do', 'spaces']:
                config = {
                    'provider_type': 'digitalocean',
                    'bucket_name': self._config.get('do_spaces_name'),
                    'access_key_id': self._config.get('do_spaces_key'),
                    'secret_access_key': self._config.get('do_spaces_secret'),
                    'region': self._config.get('do_spaces_region', 'nyc3')
                }
            elif provider_type == 'wasabi':
                config = {
                    'provider_type': 'wasabi',
                    'bucket_name': self._config.get('wasabi_bucket'),
                    'access_key_id': self._config.get('wasabi_access_key'),
                    'secret_access_key': self._config.get('wasabi_secret_key'),
                    'region': self._config.get('wasabi_region', 'us-east-1')
                }
            elif provider_type in ['backblaze', 'b2']:
                config = {
                    'provider_type': 'backblaze',
                    'bucket_name': self._config.get('backblaze_bucket'),
                    'key_id': self._config.get('backblaze_key_id'),
                    'application_key': self._config.get('backblaze_application_key'),
                    'endpoint_url': self._config.get('backblaze_endpoint')
                }
            elif provider_type in ['cloudflare', 'r2', 'cloudflare_r2']:
                config = {
                    'provider_type': 'cloudflare',
                    'bucket_name': self._config.get('cloudflare_r2_bucket'),
                    'account_id': self._config.get('cloudflare_r2_account_id'),
                    'access_key_id': self._config.get('cloudflare_r2_access_key'),
                    'secret_access_key': self._config.get('cloudflare_r2_secret_key')
                }
            else:
                logger.warning(f"Unknown provider type '{provider_type}', using local")
                config = {
                    'provider_type': 'local',
                    'base_path': self._config.get('storage_base_path', 'data/storage')
                }

            self._instances['storage_provider'] = StorageProviderFactory.create(config)
            logger.debug(f"Created {provider_type} storage provider via factory")

        return self._instances['storage_provider']

    # ========================================================================
    # Application Layer - Services
    # ========================================================================

    def parser_service(self) -> ParserService:
        """
        Get parser service with all dependencies injected.

        Returns:
            Fully configured ParserService

        Example:
            >>> service = container.parser_service()
            >>> samples = service.parse_and_filter(code, 'python')
        """
        if 'parser_service' not in self._instances:
            self._instances['parser_service'] = ParserService(
                parser=self.parser(),
                quality_filter=self.quality_filter(),
                dedup_manager=self.duplicate_manager()
            )
            logger.debug("Created ParserService with injected dependencies")
        return self._instances['parser_service']

    def data_collection_service(self) -> DataCollectionService:
        """
        Get data collection service with all dependencies injected.

        Returns:
            Fully configured DataCollectionService

        Example:
            >>> service = container.data_collection_service()
            >>> result = service.collect_from_language('python', count=10)
        """
        if 'data_collection_service' not in self._instances:
            temp_dir = self._config.get('temp_dir', 'data/temp')
            self._instances['data_collection_service'] = DataCollectionService(
                repo_fetcher=self.repository_fetcher(),
                parser_service=self.parser_service(),
                storage_provider=self.storage_provider(),
                temp_dir=temp_dir,
                auto_cleanup=True
            )
            logger.debug("Created DataCollectionService with injected dependencies")
        return self._instances['data_collection_service']

    def storage_service(self) -> StorageService:
        """
        Get storage service with dependencies injected.

        Returns:
            Fully configured StorageService

        Example:
            >>> service = container.storage_service()
            >>> service.upload_dataset(local_path, 'my_dataset')
        """
        if 'storage_service' not in self._instances:
            self._instances['storage_service'] = StorageService(
                provider=self.storage_provider()
            )
            logger.debug("Created StorageService with injected dependencies")
        return self._instances['storage_service']

    def inference_service(self, device: Optional[str] = None) -> InferenceService:
        """
        Get inference service for model inference operations.

        Args:
            device: Optional device override ('cuda', 'cpu')

        Returns:
            Fully configured InferenceService

        Example:
            >>> service = container.inference_service(device='cuda')
            >>> service.load_text_classifier('models/classifier')
            >>> result = service.classify_text("def example(): pass")
        """
        # InferenceService is not singleton because device can change
        # Use key based on device
        key = f'inference_service_{device or "auto"}'
        if key not in self._instances:
            self._instances[key] = InferenceService(device=device)
            logger.debug(f"Created InferenceService (device={device or 'auto'})")
        return self._instances[key]

    # ========================================================================
    # Application Layer - Use Cases
    # ========================================================================

    def collect_github_data_use_case(self):
        """
        Get GitHub data collection use case.

        Returns:
            CollectGitHubDataUseCase with dependencies

        Example:
            >>> use_case = container.collect_github_data_use_case()
            >>> result = use_case.execute(request)
        """
        from application.use_cases import CollectGitHubDataUseCase

        if 'collect_github_data_use_case' not in self._instances:
            self._instances['collect_github_data_use_case'] = CollectGitHubDataUseCase(
                data_collection_service=self.data_collection_service()
            )
            logger.debug("Created CollectGitHubDataUseCase")
        return self._instances['collect_github_data_use_case']

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self):
        """Reset container, clearing all instances."""
        self._instances.clear()
        logger.debug("Container reset")

    def get_config(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)

    def set_config(self, key: str, value):
        """Set configuration value."""
        self._config[key] = value
        # Clear affected instances
        self._instances.clear()
        logger.debug(f"Config updated: {key}={value}, instances cleared")

    def __repr__(self) -> str:
        """String representation."""
        return f"Container(instances={len(self._instances)}, config_keys={list(self._config.keys())})"


# Global container instance (optional convenience)
_global_container = None


def get_container(config: Optional[dict] = None) -> Container:
    """
    Get global container instance.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        Container instance

    Example:
        >>> container = get_container()
        >>> service = container.parser_service()
    """
    global _global_container
    if _global_container is None:
        _global_container = Container(config)
    return _global_container


def reset_container():
    """Reset global container."""
    global _global_container
    if _global_container:
        _global_container.reset()
    _global_container = None
