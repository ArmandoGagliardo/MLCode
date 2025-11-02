#!/usr/bin/env python3
"""
Minimal test - just extraction, no quality filter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser

def test_extraction():
    parser = UniversalParser()
    
    code = 'def hello():\n    return "world"'
    print(f"Testing Python extraction...")
    print(f"Code: {code}")
    
    print("\nCalling extract_all_functions...")
    functions = parser.extract_all_functions(code, 'python')
    
    print(f"Extracted: {len(functions)} functions")
    
    for func in functions:
        print(f"  Name: {func.get('name')}")
        print(f"  Output: {func.get('output')[:100]}")

if __name__ == "__main__":
    test_extraction()
