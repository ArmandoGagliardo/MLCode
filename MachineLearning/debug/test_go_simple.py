#!/usr/bin/env python3
"""
Test specific Go file with known functions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser

# Simple Go code with function
go_code = '''package main

import "fmt"

func Add(a int, b int) int {
    return a + b
}

func main() {
    result := Add(5, 3)
    fmt.Println(result)
}
'''

def main():
    print("="*70)
    print("GO PARSER DEBUG")
    print("="*70)
    
    print("\nGo code:")
    print(go_code)
    
    print("\n" + "="*70)
    print("PARSING")
    print("="*70)
    
    parser = UniversalParser()
    functions = parser.extract_all_functions(go_code, 'go')
    
    print(f"\nExtracted: {len(functions)} functions")
    
    for i, func in enumerate(functions, 1):
        print(f"\n[{i}] {func.get('name')}")
        print(f"    Type: {func.get('task_type')}")
        print(f"    Signature: {func.get('signature')}")
        print(f"    Body preview: {func.get('body', '')[:100]}")
        print(f"    Output preview: {func.get('output', '')[:150]}")
    
    if len(functions) == 0:
        print("\n❌ NO FUNCTIONS EXTRACTED!")
        print("This confirms there's a bug in the Go parser")
    else:
        print(f"\n✅ Go parser works! Extracted {len(functions)} functions")

if __name__ == "__main__":
    main()
