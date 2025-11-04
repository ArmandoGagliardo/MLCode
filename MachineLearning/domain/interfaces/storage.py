"""
Storage Provider Interface
==========================

Defines the contract for storage providers (cloud storage, local filesystem, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pathlib import Path


class IStorageProvider(ABC):
    """
    Interface for storage providers.

    Storage providers handle uploading, downloading, and listing files
    in various storage backends (S3, Backblaze, DigitalOcean, local, etc.).

    Example:
        >>> storage = S3Provider(config)
        >>> storage.connect()
        >>> storage.upload('local/data.json', 'datasets/data.json')
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to storage provider.

        Returns:
            True if connection successful, False otherwise

        Raises:
            StorageError: If connection fails

        Example:
            >>> storage.connect()
            True
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to storage provider.

        Should be called when done with storage operations to free resources.

        Example:
            >>> storage.disconnect()
        """
        pass

    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file from local filesystem to storage.

        Args:
            local_path: Path to local file
            remote_path: Destination path in storage

        Returns:
            True if upload successful, False otherwise

        Raises:
            FileNotFoundError: If local file doesn't exist
            StorageError: If upload fails

        Example:
            >>> storage.upload('/local/data.json', 'datasets/data.json')
            True
        """
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from storage to local filesystem.

        Args:
            remote_path: Path in storage
            local_path: Destination path on local filesystem

        Returns:
            True if download successful, False otherwise

        Raises:
            StorageError: If download fails or file doesn't exist

        Example:
            >>> storage.download('datasets/data.json', '/local/data.json')
            True
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "", recursive: bool = True) -> List[str]:
        """
        List files in storage with optional prefix filter.

        Args:
            prefix: Only list files with this prefix (like a directory path)
            recursive: If True, list all files recursively; if False, only immediate children

        Returns:
            List of file paths in storage

        Example:
            >>> storage.list_files('datasets/')
            ['datasets/python.json', 'datasets/javascript.json']
        """
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            remote_path: Path to file in storage

        Returns:
            True if deletion successful, False otherwise

        Raises:
            StorageError: If deletion fails

        Example:
            >>> storage.delete('datasets/old_data.json')
            True
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            remote_path: Path to check

        Returns:
            True if file exists, False otherwise

        Example:
            >>> storage.exists('datasets/data.json')
            True
        """
        pass

    @abstractmethod
    def get_file_size(self, remote_path: str) -> Optional[int]:
        """
        Get size of file in storage.

        Args:
            remote_path: Path to file

        Returns:
            File size in bytes, or None if file doesn't exist

        Example:
            >>> storage.get_file_size('datasets/data.json')
            1024000
        """
        pass

    @abstractmethod
    def get_metadata(self, remote_path: str) -> Optional[Dict]:
        """
        Get metadata about file in storage.

        Args:
            remote_path: Path to file

        Returns:
            Dictionary with metadata (size, modified_date, etag, etc.)
            or None if file doesn't exist

        Example:
            >>> storage.get_metadata('datasets/data.json')
            {'size': 1024, 'modified': '2025-11-04', 'etag': 'abc123'}
        """
        pass
