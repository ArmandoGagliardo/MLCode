"""
Storage Provider Implementations
=================================

Cloud storage provider implementations for the infrastructure layer.

Available Providers:
-------------------
- LocalProvider: Local filesystem storage
- S3Provider: AWS S3 storage
- DigitalOceanProvider: DigitalOcean Spaces (S3-compatible)
- BackblazeProvider: Backblaze B2 storage
- WasabiProvider: Wasabi cloud storage (S3-compatible)
- CloudflareR2Provider: Cloudflare R2 storage (S3-compatible)

Example:
    >>> from infrastructure.storage.providers import S3Provider
    >>> provider = S3Provider({'bucket_name': 'my-bucket', ...})
    >>> provider.connect()
"""

from infrastructure.storage.providers.local_provider import LocalProvider
from infrastructure.storage.providers.s3_provider import S3Provider
from infrastructure.storage.providers.digitalocean_provider import DigitalOceanProvider
from infrastructure.storage.providers.wasabi_provider import WasabiProvider
from infrastructure.storage.providers.backblaze_provider import BackblazeProvider
from infrastructure.storage.providers.cloudflare_r2_provider import CloudflareR2Provider

__all__ = [
    'LocalProvider',
    'S3Provider',
    'DigitalOceanProvider',
    'WasabiProvider',
    'BackblazeProvider',
    'CloudflareR2Provider',
]
