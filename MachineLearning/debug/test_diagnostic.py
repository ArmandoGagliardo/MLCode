#!/usr/bin/env python3
"""
Diagnostic Test - Check why no functions are extracted
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable DEBUG logging
logging.basicConfig(level=logging.DEBUG)

from github_repo_processor import GitHubRepoProcessor
from module.preprocessing.universal_parser_new import UniversalParser

def diagnostic_test():
    """Test extraction on a single file"""
    
    print("="*70)
    print("DIAGNOSTIC TEST - FUNCTION EXTRACTION")
    print("="*70)
    
    # Clone a small repo
    print("\n[1] Cloning black repository...")
    processor = GitHubRepoProcessor(cloud_save=False)
    local_path = processor.clone_repository('https://github.com/psf/black')
    
    if not local_path:
        print("[ERROR] Clone failed")
        return
    
    print(f"  [OK] Cloned to: {local_path}")
    
    # Find Python files
    print("\n[2] Finding Python files...")
    code_files = processor.find_code_files(local_path, languages=['python'])
    print(f"  Found {len(code_files)} Python files")
    
    if not code_files:
        print("  [ERROR] No files found")
        return
    
    # Test extraction on first few files
    print("\n[3] Testing function extraction on first 3 files...")
    
    for i, file_path in enumerate(code_files[:3]):
        print(f"\n  File {i+1}: {os.path.basename(file_path)}")
        print(f"    Path: {file_path}")
        
        # Extract functions
        functions = processor.extract_functions_from_file(file_path)
        print(f"    Raw functions extracted: {len(functions)}")
        
        if functions:
            print(f"    Sample function:")
            func = functions[0]
            print(f"      Name: {func.get('name', 'N/A')}")
            print(f"      Language: {func.get('language', 'N/A')}")
            print(f"      Has body: {'Yes' if func.get('body') else 'No'}")
            print(f"      Body length: {len(func.get('body', ''))} chars")
            print(f"      Body preview: {func.get('body', '')[:100]}...")
        
        # Check filters
        filtered = []
        for func in functions:
            # Check name and body
            if not func.get('name') or not func.get('body'):
                print(f"    [SKIP] Function skipped: missing name or body")
                continue
            
            # Check duplicate
            is_dup = processor.duplicate_manager.is_duplicate(
                func['hash'],
                {'function': func['name']}
            )
            if is_dup:
                print(f"    [DUP] Function '{func['name']}' is duplicate")
                continue
            
            # Check quality
            full_code = func.get('signature', '') + '\n' + func.get('body', '')
            is_valid = processor.quality_filter.is_valid_code(full_code.strip())
            if not is_valid:
                print(f"    [QUALITY] Function '{func['name']}' failed quality check")
                print(f"      Full code (first 200 chars): {full_code[:200]}")
                continue
            
            filtered.append(func)
        
        print(f"    Functions after filtering: {len(filtered)}")
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)

if __name__ == "__main__":
    diagnostic_test()
