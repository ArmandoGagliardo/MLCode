"""
Storage Service
===============

High-level storage operations with additional business logic.
"""

import logging
from pathlib import Path
from typing import List, Optional
from domain.interfaces.storage import IStorageProvider
from domain.exceptions import StorageError, ValidationError
from domain.validation.validators import PathValidator

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for high-level storage operations.

    Provides convenient methods for common storage tasks with:
    - Validation
    - Error handling
    - Logging
    - Business logic

    Example:
        >>> provider = LocalProvider(config)
        >>> service = StorageService(provider)
        >>> service.upload_dataset('local/data.json', 'datasets/python.json')
        True
    """

    def __init__(self, provider: IStorageProvider):
        """
        Initialize storage service.

        Args:
            provider: Storage provider implementation
        """
        self._provider = provider
        self._connected = False
        logger.info(f"StorageService initialized with {provider.__class__.__name__}")

    def connect(self) -> bool:
        """
        Connect to storage provider.

        Returns:
            True if connection successful

        Raises:
            StorageError: If connection fails
        """
        if self._connected:
            logger.debug("Already connected")
            return True

        self._connected = self._provider.connect()
        return self._connected

    def disconnect(self) -> None:
        """Disconnect from storage provider"""
        if self._connected:
            self._provider.disconnect()
            self._connected = False

    def upload_dataset(self, local_path: str, dataset_name: str) -> bool:
        """
        Upload dataset with validation.

        Args:
            local_path: Path to local dataset file
            dataset_name: Name for remote dataset

        Returns:
            True if upload successful

        Raises:
            ValidationError: If file doesn't exist or is invalid
            StorageError: If upload fails

        Example:
            >>> service.upload_dataset('data.json', 'python_functions')
            True
        """
        # Validate
        PathValidator.validate_path(local_path, must_exist=True)

        if not Path(local_path).is_file():
            raise ValidationError(f"Not a file: {local_path}")

        # Construct remote path
        remote_path = f"datasets/{dataset_name}"

        # Upload
        logger.info(f"Uploading dataset: {local_path} -> {remote_path}")
        result = self._provider.upload(local_path, remote_path)

        if result:
            size = self._provider.get_file_size(remote_path)
            logger.info(f"Upload successful: {size} bytes")

        return result

    def download_dataset(self, dataset_name: str, local_path: str) -> bool:
        """
        Download dataset with validation.

        Args:
            dataset_name: Name of remote dataset
            local_path: Where to save locally

        Returns:
            True if download successful

        Raises:
            StorageError: If dataset doesn't exist or download fails

        Example:
            >>> service.download_dataset('python_functions', 'data/dataset.json')
            True
        """
        remote_path = f"datasets/{dataset_name}"

        # Check exists
        if not self._provider.exists(remote_path):
            raise StorageError(
                f"Dataset not found: {dataset_name}",
                details={'remote_path': remote_path}
            )

        # Download
        logger.info(f"Downloading dataset: {remote_path} -> {local_path}")
        result = self._provider.download(remote_path, local_path)

        if result:
            size = Path(local_path).stat().st_size
            logger.info(f"Download successful: {size} bytes")

        return result

    def list_datasets(self) -> List[str]:
        """
        List available datasets.

        Returns:
            List of dataset names

        Example:
            >>> service.list_datasets()
            ['python_functions', 'javascript_classes', ...]
        """
        files = self._provider.list_files(prefix="datasets/")

        # Extract dataset names (remove 'datasets/' prefix)
        datasets = []
        for file in files:
            if file.startswith('datasets/'):
                name = file.replace('datasets/', '', 1)
                datasets.append(name)

        logger.debug(f"Found {len(datasets)} datasets")
        return datasets

    def upload_model(self, local_path: str, model_name: str) -> bool:
        """
        Upload trained model.

        Args:
            local_path: Path to local model directory/file
            model_name: Name for remote model

        Returns:
            True if upload successful
        """
        remote_path = f"models/{model_name}"
        logger.info(f"Uploading model: {local_path} -> {remote_path}")
        return self._provider.upload(local_path, remote_path)

    def download_model(self, model_name: str, local_path: str) -> bool:
        """
        Download trained model.

        Args:
            model_name: Name of remote model
            local_path: Where to save locally

        Returns:
            True if download successful
        """
        remote_path = f"models/{model_name}"
        logger.info(f"Downloading model: {remote_path} -> {local_path}")
        return self._provider.download(remote_path, local_path)

    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file paths

        Example:
            >>> service.list_files('datasets/python/')
            ['datasets/python/file1.json', 'datasets/python/file2.json']
        """
        return self._provider.list_files(prefix=prefix)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from storage.

        Args:
            remote_path: Remote file path
            local_path: Local destination path

        Returns:
            True if download successful

        Raises:
            StorageError: If download fails
        """
        logger.info(f"Downloading file: {remote_path} -> {local_path}")
        return self._provider.download(remote_path, local_path)

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to storage.

        Args:
            local_path: Local file path
            remote_path: Remote destination path

        Returns:
            True if upload successful

        Raises:
            ValidationError: If file doesn't exist
            StorageError: If upload fails
        """
        PathValidator.validate_path(local_path, must_exist=True)
        logger.info(f"Uploading file: {local_path} -> {remote_path}")
        return self._provider.upload(local_path, remote_path)

    def get_file_info(self, remote_path: str) -> Optional[dict]:
        """
        Get file information.

        Args:
            remote_path: Remote file path

        Returns:
            Dictionary with file info (size, modified, etc.) or None

        Example:
            >>> info = service.get_file_info('datasets/python/data.json')
            >>> print(f"Size: {info['size']} bytes")
        """
        try:
            size = self._provider.get_file_size(remote_path)
            exists = self._provider.exists(remote_path)

            if not exists:
                return None

            return {
                'path': remote_path,
                'size': size,
                'exists': exists
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_path}: {e}")
            return None

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats

        Example:
            >>> stats = service.get_storage_stats()
            >>> stats['total_datasets']
            15
        """
        datasets = self.list_datasets()

        # Calculate total size
        total_size = 0
        for dataset in datasets:
            size = self._provider.get_file_size(f"datasets/{dataset}")
            if size:
                total_size += size

        return {
            'total_datasets': len(datasets),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'connected': self._connected,
            'provider': self._provider.__class__.__name__,
        }

    @property
    def provider(self) -> str:
        """Get provider name (for compatibility with old code)."""
        return self._provider.__class__.__name__

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
