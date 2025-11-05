"""
DigitalOcean Spaces Storage Provider
====================================

DigitalOcean Spaces storage provider for Clean Architecture.

Spaces is a S3-compatible object storage service from DigitalOcean.

Pricing:
--------
- $5/month for 250GB storage + 1TB transfer
- Additional storage: $0.02/GB/month
- Additional transfer: $0.01/GB
- Excellent price/performance ratio

Setup:
------
1. Create Digital

Ocean account at https://www.digitalocean.com/
2. Create a Space in your desired region
3. Navigate to API → Spaces Keys
4. Generate Spaces access key pair
5. Add credentials to environment:
   DO_SPACES_KEY=your_access_key
   DO_SPACES_SECRET=your_secret_key
   DO_SPACES_NAME=your_space_name
   DO_SPACES_REGION=nyc3  # or your region

Available Regions:
------------------
- nyc3: New York 3
- ams3: Amsterdam 3
- sgp1: Singapore 1
- sfo2: San Francisco 2
- sfo3: San Francisco 3
- fra1: Frankfurt 1

Example:
    >>> from infrastructure.storage.providers import DigitalOceanProvider
    >>>
    >>> provider = DigitalOceanProvider({
    ...     'bucket_name': 'my-ml-space',
    ...     'access_key_id': 'DO00...',
    ...     'secret_access_key': 'your_secret...',
    ...     'region': 'nyc3'
    ... })
    >>>
    >>> provider.connect()
    >>> provider.upload('model.pt', 'models/v1/model.pt')
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from domain.interfaces.storage import IStorageProvider
from domain.exceptions import StorageError, ConfigurationError

logger = logging.getLogger(__name__)


class DigitalOceanProvider(IStorageProvider):
    """
    DigitalOcean Spaces Storage Provider.

    Uses S3-compatible API to interact with DigitalOcean Spaces.
    Spaces is a cost-effective alternative to AWS S3 with predictable pricing.

    Attributes:
        bucket_name: Space name
        access_key_id: Spaces access key
        secret_access_key: Spaces secret key
        region: Space region (nyc3, ams3, sgp1, sfo2, sfo3, fra1)

    Example:
        >>> provider = DigitalOceanProvider({
        ...     'bucket_name': 'my-space',
        ...     'access_key_id': 'DO00...',
        ...     'secret_access_key': 'secret...',
        ...     'region': 'nyc3'
        ... })
        >>> provider.connect()
        >>> files = provider.list_files()
    """

    # DigitalOcean Spaces endpoints by region
    ENDPOINTS = {
        'nyc3': 'https://nyc3.digitaloceanspaces.com',
        'ams3': 'https://ams3.digitaloceanspaces.com',
        'sgp1': 'https://sgp1.digitaloceanspaces.com',
        'sfo2': 'https://sfo2.digitaloceanspaces.com',
        'sfo3': 'https://sfo3.digitaloceanspaces.com',
        'fra1': 'https://fra1.digitaloceanspaces.com',
    }

    def __init__(self, config: Dict):
        """
        Initialize DigitalOcean Spaces provider.

        Args:
            config: Configuration dictionary with keys:
                - bucket_name (required): Space name
                - access_key_id (required): Spaces access key
                - secret_access_key (required): Spaces secret key
                - region (optional): Space region (default: nyc3)

        Raises:
            ConfigurationError: If required configuration is missing

        Example:
            >>> config = {
            ...     'bucket_name': 'my-space',
            ...     'access_key_id': 'DO00...',
            ...     'secret_access_key': 'secret...',
            ...     'region': 'nyc3'
            ... }
            >>> provider = DigitalOceanProvider(config)
        """
        # Validate configuration
        required_keys = ['bucket_name', 'access_key_id', 'secret_access_key']
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )

        self.bucket_name = config['bucket_name']
        self.access_key_id = config['access_key_id']
        self.secret_access_key = config['secret_access_key']
        self.region = config.get('region', 'nyc3')

        # Validate region
        if self.region not in self.ENDPOINTS:
            logger.warning(
                f"Unknown region '{self.region}', using nyc3. "
                f"Available regions: {', '.join(self.ENDPOINTS.keys())}"
            )
            self.region = 'nyc3'

        self.endpoint_url = self.ENDPOINTS[self.region]

        self._client = None
        self._connected = False

        logger.debug(
            f"DigitalOceanProvider initialized (space={self.bucket_name}, region={self.region})"
        )

    def connect(self) -> None:
        """
        Connect to DigitalOcean Spaces.

        Uses S3-compatible API with region-specific endpoint.

        Raises:
            StorageError: If connection fails
            ConfigurationError: If credentials are invalid

        Example:
            >>> provider = DigitalOceanProvider(config)
            >>> provider.connect()
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Create S3 client with DigitalOcean endpoint
            self._client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )

            # Test connection by checking if Space exists
            self._client.head_bucket(Bucket=self.bucket_name)

            self._connected = True
            logger.info(f"Connected to DigitalOcean Space: {self.bucket_name} ({self.region})")

        except NoCredentialsError:
            raise ConfigurationError(
                "DigitalOcean Spaces credentials not found. Please provide valid access keys."
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchBucket':
                raise StorageError(
                    f"Space '{self.bucket_name}' not found in region '{self.region}'",
                    details={'error_code': error_code, 'region': self.region}
                )
            elif error_code == '403' or error_code == 'AccessDenied':
                raise StorageError(
                    f"Access denied to Space '{self.bucket_name}'",
                    details={'error_code': error_code}
                )
            else:
                raise StorageError(
                    f"Failed to connect to DigitalOcean Spaces: {error_msg}",
                    details={'error_code': error_code}
                )
        except ImportError:
            raise ConfigurationError(
                "boto3 library not installed. Install with: pip install boto3"
            )
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to DigitalOcean Spaces: {str(e)}")

    def disconnect(self) -> None:
        """
        Disconnect from DigitalOcean Spaces.

        Example:
            >>> provider.disconnect()
        """
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from DigitalOcean Spaces")

    def upload(self, local_path: str, remote_path: str, metadata: Optional[Dict] = None) -> None:
        """
        Upload file to DigitalOcean Spaces.

        Args:
            local_path: Path to local file
            remote_path: Destination path in Space
            metadata: Optional metadata to attach to object

        Raises:
            StorageError: If upload fails
            FileNotFoundError: If local file doesn't exist

        Example:
            >>> provider.upload('data.json', 'datasets/data.json')
        """
        self._ensure_connected()

        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            from botocore.exceptions import ClientError

            extra_args = {'ACL': 'private'}  # Default to private
            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

            self._client.upload_file(
                str(local_file),
                self.bucket_name,
                remote_path,
                ExtraArgs=extra_args
            )

            logger.info(f"Uploaded: {local_path} → spaces://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(
                f"Failed to upload file: {error_msg}",
                details={'local_path': local_path, 'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error uploading file: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> None:
        """
        Download file from DigitalOcean Spaces.

        Args:
            remote_path: Path to file in Space
            local_path: Local destination path

        Raises:
            StorageError: If download fails

        Example:
            >>> provider.download('datasets/data.json', 'local/data.json')
        """
        self._ensure_connected()

        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            from botocore.exceptions import ClientError

            self._client.download_file(
                self.bucket_name,
                remote_path,
                str(local_file)
            )

            logger.info(f"Downloaded: spaces://{self.bucket_name}/{remote_path} → {local_path}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchKey':
                raise StorageError(
                    f"File not found in Space: {remote_path}",
                    details={'remote_path': remote_path}
                )
            else:
                raise StorageError(
                    f"Failed to download file: {error_msg}",
                    details={'remote_path': remote_path, 'local_path': local_path}
                )
        except Exception as e:
            raise StorageError(f"Unexpected error downloading file: {str(e)}")

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """
        List files in DigitalOcean Space.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file paths in Space

        Raises:
            StorageError: If listing fails

        Example:
            >>> files = provider.list_files()
            >>> dataset_files = provider.list_files(prefix='datasets/')
        """
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            params = {'Bucket': self.bucket_name}
            if prefix:
                params['Prefix'] = prefix

            response = self._client.list_objects_v2(**params)

            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]

            logger.debug(f"Listed {len(files)} files from DigitalOcean Spaces (prefix={prefix})")
            return files

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(f"Failed to list files: {error_msg}")
        except Exception as e:
            raise StorageError(f"Unexpected error listing files: {str(e)}")

    def delete(self, remote_path: str) -> None:
        """
        Delete file from DigitalOcean Spaces.

        Args:
            remote_path: Path to file in Space

        Raises:
            StorageError: If deletion fails

        Example:
            >>> provider.delete('old_data/file.json')
        """
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"Deleted: spaces://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(
                f"Failed to delete file: {error_msg}",
                details={'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error deleting file: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        """
        Check if file exists in DigitalOcean Spaces.

        Args:
            remote_path: Path to file in Space

        Returns:
            True if file exists, False otherwise

        Example:
            >>> if provider.exists('datasets/data.json'):
            ...     print("File exists")
        """
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            self._client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                return False
            logger.warning(f"Error checking file existence: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking file existence: {e}")
            return False

    def get_file_size(self, remote_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            remote_path: Path to file in Space

        Returns:
            File size in bytes

        Raises:
            StorageError: If file doesn't exist or operation fails

        Example:
            >>> size = provider.get_file_size('datasets/data.json')
            >>> print(f"File size: {size / 1024 / 1024:.2f} MB")
        """
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            return response['ContentLength']

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                raise StorageError(
                    f"File not found: {remote_path}",
                    details={'remote_path': remote_path}
                )
            raise StorageError(
                f"Failed to get file size: {e}",
                details={'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error getting file size: {str(e)}")

    def get_metadata(self, remote_path: str) -> Dict:
        """
        Get file metadata.

        Args:
            remote_path: Path to file in Space

        Returns:
            Dictionary with file metadata

        Raises:
            StorageError: If file doesn't exist or operation fails

        Example:
            >>> metadata = provider.get_metadata('datasets/data.json')
            >>> print(metadata['size'], metadata['last_modified'])
        """
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            metadata = {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', 'application/octet-stream')
            }

            # Add custom metadata if present
            if 'Metadata' in response:
                metadata['custom'] = response['Metadata']

            return metadata

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                raise StorageError(
                    f"File not found: {remote_path}",
                    details={'remote_path': remote_path}
                )
            raise StorageError(
                f"Failed to get metadata: {e}",
                details={'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error getting metadata: {str(e)}")

    def _ensure_connected(self) -> None:
        """
        Ensure provider is connected.

        Raises:
            StorageError: If not connected
        """
        if not self._connected or not self._client:
            raise StorageError(
                "Not connected to DigitalOcean Spaces. Call connect() first."
            )

    def __str__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return (
            f"DigitalOceanProvider(space={self.bucket_name}, "
            f"region={self.region}, status={status})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"DigitalOceanProvider(bucket_name='{self.bucket_name}', "
            f"region='{self.region}', endpoint='{self.endpoint_url}', "
            f"connected={self._connected})"
        )
