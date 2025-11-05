"""
Storage Provider Factory
=========================

Factory for creating storage provider instances based on configuration.
Implements the Factory Pattern for extensibility.
"""

import logging
from typing import Dict, Type, Optional
from domain.interfaces.storage import IStorageProvider
from domain.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class StorageProviderFactory:
    """
    Factory for creating storage provider instances.

    This factory implements the Factory Pattern to:
    - Decouple client code from concrete provider classes
    - Allow easy addition of new providers
    - Centralize provider instantiation logic

    Usage:
        # 1. Register providers
        StorageProviderFactory.register('s3', S3Provider)
        StorageProviderFactory.register('local', LocalProvider)

        # 2. Create instances
        config = {'provider_type': 's3', 'bucket': 'my-bucket', ...}
        provider = StorageProviderFactory.create(config)

    Example:
        >>> from infrastructure.storage.providers.local import LocalProvider
        >>> StorageProviderFactory.register('local', LocalProvider)
        >>> config = {'provider_type': 'local', 'base_path': '/data'}
        >>> provider = StorageProviderFactory.create(config)
        >>> provider.connect()
        True
    """

    _providers: Dict[str, Type[IStorageProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[IStorageProvider]) -> None:
        """
        Register a storage provider implementation.

        Args:
            name: Provider name (e.g., 's3', 'digitalocean', 'local')
            provider_class: Provider class that implements IStorageProvider

        Raises:
            ValueError: If name is empty or provider_class doesn't implement IStorageProvider

        Example:
            >>> StorageProviderFactory.register('s3', S3Provider)
            >>> StorageProviderFactory.register('local', LocalProvider)
        """
        if not name:
            raise ValueError("Provider name cannot be empty")

        if not issubclass(provider_class, IStorageProvider):
            raise ValueError(
                f"Provider class must implement IStorageProvider, "
                f"got {provider_class.__name__}"
            )

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered storage provider: {name} -> {provider_class.__name__}")

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a storage provider.

        Args:
            name: Provider name to unregister

        Example:
            >>> StorageProviderFactory.unregister('s3')
        """
        if name.lower() in cls._providers:
            del cls._providers[name.lower()]
            logger.info(f"Unregistered storage provider: {name}")

    @classmethod
    def create(cls, config: Dict) -> IStorageProvider:
        """
        Create storage provider instance from configuration.

        Args:
            config: Configuration dictionary with at minimum:
                - provider_type: str - Type of provider (s3, local, etc.)
                Additional keys depend on provider type.

        Returns:
            Configured storage provider instance

        Raises:
            ConfigurationError: If provider_type missing or provider not registered
            Exception: If provider instantiation fails

        Example:
            >>> config = {
            ...     'provider_type': 'local',
            ...     'base_path': '/data/storage',
            ...     'create_dirs': True
            ... }
            >>> provider = StorageProviderFactory.create(config)
        """
        provider_type = config.get('provider_type', '').lower()

        if not provider_type:
            raise ConfigurationError(
                "Configuration must include 'provider_type'",
                details={'available_providers': list(cls._providers.keys())}
            )

        provider_class = cls._providers.get(provider_type)

        if not provider_class:
            available = ', '.join(cls._providers.keys())
            raise ConfigurationError(
                f"Unknown storage provider: {provider_type}",
                details={
                    'requested': provider_type,
                    'available': list(cls._providers.keys())
                }
            )

        try:
            logger.info(f"Creating {provider_type} storage provider")
            instance = provider_class(config)
            logger.debug(f"Created {provider_class.__name__} instance")
            return instance

        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}", exc_info=True)
            raise ConfigurationError(
                f"Failed to instantiate {provider_type} provider: {e}",
                details={'provider_type': provider_type, 'error': str(e)}
            )

    @classmethod
    def get_registered_providers(cls) -> list:
        """
        Get list of registered provider names.

        Returns:
            List of provider names

        Example:
            >>> StorageProviderFactory.get_registered_providers()
            ['s3', 'digitalocean', 'backblaze', 'local']
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider name to check

        Returns:
            True if registered, False otherwise

        Example:
            >>> StorageProviderFactory.is_registered('s3')
            True
        """
        return name.lower() in cls._providers

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered providers (mainly for testing).

        Example:
            >>> StorageProviderFactory.clear()
            >>> StorageProviderFactory.get_registered_providers()
            []
        """
        cls._providers.clear()
        logger.info("Cleared all registered storage providers")


# Auto-register built-in providers when available
def _auto_register_providers():
    """Auto-register available storage providers"""
    # Local provider
    try:
        from infrastructure.storage.providers.local_provider import LocalProvider
        StorageProviderFactory.register('local', LocalProvider)
    except ImportError:
        logger.debug("LocalProvider not available")

    # AWS S3 provider
    try:
        from infrastructure.storage.providers.s3_provider import S3Provider
        StorageProviderFactory.register('s3', S3Provider)
        StorageProviderFactory.register('aws', S3Provider)  # Alias
    except ImportError:
        logger.debug("S3Provider not available")

    # DigitalOcean Spaces provider
    try:
        from infrastructure.storage.providers.digitalocean_provider import DigitalOceanProvider
        StorageProviderFactory.register('digitalocean', DigitalOceanProvider)
        StorageProviderFactory.register('do', DigitalOceanProvider)  # Alias
        StorageProviderFactory.register('spaces', DigitalOceanProvider)  # Alias
    except ImportError:
        logger.debug("DigitalOceanProvider not available")

    # Wasabi provider
    try:
        from infrastructure.storage.providers.wasabi_provider import WasabiProvider
        StorageProviderFactory.register('wasabi', WasabiProvider)
    except ImportError:
        logger.debug("WasabiProvider not available")

    # Backblaze B2 provider
    try:
        from infrastructure.storage.providers.backblaze_provider import BackblazeProvider
        StorageProviderFactory.register('backblaze', BackblazeProvider)
        StorageProviderFactory.register('b2', BackblazeProvider)  # Alias
    except ImportError:
        logger.debug("BackblazeProvider not available")

    # Cloudflare R2 provider
    try:
        from infrastructure.storage.providers.cloudflare_r2_provider import CloudflareR2Provider
        StorageProviderFactory.register('cloudflare', CloudflareR2Provider)
        StorageProviderFactory.register('r2', CloudflareR2Provider)  # Alias
        StorageProviderFactory.register('cloudflare_r2', CloudflareR2Provider)  # Alias
    except ImportError:
        logger.debug("CloudflareR2Provider not available")


# Auto-register on module load
_auto_register_providers()
