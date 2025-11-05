"""
Cloudflare R2 Cloud Storage Provider
=====================================

Cloudflare R2 storage provider for Clean Architecture.

R2 is S3-compatible storage with ZERO egress fees.

Pricing:
--------
- $15/TB/month for storage
- $0/TB for egress (downloads) - ZERO fees!
- $4.50/million Class A operations (write, list)
- $0.36/million Class B operations (read)
- Best for high-traffic applications

Setup:
------
1. Sign up for Cloudflare at https://www.cloudflare.com/
2. Navigate to R2 in dashboard
3. Enable R2 (may require payment method)
4. Create a bucket
5. Generate R2 API token (Manage R2 API Tokens)
6. Get your account ID from R2 dashboard
7. Add credentials to environment:
   CLOUDFLARE_R2_ACCOUNT_ID=your_account_id
   CLOUDFLARE_R2_ACCESS_KEY=your_access_key
   CLOUDFLARE_R2_SECRET_KEY=your_secret_key
   CLOUDFLARE_R2_BUCKET=your_bucket_name

Example:
    >>> from infrastructure.storage.providers import CloudflareR2Provider
    >>>
    >>> provider = CloudflareR2Provider({
    ...     'bucket_name': 'my-ml-bucket',
    ...     'account_id': 'your_account_id',
    ...     'access_key_id': 'your_access_key',
    ...     'secret_access_key': 'your_secret_key'
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


class CloudflareR2Provider(IStorageProvider):
    """
    Cloudflare R2 Cloud Storage Provider.

    Uses S3-compatible API for Cloudflare R2 storage.
    R2's main advantage is ZERO egress fees, ideal for high-traffic applications.

    Attributes:
        bucket_name: R2 bucket name
        account_id: Cloudflare account ID
        access_key_id: R2 access key
        secret_access_key: R2 secret key

    Example:
        >>> provider = CloudflareR2Provider({
        ...     'bucket_name': 'my-bucket',
        ...     'account_id': 'account_id',
        ...     'access_key_id': 'access_key',
        ...     'secret_access_key': 'secret_key'
        ... })
        >>> provider.connect()
    """

    def __init__(self, config: Dict):
        """
        Initialize Cloudflare R2 provider.

        Args:
            config: Configuration dictionary with keys:
                - bucket_name (required): R2 bucket name
                - account_id (required): Cloudflare account ID
                - access_key_id (required): R2 access key
                - secret_access_key (required): R2 secret key

        Raises:
            ConfigurationError: If required configuration is missing
        """
        required_keys = ['bucket_name', 'account_id', 'access_key_id', 'secret_access_key']
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )

        self.bucket_name = config['bucket_name']
        self.account_id = config['account_id']
        self.access_key_id = config['access_key_id']
        self.secret_access_key = config['secret_access_key']

        # R2 endpoint is constructed from account_id
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self._client = None
        self._connected = False

        logger.debug(f"CloudflareR2Provider initialized (bucket={self.bucket_name})")

    def connect(self) -> None:
        """
        Connect to Cloudflare R2.

        R2 uses 'auto' as region and account-specific endpoint.

        Raises:
            StorageError: If connection fails
            ConfigurationError: If credentials are invalid
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Create S3 client with R2 endpoint
            self._client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto'  # R2 uses 'auto' for region
            )

            # Test connection by checking if bucket exists
            self._client.head_bucket(Bucket=self.bucket_name)

            self._connected = True
            logger.info(f"Connected to Cloudflare R2 bucket: {self.bucket_name}")

        except NoCredentialsError:
            raise ConfigurationError("Cloudflare R2 credentials not found.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchBucket':
                raise StorageError(
                    f"R2 bucket '{self.bucket_name}' not found",
                    details={'error_code': error_code}
                )
            elif error_code == '403' or error_code == 'AccessDenied':
                raise StorageError(
                    f"Access denied to R2 bucket '{self.bucket_name}'",
                    details={'error_code': error_code}
                )
            else:
                raise StorageError(f"Failed to connect to Cloudflare R2: {error_msg}")
        except ImportError:
            raise ConfigurationError("boto3 library not installed. Install with: pip install boto3")
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to Cloudflare R2: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from Cloudflare R2."""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from Cloudflare R2")

    def upload(self, local_path: str, remote_path: str, metadata: Optional[Dict] = None) -> None:
        """Upload file to Cloudflare R2."""
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

            logger.info(f"Uploaded: {local_path} → r2://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(f"Failed to upload file: {error_msg}")
        except Exception as e:
            raise StorageError(f"Unexpected error uploading file: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> None:
        """Download file from Cloudflare R2."""
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

            logger.info(f"Downloaded: r2://{self.bucket_name}/{remote_path} → {local_path}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchKey':
                raise StorageError(f"File not found in R2: {remote_path}")
            raise StorageError(f"Failed to download file: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error downloading file: {str(e)}")

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List files in Cloudflare R2 bucket."""
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

            logger.debug(f"Listed {len(files)} files from Cloudflare R2")
            return files

        except ClientError as e:
            raise StorageError(f"Failed to list files: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error listing files: {str(e)}")

    def delete(self, remote_path: str) -> None:
        """Delete file from Cloudflare R2."""
        self._ensure_connected()

        try:
            from botocore.exceptions import ClientError

            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"Deleted: r2://{self.bucket_name}/{remote_path}")

        except ClientError as e:
            raise StorageError(f"Failed to delete file: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error deleting file: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        """Check if file exists in Cloudflare R2."""
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
            raise StorageError("Not connected to Cloudflare R2. Call connect() first.")

    def __str__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"CloudflareR2Provider(bucket={self.bucket_name}, status={status})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"CloudflareR2Provider(bucket_name='{self.bucket_name}', "
            f"account_id='{self.account_id}', endpoint='{self.endpoint_url}', "
            f"connected={self._connected})"
        )
