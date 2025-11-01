"""
Storage Manager

Main class for managing cloud storage operations including:
- Auto-connecting to cloud provider on startup
- Downloading datasets before training
- Backing up models after fine-tuning
- Syncing data between local and cloud storage

Usage:
    from module.storage import StorageManager

    # Initialize and connect
    storage = StorageManager()
    storage.connect()

    # Download datasets
    storage.download_datasets()

    # Train model...

    # Backup model
    storage.backup_model('path/to/model', model_name='my_model_v1')
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging
import json

from .providers import create_provider
from .base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class StorageManager:
    """Main storage manager for cloud storage operations"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize storage manager

        Args:
            config: Optional configuration dict. If None, loads from environment variables.
        """
        self.provider: Optional[BaseStorageProvider] = None
        self.config = config or self._load_config_from_env()
        self.connected = False

        # Default paths
        self.local_dataset_dir = self.config.get('local_dataset_dir', 'data/datasets')
        self.local_models_dir = self.config.get('local_models_dir', 'models/saved')
        self.remote_dataset_prefix = self.config.get('remote_dataset_prefix', 'datasets')
        self.remote_models_prefix = self.config.get('remote_models_prefix', 'models')

        # Create local directories
        Path(self.local_dataset_dir).mkdir(parents=True, exist_ok=True)
        Path(self.local_models_dir).mkdir(parents=True, exist_ok=True)

    def _load_config_from_env(self) -> Dict:
        """Load storage configuration from environment variables"""
        provider_type = os.getenv('STORAGE_PROVIDER', 'backblaze').lower()

        config = {
            'provider_type': provider_type,
            'local_dataset_dir': os.getenv('LOCAL_DATASET_DIR', 'data/datasets'),
            'local_models_dir': os.getenv('LOCAL_MODELS_DIR', 'models/saved'),
            'remote_dataset_prefix': os.getenv('REMOTE_DATASET_PREFIX', 'datasets'),
            'remote_models_prefix': os.getenv('REMOTE_MODELS_PREFIX', 'models'),
            'auto_sync_on_startup': os.getenv('AUTO_SYNC_ON_STARTUP', 'true').lower() == 'true',
            'auto_backup_after_training': os.getenv('AUTO_BACKUP_AFTER_TRAINING', 'true').lower() == 'true',
        }

        # Provider-specific configuration
        if provider_type == 'backblaze':
            config['provider_config'] = {
                'bucket_name': os.getenv('BACKBLAZE_BUCKET'),
                'key_id': os.getenv('BACKBLAZE_KEY_ID'),
                'application_key': os.getenv('BACKBLAZE_APPLICATION_KEY'),
                'endpoint_url': os.getenv('BACKBLAZE_ENDPOINT'),
            }
        elif provider_type == 'wasabi':
            config['provider_config'] = {
                'bucket_name': os.getenv('WASABI_BUCKET'),
                'access_key': os.getenv('WASABI_ACCESS_KEY'),
                'secret_key': os.getenv('WASABI_SECRET_KEY'),
                'region': os.getenv('WASABI_REGION', 'us-east-1'),
            }
        elif provider_type in ['s3', 'aws']:
            config['provider_config'] = {
                'bucket_name': os.getenv('AWS_BUCKET'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region': os.getenv('AWS_REGION', 'us-east-1'),
            }
        elif provider_type in ['digitalocean', 'do']:
            config['provider_config'] = {
                'bucket_name': os.getenv('DO_SPACES_NAME'),
                'access_key': os.getenv('DO_SPACES_KEY'),
                'secret_key': os.getenv('DO_SPACES_SECRET'),
                'region': os.getenv('DO_SPACES_REGION', 'nyc3'),
            }
        elif provider_type in ['cloudflare_r2', 'r2']:
            config['provider_config'] = {
                'bucket_name': os.getenv('CLOUDFLARE_R2_BUCKET'),
                'account_id': os.getenv('CLOUDFLARE_R2_ACCOUNT_ID'),
                'access_key': os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
                'secret_key': os.getenv('CLOUDFLARE_R2_SECRET_KEY'),
            }
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        return config

    def connect(self) -> bool:
        """
        Connect to cloud storage provider

        Returns:
            True if connection successful
        """
        try:
            provider_type = self.config['provider_type']
            provider_config = self.config['provider_config']

            # Remove None values
            provider_config = {k: v for k, v in provider_config.items() if v is not None}

            logger.info(f"Connecting to {provider_type} storage...")

            # Create provider instance
            self.provider = create_provider(provider_type, **provider_config)

            # Connect
            if self.provider.connect():
                self.connected = True
                logger.info(f"Successfully connected to {provider_type} storage")

                # Auto-sync datasets if configured
                if self.config.get('auto_sync_on_startup', True):
                    logger.info("Auto-sync enabled, downloading datasets...")
                    self.download_datasets()

                return True
            else:
                logger.error(f"Failed to connect to {provider_type} storage")
                return False

        except Exception as e:
            logger.error(f"Error connecting to storage: {e}")
            return False

    def download_datasets(self, force: bool = False) -> Dict[str, int]:
        """
        Download datasets from cloud storage

        Args:
            force: If True, download all files. If False, only download new files.

        Returns:
            Dict with download statistics
        """
        if not self.connected or self.provider is None:
            logger.error("Not connected to storage provider")
            return {'downloaded': 0, 'skipped': 0, 'failed': 0}

        logger.info(f"Downloading datasets to {self.local_dataset_dir}...")

        try:
            if force:
                # Download all files
                files = self.provider.list_files(prefix=self.remote_dataset_prefix)
                downloaded_files = self.provider.download_directory(
                    self.remote_dataset_prefix,
                    self.local_dataset_dir
                )

                stats = {
                    'downloaded': len(downloaded_files),
                    'skipped': 0,
                    'failed': len(files) - len(downloaded_files)
                }
            else:
                # Sync only new files
                stats = self.provider.sync_directory(
                    self.local_dataset_dir,
                    self.remote_dataset_prefix,
                    direction='download'
                )

            logger.info(f"Dataset download complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error downloading datasets: {e}")
            return {'downloaded': 0, 'skipped': 0, 'failed': 1}

    def upload_datasets(self, force: bool = False) -> Dict[str, int]:
        """
        Upload datasets to cloud storage

        Args:
            force: If True, upload all files. If False, only upload new files.

        Returns:
            Dict with upload statistics
        """
        if not self.connected or self.provider is None:
            logger.error("Not connected to storage provider")
            return {'uploaded': 0, 'skipped': 0, 'failed': 0}

        logger.info(f"Uploading datasets from {self.local_dataset_dir}...")

        try:
            if force:
                # Upload all files
                uploaded_files = self.provider.upload_directory(
                    self.local_dataset_dir,
                    self.remote_dataset_prefix
                )

                stats = {
                    'uploaded': len(uploaded_files),
                    'skipped': 0,
                    'failed': 0
                }
            else:
                # Sync only new files
                stats = self.provider.sync_directory(
                    self.local_dataset_dir,
                    self.remote_dataset_prefix,
                    direction='upload'
                )

            logger.info(f"Dataset upload complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error uploading datasets: {e}")
            return {'uploaded': 0, 'skipped': 0, 'failed': 1}

    def backup_model(
        self,
        model_path: str,
        model_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Backup a trained model to cloud storage

        Args:
            model_path: Path to model file or directory
            model_name: Optional model name (defaults to filename with timestamp)
            metadata: Optional metadata dict to store with model

        Returns:
            True if backup successful
        """
        if not self.connected or self.provider is None:
            logger.error("Not connected to storage provider")
            return False

        try:
            model_path = Path(model_path)

            if not model_path.exists():
                logger.error(f"Model path does not exist: {model_path}")
                return False

            # Generate model name with timestamp
            if model_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_name = f"{model_path.stem}_{timestamp}"

            # Prepare metadata
            backup_metadata = {
                'backup_date': datetime.now().isoformat(),
                'model_name': model_name,
                'original_path': str(model_path),
            }

            if metadata:
                backup_metadata.update(metadata)

            logger.info(f"Backing up model: {model_name}")

            # Backup single file or directory
            if model_path.is_file():
                remote_path = f"{self.remote_models_prefix}/{model_name}/{model_path.name}"

                success = self.provider.upload_file(
                    str(model_path),
                    remote_path,
                    metadata=backup_metadata
                )

                if success:
                    # Save metadata file
                    metadata_path = f"{self.remote_models_prefix}/{model_name}/metadata.json"
                    metadata_content = json.dumps(backup_metadata, indent=2)

                    # Create temp metadata file
                    temp_metadata_file = Path(self.local_models_dir) / 'temp_metadata.json'
                    temp_metadata_file.write_text(metadata_content)

                    self.provider.upload_file(
                        str(temp_metadata_file),
                        metadata_path
                    )

                    temp_metadata_file.unlink()  # Delete temp file

                    logger.info(f"Model backup successful: {model_name}")
                    return True
                else:
                    return False

            elif model_path.is_dir():
                # Upload entire directory
                remote_prefix = f"{self.remote_models_prefix}/{model_name}"

                uploaded_files = self.provider.upload_directory(
                    str(model_path),
                    remote_prefix
                )

                if uploaded_files:
                    # Save metadata file
                    metadata_path = f"{remote_prefix}/metadata.json"
                    metadata_content = json.dumps(backup_metadata, indent=2)

                    temp_metadata_file = Path(self.local_models_dir) / 'temp_metadata.json'
                    temp_metadata_file.write_text(metadata_content)

                    self.provider.upload_file(
                        str(temp_metadata_file),
                        metadata_path
                    )

                    temp_metadata_file.unlink()

                    logger.info(f"Model backup successful: {model_name} ({len(uploaded_files)} files)")
                    return True
                else:
                    logger.error("No files were uploaded")
                    return False

            else:
                logger.error(f"Invalid model path: {model_path}")
                return False

        except Exception as e:
            logger.error(f"Error backing up model: {e}")
            return False

    def restore_model(
        self,
        model_name: str,
        destination: Optional[str] = None
    ) -> bool:
        """
        Restore a model from cloud storage

        Args:
            model_name: Name of the model to restore
            destination: Optional destination path (defaults to local_models_dir)

        Returns:
            True if restore successful
        """
        if not self.connected or self.provider is None:
            logger.error("Not connected to storage provider")
            return False

        try:
            if destination is None:
                destination = str(Path(self.local_models_dir) / model_name)

            remote_prefix = f"{self.remote_models_prefix}/{model_name}"

            logger.info(f"Restoring model: {model_name}")

            # Download model directory
            downloaded_files = self.provider.download_directory(
                remote_prefix,
                destination
            )

            if downloaded_files:
                logger.info(f"Model restored successfully: {model_name} ({len(downloaded_files)} files)")
                return True
            else:
                logger.error("No files were downloaded")
                return False

        except Exception as e:
            logger.error(f"Error restoring model: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        List all backed up models

        Returns:
            List of model names
        """
        if not self.connected or self.provider is None:
            logger.error("Not connected to storage provider")
            return []

        try:
            files = self.provider.list_files(prefix=self.remote_models_prefix)

            # Extract unique model names (first level directories)
            model_names = set()
            for file_info in files:
                key = file_info['key']
                # Remove prefix and get first directory
                relative_path = key[len(self.remote_models_prefix):].lstrip('/')
                if '/' in relative_path:
                    model_name = relative_path.split('/')[0]
                    model_names.add(model_name)

            return sorted(list(model_names))

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def get_storage_info(self) -> Dict:
        """
        Get storage statistics

        Returns:
            Dict with storage information
        """
        if not self.connected or self.provider is None:
            return {
                'connected': False,
                'provider': self.config.get('provider_type', 'unknown')
            }

        try:
            info = self.provider.get_bucket_info()
            info['connected'] = True
            info['provider'] = self.config['provider_type']
            info['local_dataset_dir'] = self.local_dataset_dir
            info['local_models_dir'] = self.local_models_dir

            return info

        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {
                'connected': self.connected,
                'provider': self.config['provider_type'],
                'error': str(e)
            }

    def disconnect(self):
        """Disconnect from storage provider"""
        if self.provider:
            self.provider.client = None
            self.provider = None
            self.connected = False
            logger.info("Disconnected from storage provider")


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize storage manager
    storage = StorageManager()

    # Connect to storage
    if storage.connect():
        print("\nStorage connected successfully!")

        # Get storage info
        info = storage.get_storage_info()
        print(f"\nStorage Info:")
        print(f"  Provider: {info.get('provider')}")
        print(f"  Bucket: {info.get('bucket_name')}")
        print(f"  Files: {info.get('file_count')}")
        print(f"  Size: {info.get('total_size_mb')} MB")

        # List models
        models = storage.list_models()
        print(f"\nBacked up models ({len(models)}):")
        for model in models:
            print(f"  - {model}")

    else:
        print("Failed to connect to storage")
        sys.exit(1)
