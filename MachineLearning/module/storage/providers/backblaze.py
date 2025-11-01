"""
Backblaze B2 Storage Provider

Backblaze B2 is a cost-effective cloud storage solution.
Pricing: ~$5/TB/month for storage, $10/TB for download

Setup:
1. Create account at https://www.backblaze.com/b2/
2. Create bucket
3. Create application key with read/write access
4. Add credentials to .env:
   BACKBLAZE_KEY_ID=your_key_id
   BACKBLAZE_APPLICATION_KEY=your_app_key
   BACKBLAZE_BUCKET=your_bucket_name
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging

from ..base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class BackblazeProvider(BaseStorageProvider):
    """Backblaze B2 storage provider using S3-compatible API"""

    # Backblaze B2 S3-compatible endpoint
    ENDPOINT_URL = "https://s3.us-west-004.backblazeb2.com"  # Update region as needed

    def __init__(
        self,
        bucket_name: str,
        key_id: str,
        application_key: str,
        endpoint_url: Optional[str] = None,
        **config
    ):
        """
        Initialize Backblaze B2 provider

        Args:
            bucket_name: B2 bucket name
            key_id: Application key ID
            application_key: Application key
            endpoint_url: Optional custom endpoint URL
            **config: Additional configuration
        """
        super().__init__(bucket_name, **config)

        self.key_id = key_id
        self.application_key = application_key
        self.endpoint_url = endpoint_url or self.ENDPOINT_URL

    def connect(self) -> bool:
        """Connect to Backblaze B2"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.application_key
            )

            # Test connection by listing buckets
            response = self.client.list_buckets()
            logger.info(f"✅ Connected to Backblaze B2 (found {len(response['Buckets'])} buckets)")

            # Check if our bucket exists
            bucket_exists = any(b['Name'] == self.bucket_name for b in response['Buckets'])

            if not bucket_exists:
                logger.warning(f"⚠️  Bucket '{self.bucket_name}' not found")
                return False

            return True

        except ClientError as e:
            logger.error(f"❌ Failed to connect to Backblaze: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Backblaze: {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Upload file to Backblaze B2"""
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

            logger.info(f"✅ Uploaded: {local_path} -> {remote_path}")
            return True

        except ClientError as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            return False

    def download_file(
        self,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download file from Backblaze B2"""
        try:
            self.client.download_file(
                self.bucket_name,
                remote_path,
                local_path
            )

            logger.info(f"✅ Downloaded: {remote_path} -> {local_path}")
            return True

        except ClientError as e:
            logger.error(f"❌ Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading file: {e}")
            return False

    def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[Dict]:
        """List files in Backblaze B2 bucket"""
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
            logger.error(f"❌ Failed to list files: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error listing files: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from Backblaze B2"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            logger.info(f"✅ Deleted: {remote_path}")
            return True

        except ClientError as e:
            logger.error(f"❌ Delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting file: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in Backblaze B2"""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"❌ Error checking file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking file existence: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    import os

    logging.basicConfig(level=logging.INFO)

    # Initialize provider
    provider = BackblazeProvider(
        bucket_name=os.getenv('BACKBLAZE_BUCKET', 'my-ml-bucket'),
        key_id=os.getenv('BACKBLAZE_KEY_ID'),
        application_key=os.getenv('BACKBLAZE_APPLICATION_KEY')
    )

    # Connect
    if provider.connect():
        print("✅ Connected to Backblaze!")

        # List files
        files = provider.list_files()
        print(f"Files in bucket: {len(files)}")

        # Get bucket info
        info = provider.get_bucket_info()
        print(f"Bucket info: {info}")
