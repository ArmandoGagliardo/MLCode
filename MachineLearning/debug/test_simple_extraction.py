#!/usr/bin/env python3
"""
Test extraction with simple code samples
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter

# Simple, valid test cases
SIMPLE_TESTS = {
    'python': 'def hello():\n    return "world"',
    'javascript': 'function hello() { return "world"; }',
    'java': 'public class Test {\n    public void hello() {\n        System.out.println("Hello");\n    }\n}',
    'go': 'func Hello() string {\n    return "world"\n}',
    'rust': 'fn hello() -> String {\n    "world".to_string()\n}',
    'ruby': 'def hello\n    "world"\nend',
    'cpp': 'int hello() {\n    return 42;\n}'
}

def main():
    print("="*70)
    print("SIMPLE EXTRACTION TEST")
    print("="*70)
    
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    results = {}
    
    for language in sorted(SIMPLE_TESTS.keys()):
        code = SIMPLE_TESTS[language]
        
        print(f"\n{'='*70}")
        print(f"Testing {language.upper()}")
        print(f"{'='*70}")
        print(f"Code:\n{code}\n")
        
        # Extract
        functions = parser.extract_all_functions(code, language)
        
        print(f"Extracted: {len(functions)} items")
        
        valid_count = 0
        for i, func in enumerate(functions, 1):
            name = func.get('name', 'Unknown')
            print(f"\n  [{i}] {name}")
            print(f"      Type: {func.get('task_type')}")
            print(f"      Has name: {bool(func.get('name'))}")
            print(f"      Has body: {bool(func.get('body'))}")
            print(f"      Has signature: {bool(func.get('signature'))}")
            print(f"      Has output: {bool(func.get('output'))}")
            
            if func.get('signature'):
                print(f"      Signature: {func['signature'][:100]}")
            
            if func.get('output'):
                print(f"      Output length: {len(func['output'])} chars")
                print(f"      Output preview:")
                for line in func['output'].split('\n')[:5]:
                    print(f"        {line}")
                
                # Quality check
                is_valid = quality_filter.is_valid_code(func['output'], language)
                print(f"      Quality: {'PASS ✓' if is_valid else 'FAIL ✗'}")
                
                if not is_valid:
                    # Show why it failed
                    score = quality_filter.calculate_quality_score(func['output'])
                    print(f"      Quality score: {score:.2f}")
                    
                    # Try individual checks
                    has_structure = quality_filter._has_code_structure(func['output'])
                    print(f"      Has structure: {has_structure}")
                    
                    has_bad_patterns = quality_filter._has_bad_patterns(func['output'])
                    print(f"      Has bad patterns: {has_bad_patterns}")
                    
                    is_too_short = len(func['output'].strip()) < quality_filter.min_code_length
                    print(f"      Too short: {is_too_short} (len={len(func['output'].strip())})")
                
                if is_valid:
                    valid_count += 1
        
        results[language] = {
            'extracted': len(functions),
            'valid': valid_count
        }
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for lang in sorted(results.keys()):
        data = results[lang]
        status = "✅" if data['valid'] > 0 else "❌"
        print(f"{status} {lang:<12} Extracted: {data['extracted']:<3} Valid: {data['valid']:<3}")
    
    total_extracted = sum(r['extracted'] for r in results.values())
    total_valid = sum(r['valid'] for r in results.values())
    
    print(f"\nTotal: {total_valid}/{total_extracted} valid functions")
    print("="*70)

if __name__ == "__main__":
    main()
