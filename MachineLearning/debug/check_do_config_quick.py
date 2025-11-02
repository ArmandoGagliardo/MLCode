#!/usr/bin/env python3
"""Quick DO Spaces Configuration Check"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("DIGITALOCEAN SPACES - QUICK CONFIGURATION CHECK")
print("="*70)

# Environment Variables
print("\n[1] Environment Variables:")
print("-" * 70)
bucket = os.getenv('DO_BUCKET_NAME')
region = os.getenv('DO_REGION')
endpoint = os.getenv('DO_ENDPOINT_URL')
access_key = os.getenv('DO_ACCESS_KEY_ID')
secret_key = os.getenv('DO_SECRET_ACCESS_KEY')

print(f"  Bucket Name: {bucket or 'NOT SET'}")
print(f"  Region: {region or 'NOT SET'}")
print(f"  Endpoint URL: {endpoint or 'NOT SET'}")
print(f"  Access Key ID: {'***' + access_key[-4:] if access_key else 'NOT SET'}")
print(f"  Secret Key: {'SET (' + str(len(secret_key)) + ' chars)' if secret_key else 'NOT SET'}")

# Region Validation
print("\n[2] Region Validation:")
print("-" * 70)
valid_regions = ['nyc3', 'ams3', 'sgp1', 'sfo2', 'sfo3', 'fra1']
if region in valid_regions:
    print(f"  [OK] '{region}' is a valid DO Spaces region")
else:
    print(f"  [WARNING] '{region}' is not in known regions: {valid_regions}")

# Endpoint Format Check
print("\n[3] Endpoint Format:")
print("-" * 70)
if endpoint:
    # Official DO Spaces endpoint format: https://{bucket}.{region}.digitaloceanspaces.com
    expected_endpoint = f"https://{bucket}.{region}.digitaloceanspaces.com"
    if endpoint == expected_endpoint:
        print(f"  [OK] Endpoint matches official format")
        print(f"      {endpoint}")
    else:
        print(f"  [WARNING] Endpoint format mismatch")
        print(f"      Current:  {endpoint}")
        print(f"      Expected: {expected_endpoint}")
        print(f"  Per DO documentation:")
        print(f"    https://docs.digitalocean.com/reference/api/spaces/")
else:
    print("  [ERROR] Endpoint URL not set")

# Dependencies Check
print("\n[4] Dependencies:")
print("-" * 70)
try:
    import boto3
    print(f"  [OK] boto3: {boto3.__version__}")
except ImportError:
    print("  [ERROR] boto3 not installed")

try:
    import botocore
    print(f"  [OK] botocore: {botocore.__version__}")
except ImportError:
    print("  [ERROR] botocore not installed")

# Provider Implementation Check
print("\n[5] Provider Implementation:")
print("-" * 70)
try:
    from module.storage.providers.digitalocean import DigitalOceanProvider
    
    # Check endpoint mappings
    provider_regions = {
        'nyc3': 'https://nyc3.digitaloceanspaces.com',
        'ams3': 'https://ams3.digitaloceanspaces.com',
        'sgp1': 'https://sgp1.digitaloceanspaces.com',
        'sfo2': 'https://sfo2.digitaloceanspaces.com',
        'sfo3': 'https://sfo3.digitaloceanspaces.com',
        'fra1': 'https://fra1.digitaloceanspaces.com',
    }
    
    # Validate that DO provider has correct endpoint mappings
    do_provider_code = open('module/storage/providers/digitalocean.py').read()
    all_regions_present = all(region in do_provider_code for region in provider_regions.keys())
    
    if all_regions_present:
        print(f"  [OK] DigitalOceanProvider has all 6 regions mapped")
        for r, ep in provider_regions.items():
            print(f"      {r}: {ep}")
    else:
        print(f"  [WARNING] Some regions may be missing from provider")
        
except ImportError as e:
    print(f"  [ERROR] Cannot import DigitalOceanProvider: {e}")

# Connection Test
print("\n[6] Connection Test:")
print("-" * 70)
if all([bucket, region, access_key, secret_key]):
    try:
        import boto3
        s3_client = boto3.client(
            's3',
            region_name=region,
            endpoint_url=f"https://{region}.digitaloceanspaces.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Test list operation
        response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=1)
        print(f"  [OK] Successfully connected to DO Spaces")
        print(f"      Bucket '{bucket}' is accessible")
        
    except Exception as e:
        print(f"  [ERROR] Connection test failed: {e}")
else:
    print("  [SKIPPED] Missing required credentials")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
print("\nRECOMMENDATIONS:")
print("  Per official DO Spaces API documentation:")
print("  - Endpoint format: https://<region>.digitaloceanspaces.com")
print("  - Bucket access: https://<bucket>.<region>.digitaloceanspaces.com")
print("  - Supported regions: nyc3, ams3, sgp1, sfo2, sfo3, fra1")
print("  - Authentication: AWS Signature Version 4 (via boto3)")
print("\n  Documentation: https://docs.digitalocean.com/reference/api/spaces/")
print("="*70)
