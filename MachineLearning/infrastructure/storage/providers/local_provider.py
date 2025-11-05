"""
Local Storage Provider
======================

Implementation of IStorageProvider for local filesystem storage.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional, Dict
from domain.interfaces.storage import IStorageProvider
from domain.exceptions import StorageError
from domain.validation.validators import PathValidator

logger = logging.getLogger(__name__)


class LocalProvider(IStorageProvider):
    """
    Local filesystem storage provider.

    Stores files in the local filesystem, useful for:
    - Development and testing
    - Single-machine deployments
    - Fast local access

    Configuration:
        - base_path: str - Base directory for storage (default: 'data/storage')
        - create_dirs: bool - Auto-create directories (default: True)

    Example:
        >>> config = {'provider_type': 'local', 'base_path': '/data'}
        >>> provider = LocalProvider(config)
        >>> provider.connect()
        >>> provider.upload('file.txt', 'remote/file.txt')
        True
    """

    def __init__(self, config: Dict):
        """
        Initialize local storage provider.

        Args:
            config: Configuration dictionary
        """
        self._config = config
        self._base_path = Path(config.get('base_path', 'data/storage'))
        self._create_dirs = config.get('create_dirs', True)
        self._connected = False

        logger.info(f"LocalProvider initialized: {self._base_path}")

    def connect(self) -> bool:
        """Establish connection (create base directory if needed)"""
        try:
            if self._create_dirs:
                self._base_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created storage directory: {self._base_path}")

            if not self._base_path.exists():
                raise StorageError(
                    f"Storage directory does not exist: {self._base_path}",
                    details={'base_path': str(self._base_path)}
                )

            self._connected = True
            logger.info("LocalProvider connected")
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}", exc_info=True)
            raise StorageError(f"Connection failed: {e}")

    def disconnect(self) -> None:
        """Close connection (no-op for local storage)"""
        self._connected = False
        logger.info("LocalProvider disconnected")

    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to storage"""
        try:
            # Validate paths
            PathValidator.validate_path(local_path, must_exist=True)
            PathValidator.validate_path(remote_path)

            # Construct full remote path
            full_remote = self._base_path / remote_path

            # Create parent directories
            full_remote.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(local_path, full_remote)

            logger.info(f"Uploaded: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            raise StorageError(f"Upload failed: {e}")

    def download(self, remote_path: str, local_path: str) -> bool:
        """Download file from storage"""
        try:
            PathValidator.validate_path(remote_path)

            full_remote = self._base_path / remote_path

            if not full_remote.exists():
                raise StorageError(
                    f"Remote file not found: {remote_path}",
                    details={'full_path': str(full_remote)}
                )

            # Create local parent directories
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(full_remote, local_path)

            logger.info(f"Downloaded: {remote_path} -> {local_path}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            raise StorageError(f"Download failed: {e}")

    def list_files(self, prefix: str = "", recursive: bool = True) -> List[str]:
        """List files in storage"""
        try:
            search_path = self._base_path / prefix

            if not search_path.exists():
                return []

            if recursive:
                files = search_path.rglob('*')
            else:
                files = search_path.glob('*')

            # Return relative paths from base
            result = []
            for file in files:
                if file.is_file():
                    rel_path = file.relative_to(self._base_path)
                    result.append(str(rel_path))

            logger.debug(f"Listed {len(result)} files with prefix '{prefix}'")
            return result

        except Exception as e:
            logger.error(f"List files failed: {e}", exc_info=True)
            raise StorageError(f"List files failed: {e}")

    def delete(self, remote_path: str) -> bool:
        """Delete file from storage"""
        try:
            full_remote = self._base_path / remote_path

            if not full_remote.exists():
                logger.warning(f"File not found for deletion: {remote_path}")
                return False

            full_remote.unlink()
            logger.info(f"Deleted: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Delete failed: {e}", exc_info=True)
            raise StorageError(f"Delete failed: {e}")

    def exists(self, remote_path: str) -> bool:
        """Check if file exists"""
        try:
            full_remote = self._base_path / remote_path
            return full_remote.exists() and full_remote.is_file()
        except Exception:
            return False

    def get_file_size(self, remote_path: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            full_remote = self._base_path / remote_path
            if full_remote.exists() and full_remote.is_file():
                return full_remote.stat().st_size
            return None
        except Exception as e:
            logger.warning(f"Failed to get file size: {e}")
            return None

    def get_metadata(self, remote_path: str) -> Optional[Dict]:
        """Get file metadata"""
        try:
            full_remote = self._base_path / remote_path

            if not full_remote.exists():
                return None

            stat = full_remote.stat()

            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': full_remote.is_file(),
                'path': str(remote_path),
            }

        except Exception as e:
            logger.warning(f"Failed to get metadata: {e}")
            return None
