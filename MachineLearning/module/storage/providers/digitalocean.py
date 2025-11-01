"""
DigitalOcean Spaces Storage Provider

DigitalOcean Spaces is an S3-compatible object storage service.
Pricing: $5/month for 250GB storage + 1TB transfer

Setup:
1. Create DigitalOcean account at https://www.digitalocean.com/
2. Create a Space
3. Generate Spaces access key
4. Add credentials to .env:
   DO_SPACES_KEY=your_access_key
   DO_SPACES_SECRET=your_secret_key
   DO_SPACES_NAME=your_space_name
   DO_SPACES_REGION=nyc3  # or your region
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging

from ..base_provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class DigitalOceanProvider(BaseStorageProvider):
    """DigitalOcean Spaces storage provider using S3-compatible API"""

    # DigitalOcean Spaces endpoints by region
    ENDPOINTS = {
        'nyc3': 'https://nyc3.digitaloceanspaces.com',
        'ams3': 'https://ams3.digitaloceanspaces.com',
        'sgp1': 'https://sgp1.digitaloceanspaces.com',
        'sfo2': 'https://sfo2.digitaloceanspaces.com',
        'sfo3': 'https://sfo3.digitaloceanspaces.com',
        'fra1': 'https://fra1.digitaloceanspaces.com',
    }

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = 'nyc3',
        **config
    ):
        """
        Initialize DigitalOcean Spaces provider

        Args:
            bucket_name: Space name
            access_key: Spaces access key
            secret_key: Spaces secret key
            region: Space region
            **config: Additional configuration
        """
        super().__init__(bucket_name, **config)

        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.endpoint_url = self.ENDPOINTS.get(region, self.ENDPOINTS['nyc3'])

    def connect(self) -> bool:
        """Connect to DigitalOcean Spaces"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )

            # Test connection by checking if space exists
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to DigitalOcean Space: {self.bucket_name}")

            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Space '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to Space '{self.bucket_name}'")
            else:
                logger.error(f"Failed to connect to DigitalOcean Spaces: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to DigitalOcean Spaces: {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Upload file to DigitalOcean Spaces"""
        try:
            extra_args = {'ACL': 'private'}  # Default to private

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
        """Download file from DigitalOcean Spaces"""
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
        """List files in DigitalOcean Space"""
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
        """Delete file from DigitalOcean Spaces"""
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
        """Check if file exists in DigitalOcean Spaces"""
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
    provider = DigitalOceanProvider(
        bucket_name=os.getenv('DO_SPACES_NAME', 'my-ml-space'),
        access_key=os.getenv('DO_SPACES_KEY'),
        secret_key=os.getenv('DO_SPACES_SECRET'),
        region=os.getenv('DO_SPACES_REGION', 'nyc3')
    )

    # Connect
    if provider.connect():
        print("Connected to DigitalOcean Spaces!")

        # List files
        files = provider.list_files()
        print(f"Files in Space: {len(files)}")

        # Get Space info
        info = provider.get_bucket_info()
        print(f"Space info: {info}")
