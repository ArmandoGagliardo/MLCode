"""
Storage Providers

Implementations for various cloud storage providers.
"""

from .backblaze import BackblazeProvider
from .wasabi import WasabiProvider
from .s3 import S3Provider
from .digitalocean import DigitalOceanProvider
from .cloudflare_r2 import CloudflareR2Provider

__all__ = [
    'BackblazeProvider',
    'WasabiProvider',
    'S3Provider',
    'DigitalOceanProvider',
    'CloudflareR2Provider',
]


# Provider factory
def create_provider(provider_type: str, **kwargs):
    """
    Factory function to create storage provider instances

    Args:
        provider_type: Type of provider ('backblaze', 'wasabi', 's3', 'digitalocean', 'cloudflare_r2')
        **kwargs: Provider-specific configuration

    Returns:
        Provider instance

    Raises:
        ValueError: If provider type is unknown
    """
    providers = {
        'backblaze': BackblazeProvider,
        'wasabi': WasabiProvider,
        's3': S3Provider,
        'aws': S3Provider,  # Alias
        'digitalocean': DigitalOceanProvider,
        'do': DigitalOceanProvider,  # Alias
        'cloudflare_r2': CloudflareR2Provider,
        'r2': CloudflareR2Provider,  # Alias
    }

    provider_class = providers.get(provider_type.lower())

    if provider_class is None:
        available = ', '.join(providers.keys())
        raise ValueError(f"Unknown provider type: {provider_type}. Available: {available}")

    return provider_class(**kwargs)
