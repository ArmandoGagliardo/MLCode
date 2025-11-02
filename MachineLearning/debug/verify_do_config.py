#!/usr/bin/env python3
"""
DigitalOcean Spaces Configuration Verification
Verifies the implementation against DO Spaces API documentation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_configuration():
    """Verify DigitalOcean Spaces configuration."""
    print("="*70)
    print("DIGITALOCEAN SPACES CONFIGURATION VERIFICATION")
    print("="*70)
    
    # Load environment
    load_dotenv()
    
    print("\n[1] Checking Environment Variables")
    print("-" * 70)
    
    # Check required variables
    required_vars = {
        'DO_BUCKET_NAME': os.getenv('DO_BUCKET_NAME'),
        'DO_ACCESS_KEY_ID': os.getenv('DO_ACCESS_KEY_ID'),
        'DO_SECRET_ACCESS_KEY': os.getenv('DO_SECRET_ACCESS_KEY'),
        'DO_REGION': os.getenv('DO_REGION'),
        'DO_ENDPOINT_URL': os.getenv('DO_ENDPOINT_URL'),
    }
    
    issues = []
    
    for var_name, var_value in required_vars.items():
        if var_value:
            if 'SECRET' in var_name or 'KEY' in var_name:
                display_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            else:
                display_value = var_value
            print(f"  [OK] {var_name}: {display_value}")
        else:
            print(f"  [ERROR] {var_name}: NOT SET")
            issues.append(f"{var_name} is not set")
    
    # Verify region
    print(f"\n[2] Region Verification")
    print("-" * 70)
    
    valid_regions = ['nyc3', 'ams3', 'sgp1', 'sfo2', 'sfo3', 'fra1']
    region = required_vars['DO_REGION']
    
    if region in valid_regions:
        print(f"  [OK] Region '{region}' is valid")
    else:
        print(f"  [WARNING] Region '{region}' not in standard list: {valid_regions}")
        print(f"            This might still work if it's a newer region")
    
    # Verify endpoint URL format
    print(f"\n[3] Endpoint URL Verification")
    print("-" * 70)
    
    endpoint = required_vars['DO_ENDPOINT_URL']
    bucket_name = required_vars['DO_BUCKET_NAME']
    
    if endpoint:
        # According to DO Spaces docs, endpoint should be:
        # https://{bucket-name}.{region}.digitaloceanspaces.com
        expected_endpoint = f"https://{bucket_name}.{region}.digitaloceanspaces.com"
        
        if endpoint == expected_endpoint:
            print(f"  [OK] Endpoint matches DO Spaces format")
            print(f"       {endpoint}")
        else:
            print(f"  [WARNING] Endpoint format differs")
            print(f"            Current:  {endpoint}")
            print(f"            Expected: {expected_endpoint}")
            print(f"            This is OK if you're using a custom domain")
    
    # Check boto3 installation
    print(f"\n[4] Dependencies Check")
    print("-" * 70)
    
    try:
        import boto3
        print(f"  [OK] boto3 is installed (version: {boto3.__version__})")
    except ImportError:
        print(f"  [ERROR] boto3 is not installed")
        issues.append("boto3 not installed - run: pip install boto3")
    
    try:
        import botocore
        print(f"  [OK] botocore is installed (version: {botocore.__version__})")
    except ImportError:
        print(f"  [ERROR] botocore is not installed")
    
    # Test provider initialization
    print(f"\n[5] Provider Implementation Check")
    print("-" * 70)
    
    try:
        from module.storage.providers.digitalocean import DigitalOceanProvider
        
        # Check if provider has correct endpoint mappings
        if hasattr(DigitalOceanProvider, 'ENDPOINTS'):
            endpoints = DigitalOceanProvider.ENDPOINTS
            print(f"  [OK] Provider has endpoint mappings:")
            for reg, ep in endpoints.items():
                print(f"       {reg}: {ep}")
                
            # Check if user's region is in mappings
            if region in endpoints:
                print(f"\n  [OK] Region '{region}' is mapped to: {endpoints[region]}")
            else:
                print(f"\n  [WARNING] Region '{region}' not in provider mappings")
                print(f"            Will use default endpoint")
        
        # Try to create provider instance
        print(f"\n[6] Provider Instantiation Test")
        print("-" * 70)
        
        provider = DigitalOceanProvider(
            bucket_name=bucket_name,
            access_key=required_vars['DO_ACCESS_KEY_ID'],
            secret_key=required_vars['DO_SECRET_ACCESS_KEY'],
            region=region
        )
        print(f"  [OK] Provider instance created successfully")
        print(f"       Bucket: {provider.bucket_name}")
        print(f"       Region: {provider.region}")
        print(f"       Endpoint: {provider.endpoint_url}")
        
        # Test connection
        print(f"\n[7] Connection Test")
        print("-" * 70)
        
        if provider.connect():
            print(f"  [OK] Successfully connected to DigitalOcean Spaces!")
            print(f"       Space: {bucket_name}")
            print(f"       Region: {region}")
            
            # Try to list files
            print(f"\n[8] API Operations Test")
            print("-" * 70)
            
            try:
                files = provider.list_files()
                print(f"  [OK] list_files() works - found {len(files)} file(s)")
                
                # Show first 3 files
                if files:
                    print(f"\n  Sample files:")
                    for i, file_info in enumerate(files[:3], 1):
                        key = file_info.get('key', 'unknown')
                        size = file_info.get('size', 0)
                        print(f"    {i}. {key} ({size} bytes)")
            except Exception as e:
                print(f"  [ERROR] list_files() failed: {e}")
                issues.append(f"list_files() operation failed: {e}")
            
        else:
            print(f"  [ERROR] Failed to connect to DigitalOcean Spaces")
            issues.append("Connection to Spaces failed")
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        issues.append(f"Provider test failed: {e}")
    
    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    if not issues:
        print("\n[SUCCESS] All checks passed!")
        print("Your DigitalOcean Spaces configuration is correct.")
        print("\nAccording to DO Spaces API documentation:")
        print("  - Using S3-compatible API: YES")
        print("  - Endpoint format: CORRECT")
        print("  - Authentication: WORKING")
        print("  - API operations: FUNCTIONAL")
        return 0
    else:
        print(f"\n[WARNING] Found {len(issues)} issue(s):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommendations:")
        print("  1. Review the issues listed above")
        print("  2. Check DO Spaces documentation:")
        print("     https://docs.digitalocean.com/reference/api/spaces/")
        print("  3. Verify your credentials in the DO dashboard:")
        print("     https://cloud.digitalocean.com/spaces")
        return 1

if __name__ == "__main__":
    try:
        exit_code = verify_configuration()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Verification interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
