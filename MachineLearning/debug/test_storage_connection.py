#!/usr/bin/env python3
"""
Test script for external storage connectivity.
Tests connection, upload, download, list, and delete operations.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from module.storage.storage_manager import StorageManager

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {text}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {text}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {text}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {text}")

def test_configuration():
    """Test 1: Verify configuration is loaded correctly."""
    print_header("TEST 1: Configuration Check")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Get storage provider
        provider = os.getenv('STORAGE_PROVIDER', 'local')
        print_info(f"Storage Provider: {provider}")
        
        if provider == 'local':
            print_warning("Provider set to 'local' - no external storage configured")
            return False
        
        # Check provider-specific credentials
        if provider == 'digitalocean':
            bucket = os.getenv('DO_BUCKET_NAME')
            access_key = os.getenv('DO_ACCESS_KEY_ID')
            secret_key = os.getenv('DO_SECRET_ACCESS_KEY')
            region = os.getenv('DO_REGION')
            endpoint = os.getenv('DO_ENDPOINT_URL')
            
            print_info(f"Bucket: {bucket}")
            print_info(f"Region: {region}")
            print_info(f"Endpoint: {endpoint}")
            print_info(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: Not set")
            print_info(f"Secret Key: {'*' * 20}" if secret_key else "Secret Key: Not set")
            
            if not all([bucket, access_key, secret_key, region]):
                print_error("Missing DigitalOcean credentials!")
                print_info("Required: DO_BUCKET_NAME, DO_ACCESS_KEY_ID, DO_SECRET_ACCESS_KEY, DO_REGION")
                return False
        
        elif provider == 'backblaze':
            bucket = os.getenv('BACKBLAZE_BUCKET_NAME')
            key_id = os.getenv('BACKBLAZE_KEY_ID')
            app_key = os.getenv('BACKBLAZE_APPLICATION_KEY')
            
            print_info(f"Bucket: {bucket}")
            print_info(f"Key ID: {key_id[:10]}..." if key_id else "Key ID: Not set")
            print_info(f"App Key: {'*' * 20}" if app_key else "App Key: Not set")
            
            if not all([bucket, key_id, app_key]):
                print_error("Missing Backblaze credentials!")
                return False
        
        elif provider == 'wasabi':
            bucket = os.getenv('WASABI_BUCKET_NAME')
            access_key = os.getenv('WASABI_ACCESS_KEY_ID')
            secret_key = os.getenv('WASABI_SECRET_ACCESS_KEY')
            
            print_info(f"Bucket: {bucket}")
            print_info(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: Not set")
            
            if not all([bucket, access_key, secret_key]):
                print_error("Missing Wasabi credentials!")
                return False
        
        elif provider == 's3':
            bucket = os.getenv('AWS_BUCKET_NAME')
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            print_info(f"Bucket: {bucket}")
            print_info(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: Not set")
            
            if not all([bucket, access_key, secret_key]):
                print_error("Missing AWS S3 credentials!")
                return False
        
        print_success("Configuration looks good!")
        return True
        
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return False

def test_connection(storage: StorageManager):
    """Test 2: Test connection to storage provider."""
    print_header("TEST 2: Connection Test")
    
    try:
        print_info("Attempting to connect...")
        if storage.connect():
            print_success("Successfully connected to storage!")
            return True
        else:
            print_error("Failed to connect to storage")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_upload(storage: StorageManager):
    """Test 3: Upload a test file."""
    print_header("TEST 3: Upload Test")
    
    try:
        # Create a test file
        test_data = {
            "test": "storage_connection_test",
            "timestamp": datetime.now().isoformat(),
            "message": "This is a test file for storage connectivity"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f, indent=2)
            temp_file = f.name
        
        print_info(f"Created test file: {temp_file}")
        
        # Upload to storage
        remote_path = "test/storage_test.json"
        print_info(f"Uploading to: {remote_path}")
        
        if storage.provider.upload_file(temp_file, remote_path):
            print_success(f"Successfully uploaded: {remote_path}")
            
            # Cleanup local temp file
            os.unlink(temp_file)
            return True
        else:
            print_error("Upload failed")
            os.unlink(temp_file)
            return False
            
    except Exception as e:
        print_error(f"Upload error: {e}")
        return False

def test_list(storage: StorageManager):
    """Test 4: List files in storage."""
    print_header("TEST 4: List Files Test")
    
    try:
        print_info("Listing files in 'test/' prefix...")
        files = storage.provider.list_files(prefix="test/")
        
        if files:
            print_success(f"Found {len(files)} file(s):")
            for i, file_info in enumerate(files[:10], 1):  # Show first 10
                key = file_info.get('key', file_info.get('Key', 'unknown'))
                print(f"  {i}. {key}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
            return True
        else:
            print_warning("No files found (this might be expected if bucket is empty)")
            return True  # Not necessarily an error
            
    except Exception as e:
        print_error(f"List error: {e}")
        return False

def test_download(storage: StorageManager):
    """Test 5: Download the test file."""
    print_header("TEST 5: Download Test")
    
    try:
        remote_path = "test/storage_test.json"
        
        # Create temp directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "downloaded_test.json")
            
            print_info(f"Downloading from: {remote_path}")
            print_info(f"Downloading to: {local_path}")
            
            if storage.provider.download_file(remote_path, local_path):
                print_success("Download successful!")
                
                # Verify content
                with open(local_path, 'r') as f:
                    data = json.load(f)
                    print_info(f"File content: {json.dumps(data, indent=2)}")
                
                return True
            else:
                print_error("Download failed")
                return False
                
    except Exception as e:
        print_error(f"Download error: {e}")
        return False

def test_exists(storage: StorageManager):
    """Test 6: Check if file exists."""
    print_header("TEST 6: File Existence Test")
    
    try:
        remote_path = "test/storage_test.json"
        
        print_info(f"Checking if exists: {remote_path}")
        if storage.provider.file_exists(remote_path):
            print_success(f"File exists: {remote_path}")
            return True
        else:
            print_warning(f"File does not exist: {remote_path}")
            return False
            
    except Exception as e:
        print_error(f"Existence check error: {e}")
        return False

def test_delete(storage: StorageManager):
    """Test 7: Delete the test file."""
    print_header("TEST 7: Delete Test")
    
    try:
        remote_path = "test/storage_test.json"
        
        print_info(f"Deleting: {remote_path}")
        if storage.provider.delete_file(remote_path):
            print_success(f"Successfully deleted: {remote_path}")
            
            # Verify deletion
            if not storage.provider.file_exists(remote_path):
                print_success("Verified: File no longer exists")
                return True
            else:
                print_warning("File still exists after deletion")
                return False
        else:
            print_error("Delete failed")
            return False
            
    except Exception as e:
        print_error(f"Delete error: {e}")
        return False

def main():
    """Run all storage tests."""
    print_header("EXTERNAL STORAGE CONNECTION TEST")
    
    print_info("This script will test:")
    print("  1. Configuration verification")
    print("  2. Connection to storage provider")
    print("  3. Upload a test file")
    print("  4. List files in storage")
    print("  5. Download the test file")
    print("  6. Check file existence")
    print("  7. Delete the test file\n")
    
    # Test results
    results = {}
    
    # Test 1: Configuration
    results['configuration'] = test_configuration()
    if not results['configuration']:
        print_error("\nConfiguration test failed. Please check your .env file.")
        print_info("Make sure STORAGE_PROVIDER is set and credentials are correct.")
        sys.exit(1)
    
    # Initialize storage manager
    try:
        print_info("\nInitializing StorageManager...")
        storage = StorageManager()
    except Exception as e:
        print_error(f"Failed to initialize StorageManager: {e}")
        sys.exit(1)
    
    # Test 2: Connection
    results['connection'] = test_connection(storage)
    if not results['connection']:
        print_error("\nConnection test failed. Cannot proceed with other tests.")
        sys.exit(1)
    
    # Test 3: Upload
    results['upload'] = test_upload(storage)
    
    # Test 4: List
    results['list'] = test_list(storage)
    
    # Test 5: Download
    results['download'] = test_download(storage)
    
    # Test 6: Exists
    results['exists'] = test_exists(storage)
    
    # Test 7: Delete
    results['delete'] = test_delete(storage)
    
    # Print summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {test_name.ljust(20)}: {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.ENDC}")
    
    if passed_tests == total_tests:
        print_success("\nAll tests passed! Your storage connection is working perfectly.")
        return 0
    else:
        print_warning(f"\n{total_tests - passed_tests} test(s) failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}[!] Test interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
