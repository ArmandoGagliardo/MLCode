#!/usr/bin/env python3
"""
Debug quality filter to see why it fails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.code_quality_filter import QualityFilter
from module.preprocessing.universal_parser_new import UniversalParser

# Test code that should pass
code = '''
def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    result = a + b
    return result
'''

def main():
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    print("="*70)
    print("QUALITY FILTER DEBUG")
    print("="*70)
    
    print("\nOriginal code:")
    print(code)
    
    # Extract
    functions = parser.extract_all_functions(code, 'python')
    print(f"\nExtracted {len(functions)} functions")
    
    if functions:
        func = functions[0]
        output = func.get('output', '')
        
        print(f"\nFunction name: {func.get('name')}")
        print(f"\nExtracted output:")
        print(repr(output))
        print(f"\nFormatted output:")
        print(output)
        
        # Test each quality check
        print("\n" + "="*70)
        print("QUALITY CHECKS")
        print("="*70)
        
        # Length
        length = len(output.strip())
        is_valid_length = quality_filter.is_valid_length(output)
        print(f"\n1. Length: {length} chars")
        print(f"   Min required: {quality_filter.min_length}")
        print(f"   Result: {'✓ PASS' if is_valid_length else '✗ FAIL'}")
        
        # Lines
        lines = [line for line in output.split('\n') if line.strip()]
        is_valid_lines = quality_filter.is_valid_line_count(output)
        print(f"\n2. Line count: {len(lines)} lines")
        print(f"   Min required: {quality_filter.min_lines}")
        print(f"   Result: {'✓ PASS' if is_valid_lines else '✗ FAIL'}")
        
        # Bad patterns
        has_bad = quality_filter.has_bad_patterns(output)
        print(f"\n3. Bad patterns: {'Found' if has_bad else 'None'}")
        print(f"   Result: {'✗ FAIL' if has_bad else '✓ PASS'}")
        
        # Python syntax
        is_valid_syntax = quality_filter.is_valid_python_syntax(output)
        print(f"\n4. Python syntax:")
        print(f"   Result: {'✓ PASS' if is_valid_syntax else '✗ FAIL'}")
        if not is_valid_syntax:
            try:
                import ast
                ast.parse(output)
            except SyntaxError as e:
                print(f"   Syntax error: {e}")
        
        # Complexity
        has_complexity = quality_filter.has_sufficient_complexity(output)
        print(f"\n5. Complexity:")
        print(f"   Result: {'✓ PASS' if has_complexity else '✗ FAIL'}")
        
        # Not boilerplate
        not_boilerplate = quality_filter.is_not_boilerplate(output)
        print(f"\n6. Not boilerplate:")
        print(f"   Result: {'✓ PASS' if not_boilerplate else '✗ FAIL'}")
        
        # Meaningful content
        has_meaningful = quality_filter.has_meaningful_content(output)
        print(f"\n7. Meaningful content:")
        print(f"   Result: {'✓ PASS' if has_meaningful else '✗ FAIL'}")
        
        # Overall
        print("\n" + "="*70)
        is_valid = quality_filter.is_valid_code(output, 'python')
        print(f"OVERALL: {'✓ PASS' if is_valid else '✗ FAIL'}")
        print("="*70)

if __name__ == "__main__":
    main()
