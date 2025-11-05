"""
AWS S3 Storage Provider
=======================

Amazon S3 storage provider implementation for Clean Architecture.

This provider implements the IStorageProvider interface for AWS S3,
providing cloud storage capabilities following Clean Architecture principles.

Pricing:
--------
- Variable by region
- ~$23/TB/month for S3 Standard
- Additional costs for requests and data transfer

Setup:
------
1. Create AWS account at https://aws.amazon.com/
2. Create S3 bucket in desired region
3. Create IAM user with S3 permissions:
   - s3:PutObject
   - s3:GetObject
   - s3:DeleteObject
   - s3:ListBucket
   - s3:HeadObject

4. Add credentials to environment:
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_BUCKET_NAME=your_bucket_name
   AWS_REGION=us-east-1  # or your region

Example:
    >>> from infrastructure.storage.providers import S3Provider
    >>>
    >>> provider = S3Provider({
    ...     'bucket_name': 'my-ml-bucket',
    ...     'access_key_id': 'AKIAIOSFODNN7EXAMPLE',
    ...     'secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    ...     'region': 'us-east-1'
    ... })
    >>>
    >>> provider.connect()
    >>> provider.upload('local_file.txt', 'remote/path/file.txt')
    >>> provider.disconnect()
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from domain.interfaces.storage import IStorageProvider
from domain.exceptions import StorageError, ConfigurationError

logger = logging.getLogger(__name__)


class S3Provider(IStorageProvider):
    """
    AWS S3 Storage Provider.

    Implements cloud storage operations using AWS S3 service.
    Compatible with S3 API (can be used with S3-compatible services).

    Attributes:
        bucket_name: S3 bucket name
        access_key_id: AWS access key ID
        secret_access_key: AWS secret access key
        region: AWS region (default: us-east-1)
        endpoint_url: Custom S3 endpoint (for S3-compatible services)

    Example:
        >>> provider = S3Provider({
        ...     'bucket_name': 'my-bucket',
        ...     'access_key_id': 'AKIA...',
        ...     'secret_access_key': 'wJalr...',
        ...     'region': 'us-east-1'
        ... })
        >>> provider.connect()
        >>> files = provider.list_files()
    """

    def __init__(self, config: Dict):
        """
        Initialize S3 provider.

        Args:
            config: Configuration dictionary with keys:
                - bucket_name (required): S3 bucket name
                - access_key_id (required): AWS access key ID
                - secret_access_key (required): AWS secret access key
                - region (optional): AWS region (default: us-east-1)
                - endpoint_url (optional): Custom S3 endpoint

        Raises:
            ConfigurationError: If required configuration is missing

        Example:
            >>> config = {
            ...     'bucket_name': 'my-bucket',
            ...     'access_key_id': 'AKIA...',
            ...     'secret_access_key': 'wJalr...'
            ... }
            >>> provider = S3Provider(config)
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
        self.endpoint_url = config.get('endpoint_url')  # For S3-compatible services

        self._client = None
        self._connected = False

        logger.debug(
            f"S3Provider initialized (bucket={self.bucket_name}, region={self.region})"
        )

    def connect(self) -> None:
        """
        Connect to AWS S3.

        Initializes boto3 S3 client and validates bucket access.

        Raises:
            StorageError: If connection fails
            ConfigurationError: If credentials are invalid

        Example:
            >>> provider = S3Provider(config)
            >>> provider.connect()
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Create S3 client
            client_config = {
                'aws_access_key_id': self.access_key_id,
                'aws_secret_access_key': self.secret_access_key,
                'region_name': self.region
            }

            if self.endpoint_url:
                client_config['endpoint_url'] = self.endpoint_url

            self._client = boto3.client('s3', **client_config)

            # Test connection by checking bucket existence
            self._client.head_bucket(Bucket=self.bucket_name)

            self._connected = True
            logger.info(f"Connected to S3 bucket: {self.bucket_name}")

        except NoCredentialsError:
            raise ConfigurationError(
                "AWS credentials not found. Please provide valid access keys."
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchBucket':
                raise StorageError(
                    f"Bucket '{self.bucket_name}' not found",
                    details={'error_code': error_code}
                )
            elif error_code == '403' or error_code == 'AccessDenied':
                raise StorageError(
                    f"Access denied to bucket '{self.bucket_name}'",
                    details={'error_code': error_code}
                )
            else:
                raise StorageError(
                    f"Failed to connect to S3: {error_msg}",
                    details={'error_code': error_code}
                )
        except ImportError:
            raise ConfigurationError(
                "boto3 library not installed. Install with: pip install boto3"
            )
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to S3: {str(e)}")

    def disconnect(self) -> None:
        """
        Disconnect from AWS S3.

        Closes the S3 client connection.

        Example:
            >>> provider.disconnect()
        """
        if self._client:
            self._client = None
            self._connected = False
            logger.info("Disconnected from S3")

    def upload(self, local_path: str, remote_path: str, metadata: Optional[Dict] = None) -> None:
        """
        Upload file to S3.

        Args:
            local_path: Path to local file
            remote_path: Destination path in S3 bucket
            metadata: Optional metadata to attach to object

        Raises:
            StorageError: If upload fails
            FileNotFoundError: If local file doesn't exist

        Example:
            >>> provider.upload('data.json', 'datasets/data.json')
            >>> provider.upload('model.pt', 'models/v1/model.pt',
            ...                 metadata={'version': '1.0'})
        """
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

            logger.info(f"Uploaded: {local_path} → s3://{self.bucket_name}/{remote_path}")

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
        Download file from S3.

        Args:
            remote_path: Path to file in S3 bucket
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

            logger.info(f"Downloaded: s3://{self.bucket_name}/{remote_path} → {local_path}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))

            if error_code == '404' or error_code == 'NoSuchKey':
                raise StorageError(
                    f"File not found in S3: {remote_path}",
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
        List files in S3 bucket.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file paths in bucket

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

            logger.debug(f"Listed {len(files)} files from S3 (prefix={prefix})")
            return files

        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            raise StorageError(f"Failed to list files: {error_msg}")
        except Exception as e:
            raise StorageError(f"Unexpected error listing files: {str(e)}")

    def delete(self, remote_path: str) -> None:
        """
        Delete file from S3.

        Args:
            remote_path: Path to file in S3 bucket

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

            logger.info(f"Deleted: s3://{self.bucket_name}/{remote_path}")

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
        Check if file exists in S3.

        Args:
            remote_path: Path to file in S3 bucket

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
            # For other errors, log warning but return False
            logger.warning(f"Error checking file existence: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking file existence: {e}")
            return False

    def get_file_size(self, remote_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            remote_path: Path to file in S3 bucket

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
            remote_path: Path to file in S3 bucket

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
                "Not connected to S3. Call connect() first."
            )

    def __str__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"S3Provider(bucket={self.bucket_name}, region={self.region}, status={status})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"S3Provider(bucket_name='{self.bucket_name}', "
            f"region='{self.region}', connected={self._connected})"
        )
