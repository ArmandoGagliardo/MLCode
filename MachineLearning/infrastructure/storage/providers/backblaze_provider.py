"""
Backblaze B2 Cloud Storage Provider
====================================

Backblaze B2 storage provider for Clean Architecture.

B2 is one of the most cost-effective cloud storage options.

Pricing:
--------
- $5/TB/month for storage
- $10/TB for download bandwidth
- 10GB/day free egress
- No API request fees
- 75% cheaper than AWS S3

Setup:
------
1. Create account at https://www.backblaze.com/b2/
2. Create bucket
3. Create application key with read/write access
4. Note the endpoint URL for your region (e.g., s3.us-west-004.backblazeb2.com)
5. Add credentials to environment:
   BACKBLAZE_KEY_ID=your_key_id
   BACKBLAZE_APPLICATION_KEY=your_app_key
   BACKBLAZE_BUCKET=your_bucket_name
   BACKBLAZE_ENDPOINT=https://s3.us-west-004.backblazeb2.com

Example:
    >>> from infrastructure.storage.providers import BackblazeProvider
    >>>
    >>> provider = BackblazeProvider({
    ...     'bucket_name': 'my-ml-bucket',
    ...     'key_id': 'your_key_id',
    ...     'application_key': 'your_app_key',
    ...     'endpoint_url': 'https://s3.us-west-004.backblazeb2.com'
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


class BackblazeProvider(IStorageProvider):
    """
    Backblaze B2 Cloud Storage Provider.

    Uses S3-compatible API for Backblaze B2 storage.
    B2 is one of the most affordable cloud storage options.

    Attributes:
        bucket_name: B2 bucket name
        key_id: Application key ID
        application_key: Application key
        endpoint_url: S3-compatible endpoint URL

    Example:
        >>> provider = BackblazeProvider({
        ...     'bucket_name': 'my-bucket',
        ...     'key_id': 'key_id',
        ...     'application_key': 'app_key',
        ...     'endpoint_url': 'https://s3.us-west-004.backblazeb2.com'
        ... })
        >>> provider.connect()
    """

    # Default endpoint (update based on your bucket region)
    DEFAULT_ENDPOINT = 'https://s3.us-west-004.backblazeb2.com'

    def __init__(self, config: Dict):
        """
        Initialize Backblaze B2 provider.

        Args:
            config: Configuration dictionary with keys:
                - bucket_name (required): B2 bucket name
                - key_id (required): Application key ID
                - application_key (required): Application key
                - endpoint_url (optional): S3-compatible endpoint

        Raises:
            ConfigurationError: If required configuration is missing
        """
        required_keys = ['bucket_name', 'key_id', 'application_key']
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )

        self.bucket_name = config['bucket_name']
        self.key_id = config['key_id']
        self.application_key = config['application_key']
        self.endpoint_url = config.get('endpoint_url', self.DEFAULT_ENDPOINT)

        self._client = None
        self._connected = False

        logger.debug(f"BackblazeProvider initialized (bucket={self.bucket_name})")

    def connect(self) -> None:
        """Connect to Backblaze B2."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            self._client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.application_key
            )

            # Test connection
            self._client.head_bucket(Bucket=self.bucket_name)

            self._connected = True
            logger.info(f"Connected to Backblaze B2 bucket: {self.bucket_name}")

        except NoCredentialsError:
            raise ConfigurationError("Backblaze B2 credentials not found.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchBucket':
                raise StorageError(
                    f"Bucket '{self.bucket_name}' not found in Backblaze B2",
                    details={'error_code': error_code}
                )
            elif error_code == '403' or error_code == 'AccessDenied':
                raise StorageError(
                    f"Access denied to Backblaze B2 bucket '{self.bucket_name}'",
                    details={'error_code': error_code}
                )
            else:
                raise StorageError(f"Failed to connect to Backblaze B2: {error_msg}")
        except ImportError:
            raise ConfigurationError("boto3 library not installed. Install with: pip install boto3")
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to Backblaze B2: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from Backblaze B2."""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from Backblaze B2")

    def upload(self, local_path: str, remote_path: str, metadata: Optional[Dict] = None) -> None:
        """Upload file to Backblaze B2."""
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

            logger.info(f"Uploaded: {local_path} → b2://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(f"Failed to upload file: {error_msg}")
        except Exception as e:
            raise StorageError(f"Unexpected error uploading file: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> None:
        """Download file from Backblaze B2."""
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

            logger.info(f"Downloaded: b2://{self.bucket_name}/{remote_path} → {local_path}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchKey':
                raise StorageError(f"File not found in B2: {remote_path}")
            raise StorageError(f"Failed to download file: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error downloading file: {str(e)}")

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List files in Backblaze B2 bucket."""
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

            logger.debug(f"Listed {len(files)} files from Backblaze B2")
            return files

        except ClientError as e:
            raise StorageError(f"Failed to list files: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error listing files: {str(e)}")

    def delete(self, remote_path: str) -> None:
        """Delete file from Backblaze B2."""
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"Deleted: b2://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            raise StorageError(f"Failed to delete file: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error deleting file: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        """Check if file exists in Backblaze B2."""
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
                raise StorageError(f"File not found: {remote_path}")
            raise StorageError(f"Failed to get file size: {e}")
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
                raise StorageError(f"File not found: {remote_path}")
            raise StorageError(f"Failed to get metadata: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error getting metadata: {str(e)}")

    def _ensure_connected(self) -> None:
        """Ensure provider is connected."""
        if not self._connected or not self._client:
            raise StorageError("Not connected to Backblaze B2. Call connect() first.")

    def __str__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"BackblazeProvider(bucket={self.bucket_name}, status={status})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"BackblazeProvider(bucket_name='{self.bucket_name}', "
            f"endpoint='{self.endpoint_url}', connected={self._connected})"
        )
