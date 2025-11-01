"""
AWS S3 Storage Provider

Amazon S3 is the original cloud storage service.
Pricing: Variable by region, ~$23/TB/month for S3 Standard

Setup:
1. Create AWS account at https://aws.amazon.com/
2. Create S3 bucket
3. Create IAM user with S3 permissions
4. Add credentials to .env:
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_BUCKET=your_bucket_name
   AWS_REGION=us-east-1  # or your region
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging

from ..base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class S3Provider(BaseStorageProvider):
    """AWS S3 storage provider"""

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = 'us-east-1',
        **config
    ):
        """
        Initialize S3 provider

        Args:
            bucket_name: S3 bucket name
            access_key: AWS access key
            secret_key: AWS secret key
            region: AWS region
            **config: Additional configuration
        """
        super().__init__(bucket_name, **config)

        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

    def connect(self) -> bool:
        """Connect to AWS S3"""
        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )

            # Test connection by checking if bucket exists
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to AWS S3 bucket: {self.bucket_name}")

            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to bucket '{self.bucket_name}'")
            else:
                logger.error(f"Failed to connect to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to S3: {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Upload file to S3"""
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
        """Download file from S3"""
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
        """List files in S3 bucket"""
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
        """Delete file from S3"""
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
        """Check if file exists in S3"""
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
    provider = S3Provider(
        bucket_name=os.getenv('AWS_BUCKET', 'my-ml-bucket'),
        access_key=os.getenv('AWS_ACCESS_KEY_ID'),
        secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region=os.getenv('AWS_REGION', 'us-east-1')
    )

    # Connect
    if provider.connect():
        print("Connected to AWS S3!")

        # List files
        files = provider.list_files()
        print(f"Files in bucket: {len(files)}")

        # Get bucket info
        info = provider.get_bucket_info()
        print(f"Bucket info: {info}")
