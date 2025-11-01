"""
Base Storage Provider

Abstract base class for all storage providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseStorageProvider(ABC):
    """Abstract base class for storage providers"""

    def __init__(self, bucket_name: str, **config):
        """
        Initialize storage provider

        Args:
            bucket_name: Name of the bucket/container
            **config: Provider-specific configuration
        """
        self.bucket_name = bucket_name
        self.config = config
        self.client = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to storage provider

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Upload a file to storage

        Args:
            local_path: Local file path
            remote_path: Remote file path in bucket
            metadata: Optional metadata dict

        Returns:
            True if upload successful
        """
        pass

    @abstractmethod
    def download_file(
        self,
        remote_path: str,
        local_path: str
    ) -> bool:
        """
        Download a file from storage

        Args:
            remote_path: Remote file path in bucket
            local_path: Local destination path

        Returns:
            True if download successful
        """
        pass

    @abstractmethod
    def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[Dict]:
        """
        List files in bucket

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file info dicts
        """
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from storage

        Args:
            remote_path: Remote file path

        Returns:
            True if deletion successful
        """
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in storage

        Args:
            remote_path: Remote file path

        Returns:
            True if file exists
        """
        pass

    def upload_directory(
        self,
        local_dir: str,
        remote_prefix: str,
        recursive: bool = True
    ) -> List[str]:
        """
        Upload entire directory

        Args:
            local_dir: Local directory path
            remote_prefix: Remote prefix path
            recursive: Include subdirectories

        Returns:
            List of uploaded file paths
        """
        local_path = Path(local_dir)
        uploaded = []

        if not local_path.exists():
            logger.error(f"Directory not found: {local_dir}")
            return uploaded

        # Get all files
        if recursive:
            files = local_path.rglob('*')
        else:
            files = local_path.glob('*')

        for file_path in files:
            if file_path.is_file():
                # Calculate relative path
                rel_path = file_path.relative_to(local_path)
                remote_path = f"{remote_prefix}/{rel_path}".replace('\\', '/')

                logger.info(f"Uploading: {file_path} -> {remote_path}")

                if self.upload_file(str(file_path), remote_path):
                    uploaded.append(str(file_path))
                else:
                    logger.error(f"Failed to upload: {file_path}")

        return uploaded

    def download_directory(
        self,
        remote_prefix: str,
        local_dir: str
    ) -> List[str]:
        """
        Download entire directory

        Args:
            remote_prefix: Remote prefix path
            local_dir: Local destination directory

        Returns:
            List of downloaded file paths
        """
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        downloaded = []

        # List all files with prefix
        files = self.list_files(prefix=remote_prefix)

        for file_info in files:
            remote_path = file_info['key']

            # Calculate local path
            rel_path = remote_path[len(remote_prefix):].lstrip('/')
            local_file = local_path / rel_path

            # Create parent directories
            local_file.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading: {remote_path} -> {local_file}")

            if self.download_file(remote_path, str(local_file)):
                downloaded.append(str(local_file))
            else:
                logger.error(f"Failed to download: {remote_path}")

        return downloaded

    def sync_directory(
        self,
        local_dir: str,
        remote_prefix: str,
        direction: str = 'upload'
    ) -> Dict[str, int]:
        """
        Sync directory (upload or download only changed files)

        Args:
            local_dir: Local directory path
            remote_prefix: Remote prefix path
            direction: 'upload' or 'download'

        Returns:
            Dict with sync statistics
        """
        stats = {
            'uploaded': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0
        }

        if direction == 'upload':
            # Upload only new/modified files
            local_path = Path(local_dir)

            if not local_path.exists():
                logger.error(f"Directory not found: {local_dir}")
                return stats

            for file_path in local_path.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_path)
                    remote_path = f"{remote_prefix}/{rel_path}".replace('\\', '/')

                    # Check if file exists remotely
                    if not self.file_exists(remote_path):
                        # New file, upload it
                        if self.upload_file(str(file_path), remote_path):
                            stats['uploaded'] += 1
                        else:
                            stats['failed'] += 1
                    else:
                        # File exists, could check modification time
                        stats['skipped'] += 1

        elif direction == 'download':
            # Download only new/modified files
            local_path = Path(local_dir)
            local_path.mkdir(parents=True, exist_ok=True)

            files = self.list_files(prefix=remote_prefix)

            for file_info in files:
                remote_path = file_info['key']
                rel_path = remote_path[len(remote_prefix):].lstrip('/')
                local_file = local_path / rel_path

                # Check if file exists locally
                if not local_file.exists():
                    # New file, download it
                    local_file.parent.mkdir(parents=True, exist_ok=True)

                    if self.download_file(remote_path, str(local_file)):
                        stats['downloaded'] += 1
                    else:
                        stats['failed'] += 1
                else:
                    stats['skipped'] += 1

        return stats

    def get_bucket_info(self) -> Dict:
        """
        Get bucket information

        Returns:
            Dict with bucket info
        """
        files = self.list_files()

        total_size = sum(f.get('size', 0) for f in files)
        file_count = len(files)

        return {
            'bucket_name': self.bucket_name,
            'file_count': file_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }
