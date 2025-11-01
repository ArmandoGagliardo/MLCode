"""
Storage Management Module

Provides cloud storage integration for datasets and model backups.

Supported Providers:
- Backblaze B2
- Wasabi
- Amazon S3
- DigitalOcean Spaces
- Cloudflare R2
- Any S3-compatible storage

Features:
- Automatic dataset download on startup
- Model backup after training
- Incremental sync
- Compression
- Encryption (optional)
- Multiple provider support

Usage:
    from module.storage import StorageManager

    # Initialize with provider
    storage = StorageManager(provider='backblaze')

    # Download datasets
    storage.download_datasets()

    # Backup model after training
    storage.backup_model('models/security_classification')
"""

from .storage_manager import StorageManager
from .base_provider import BaseStorageProvider
from .providers import (
    BackblazeProvider,
    WasabiProvider,
    S3Provider,
    DigitalOceanProvider,
    CloudflareR2Provider,
    create_provider
)

__all__ = [
    'StorageManager',
    'BaseStorageProvider',
    'BackblazeProvider',
    'WasabiProvider',
    'S3Provider',
    'DigitalOceanProvider',
    'CloudflareR2Provider',
    'create_provider',
]
