"""
Wasabi Cloud Storage Provider
==============================

Wasabi cloud storage provider for Clean Architecture.

Wasabi is a cost-effective S3-compatible storage service with NO egress fees.

Pricing:
--------
- ~$6.99/TB/month for storage
- NO egress fees (unlike AWS S3)
- No API request fees
- Predictable, simple pricing
- 80% cheaper than AWS S3

Setup:
------
1. Create account at https://wasabi.com/
2. Create bucket in desired region
3. Navigate to Access Keys
4. Create access key pair
5. Add credentials to environment:
   WASABI_ACCESS_KEY=your_access_key
   WASABI_SECRET_KEY=your_secret_key
   WASABI_BUCKET=your_bucket_name
   WASABI_REGION=us-east-1  # or your region

Available Regions:
------------------
- us-east-1: US East (N. Virginia)
- us-east-2: US East (N. Virginia) 2
- us-west-1: US West (Oregon)
- eu-central-1: EU Central (Amsterdam)
- ap-northeast-1: Asia Pacific (Tokyo)

Example:
    >>> from infrastructure.storage.providers import WasabiProvider
    >>>
    >>> provider = WasabiProvider({
    ...     'bucket_name': 'my-ml-bucket',
    ...     'access_key_id': 'WASABI...',
    ...     'secret_access_key': 'secret...',
    ...     'region': 'us-east-1'
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


class WasabiProvider(IStorageProvider):
    """
    Wasabi Cloud Storage Provider.

    Uses S3-compatible API for Wasabi cloud storage.
    Wasabi offers predictable pricing with NO egress fees.

    Attributes:
        bucket_name: Wasabi bucket name
        access_key_id: Wasabi access key
        secret_access_key: Wasabi secret key
        region: Wasabi region

    Example:
        >>> provider = WasabiProvider({
        ...     'bucket_name': 'my-bucket',
        ...     'access_key_id': 'WASABI...',
        ...     'secret_access_key': 'secret...',
        ...     'region': 'us-east-1'
        ... })
        >>> provider.connect()
        >>> files = provider.list_files()
    """

    # Wasabi S3-compatible endpoints by region
    ENDPOINTS = {
        'us-east-1': 'https://s3.wasabisys.com',
        'us-east-2': 'https://s3.us-east-2.wasabisys.com',
        'us-west-1': 'https://s3.us-west-1.wasabisys.com',
        'eu-central-1': 'https://s3.eu-central-1.wasabisys.com',
        'ap-northeast-1': 'https://s3.ap-northeast-1.wasabisys.com',
    }

    def __init__(self, config: Dict):
        """
        Initialize Wasabi provider.

        Args:
            config: Configuration dictionary with keys:
                - bucket_name (required): Wasabi bucket name
                - access_key_id (required): Wasabi access key
                - secret_access_key (required): Wasabi secret key
                - region (optional): Wasabi region (default: us-east-1)

        Raises:
            ConfigurationError: If required configuration is missing

        Example:
            >>> config = {
            ...     'bucket_name': 'my-bucket',
            ...     'access_key_id': 'WASABI...',
            ...     'secret_access_key': 'secret...',
            ...     'region': 'us-east-1'
            ... }
            >>> provider = WasabiProvider(config)
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
        self.region = config.get('region', 'us-east-1')

        # Validate region
        if self.region not in self.ENDPOINTS:
            logger.warning(
                f"Unknown region '{self.region}', using us-east-1. "
                f"Available regions: {', '.join(self.ENDPOINTS.keys())}"
            )
            self.region = 'us-east-1'

        self.endpoint_url = self.ENDPOINTS[self.region]

        self._client = None
        self._connected = False

        logger.debug(
            f"WasabiProvider initialized (bucket={self.bucket_name}, region={self.region})"
        )

    def connect(self) -> None:
        """
        Connect to Wasabi.

        Uses S3-compatible API with region-specific endpoint.

        Raises:
            StorageError: If connection fails
            ConfigurationError: If credentials are invalid

        Example:
            >>> provider = WasabiProvider(config)
            >>> provider.connect()
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Create S3 client with Wasabi endpoint
            self._client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )

            # Test connection by checking if bucket exists
            self._client.head_bucket(Bucket=self.bucket_name)

            self._connected = True
            logger.info(f"Connected to Wasabi bucket: {self.bucket_name} ({self.region})")

        except NoCredentialsError:
            raise ConfigurationError(
                "Wasabi credentials not found. Please provide valid access keys."
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchBucket':
                raise StorageError(
                    f"Bucket '{self.bucket_name}' not found in Wasabi",
                    details={'error_code': error_code, 'region': self.region}
                )
            elif error_code == '403' or error_code == 'AccessDenied':
                raise StorageError(
                    f"Access denied to Wasabi bucket '{self.bucket_name}'",
                    details={'error_code': error_code}
                )
            else:
                raise StorageError(
                    f"Failed to connect to Wasabi: {error_msg}",
                    details={'error_code': error_code}
                )
        except ImportError:
            raise ConfigurationError(
                "boto3 library not installed. Install with: pip install boto3"
            )
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to Wasabi: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from Wasabi."""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from Wasabi")

    def upload(self, local_path: str, remote_path: str, metadata: Optional[Dict] = None) -> None:
        """Upload file to Wasabi."""
        self._ensure_connected()

        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            from botocore.exceptions import ClientError

            extra_args = {}
            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

            self._client.upload_file(
                str(local_file),
                self.bucket_name,
                remote_path,
                ExtraArgs=extra_args if extra_args else None
            )

            logger.info(f"Uploaded: {local_path} → wasabi://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(
                f"Failed to upload file: {error_msg}",
                details={'local_path': local_path, 'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error uploading file: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> None:
        """Download file from Wasabi."""
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

            logger.info(f"Downloaded: wasabi://{self.bucket_name}/{remote_path} → {local_path}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchKey':
                raise StorageError(
                    f"File not found in Wasabi: {remote_path}",
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
        """List files in Wasabi bucket."""
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

            logger.debug(f"Listed {len(files)} files from Wasabi (prefix={prefix})")
            return files

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(f"Failed to list files: {error_msg}")
        except Exception as e:
            raise StorageError(f"Unexpected error listing files: {str(e)}")

    def delete(self, remote_path: str) -> None:
        """Delete file from Wasabi."""
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"Deleted: wasabi://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(
                f"Failed to delete file: {error_msg}",
                details={'remote_path': remote_path}
            )
        except Exception as e:
            raise StorageError(f"Unexpected error deleting file: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        """Check if file exists in Wasabi."""
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
        """Get file size in bytes."""
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
        """Get file metadata."""
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
        """Ensure provider is connected."""
        if not self._connected or not self._client:
            raise StorageError(
                "Not connected to Wasabi. Call connect() first."
            )

    def __str__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"WasabiProvider(bucket={self.bucket_name}, region={self.region}, status={status})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"WasabiProvider(bucket_name='{self.bucket_name}', "
            f"region='{self.region}', endpoint='{self.endpoint_url}', "
            f"connected={self._connected})"
        )
