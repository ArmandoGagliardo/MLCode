"""
Cloudflare R2 Storage Provider

Cloudflare R2 is an S3-compatible storage with zero egress fees.
Pricing: $15/TB/month for storage, $0 for egress (downloads)

Setup:
1. Sign up for Cloudflare at https://www.cloudflare.com/
2. Enable R2 in your account
3. Create a bucket
4. Generate R2 API token
5. Add credentials to .env:
   CLOUDFLARE_R2_ACCOUNT_ID=your_account_id
   CLOUDFLARE_R2_ACCESS_KEY=your_access_key
   CLOUDFLARE_R2_SECRET_KEY=your_secret_key
   CLOUDFLARE_R2_BUCKET=your_bucket_name
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging

from ..base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class CloudflareR2Provider(BaseStorageProvider):
    """Cloudflare R2 storage provider using S3-compatible API"""

    def __init__(
        self,
        bucket_name: str,
        account_id: str,
        access_key: str,
        secret_key: str,
        **config
    ):
        """
        Initialize Cloudflare R2 provider

        Args:
            bucket_name: R2 bucket name
            account_id: Cloudflare account ID
            access_key: R2 access key
            secret_key: R2 secret key
            **config: Additional configuration
        """
        super().__init__(bucket_name, **config)

        self.account_id = account_id
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    def connect(self) -> bool:
        """Connect to Cloudflare R2"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='auto'  # R2 uses 'auto' for region
            )

            # Test connection by checking if bucket exists
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to Cloudflare R2 bucket: {self.bucket_name}")

            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"R2 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to R2 bucket '{self.bucket_name}'")
            else:
                logger.error(f"Failed to connect to Cloudflare R2: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Cloudflare R2: {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Upload file to Cloudflare R2"""
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
        """Download file from Cloudflare R2"""
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
        """List files in Cloudflare R2 bucket"""
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
        """Delete file from Cloudflare R2"""
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
        """Check if file exists in Cloudflare R2"""
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
    provider = CloudflareR2Provider(
        bucket_name=os.getenv('CLOUDFLARE_R2_BUCKET', 'my-ml-bucket'),
        account_id=os.getenv('CLOUDFLARE_R2_ACCOUNT_ID'),
        access_key=os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
        secret_key=os.getenv('CLOUDFLARE_R2_SECRET_KEY')
    )

    # Connect
    if provider.connect():
        print("Connected to Cloudflare R2!")

        # List files
        files = provider.list_files()
        print(f"Files in bucket: {len(files)}")

        # Get bucket info
        info = provider.get_bucket_info()
        print(f"Bucket info: {info}")
