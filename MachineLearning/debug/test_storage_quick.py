#!/usr/bin/env python3
"""
Quick storage connection test - simplified version.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_storage_quick():
    """Quick test of storage connection."""
    print("="*70)
    print("QUICK STORAGE CONNECTION TEST")
    print("="*70)
    
    # Load environment
    load_dotenv()
    
    # Check provider
    provider = os.getenv('STORAGE_PROVIDER', 'local')
    print(f"\n[1] Storage Provider: {provider}")
    
    if provider == 'local':
        print("    [WARNING] Using local storage only")
        return
    
    # Check credentials
    print(f"\n[2] Checking {provider.upper()} credentials...")
    
    if provider == 'digitalocean':
        bucket = os.getenv('DO_BUCKET_NAME')
        access_key = os.getenv('DO_ACCESS_KEY_ID')
        secret_key = os.getenv('DO_SECRET_ACCESS_KEY')
        region = os.getenv('DO_REGION')
        endpoint = os.getenv('DO_ENDPOINT_URL')
        
        print(f"    Bucket: {bucket}")
        print(f"    Region: {region}")
        print(f"    Endpoint: {endpoint}")
        print(f"    Access Key: {access_key[:15]}..." if access_key else "    Access Key: MISSING")
        print(f"    Secret Key: {'*' * 30}" if secret_key else "    Secret Key: MISSING")
        
        if not all([bucket, access_key, secret_key, region]):
            print("\n    [ERROR] Missing credentials!")
            return
    
    # Test connection
    print(f"\n[3] Testing connection...")
    
    try:
        from module.storage.storage_manager import StorageManager
        
        storage = StorageManager()
        
        if storage.connect():
            print("    [OK] Connected successfully!")
            
            # Try to list files
            print(f"\n[4] Listing files...")
            files = storage.provider.list_files(prefix="")[:5]  # First 5 files
            
            if files:
                print(f"    Found files:")
                for f in files:
                    key = f.get('key', f.get('Key', 'unknown'))
                    print(f"      - {key}")
            else:
                print("    [INFO] No files found (bucket might be empty)")
            
            print(f"\n[OK] Storage connection is working!")
            
        else:
            print("    [ERROR] Connection failed!")
            
    except Exception as e:
        print(f"    [ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_storage_quick()
    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
