"""
Wasabi Storage Provider

Wasabi is a cost-effective S3-compatible cloud storage solution.
Pricing: ~$6/TB/month for storage, no egress fees

Setup:
1. Create account at https://wasabi.com/
2. Create bucket
3. Create access key
4. Add credentials to .env:
   WASABI_ACCESS_KEY=your_access_key
   WASABI_SECRET_KEY=your_secret_key
   WASABI_BUCKET=your_bucket_name
   WASABI_REGION=us-east-1  # or your region
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging

from ..base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class WasabiProvider(BaseStorageProvider):
    """Wasabi storage provider using S3-compatible API"""

    # Wasabi S3-compatible endpoints by region
    ENDPOINTS = {
        'us-east-1': 'https://s3.wasabisys.com',
        'us-east-2': 'https://s3.us-east-2.wasabisys.com',
        'us-west-1': 'https://s3.us-west-1.wasabisys.com',
        'eu-central-1': 'https://s3.eu-central-1.wasabisys.com',
        'ap-northeast-1': 'https://s3.ap-northeast-1.wasabisys.com',
    }

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = 'us-east-1',
        **config
    ):
        """
        Initialize Wasabi provider

        Args:
            bucket_name: Wasabi bucket name
            access_key: Access key
            secret_key: Secret key
            region: Wasabi region
            **config: Additional configuration
        """
        super().__init__(bucket_name, **config)

        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.endpoint_url = self.ENDPOINTS.get(region, self.ENDPOINTS['us-east-1'])

    def connect(self) -> bool:
        """Connect to Wasabi"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )

            # Test connection by listing buckets
            response = self.client.list_buckets()
            logger.info(f"Connected to Wasabi (found {len(response['Buckets'])} buckets)")

            # Check if our bucket exists
            bucket_exists = any(b['Name'] == self.bucket_name for b in response['Buckets'])

            if not bucket_exists:
                logger.warning(f"Bucket '{self.bucket_name}' not found")
                return False

            return True

        except ClientError as e:
            logger.error(f"Failed to connect to Wasabi: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Wasabi: {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Upload file to Wasabi"""
        try:
            extra_args = {}

            if metadata:
                extra_args['Metadata'] = metadata

            self.client.upload_file(
                local_path,
                self.bucket_name,
                remote_path,
                ExtraArgs=extra_args
            )

            logger.info(f"Uploaded: {local_path} -> {remote_path}")
            return True

        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(
        self,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download file from Wasabi"""
        try:
            self.client.download_file(
                self.bucket_name,
                remote_path,
                local_path
            )

            logger.info(f"Downloaded: {remote_path} -> {local_path}")
            return True

        except ClientError as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[Dict]:
        """List files in Wasabi bucket"""
        try:
            params = {'Bucket': self.bucket_name}

            if prefix:
                params['Prefix'] = prefix

            response = self.client.list_objects_v2(**params)

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })

            return files

        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from Wasabi"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"Deleted: {remote_path}")
            return True

        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in Wasabi"""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    import os

    logging.basicConfig(level=logging.INFO)

    # Initialize provider
    provider = WasabiProvider(
        bucket_name=os.getenv('WASABI_BUCKET', 'my-ml-bucket'),
        access_key=os.getenv('WASABI_ACCESS_KEY'),
        secret_key=os.getenv('WASABI_SECRET_KEY'),
        region=os.getenv('WASABI_REGION', 'us-east-1')
    )

    # Connect
    if provider.connect():
        print("Connected to Wasabi!")

        # List files
        files = provider.list_files()
        print(f"Files in bucket: {len(files)}")

        # Get bucket info
        info = provider.get_bucket_info()
        print(f"Bucket info: {info}")
