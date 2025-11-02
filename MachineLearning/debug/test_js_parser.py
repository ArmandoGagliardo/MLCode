#!/usr/bin/env python3
"""
Test JavaScript parser with real function code
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser

# JavaScript code with various function types
js_code = '''
// Regular function
function add(a, b) {
    return a + b;
}

// Arrow function
const multiply = (x, y) => x * y;

// Class with methods
class Calculator {
    constructor() {
        this.value = 0;
    }
    
    add(n) {
        this.value += n;
        return this;
    }
    
    getResult() {
        return this.value;
    }
}

// Async function
async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
'''

def main():
    print("="*70)
    print("JAVASCRIPT PARSER TEST")
    print("="*70)
    
    print("\nJavaScript code:")
    print(js_code)
    
    print("\n" + "="*70)
    print("PARSING")
    print("="*70)
    
    parser = UniversalParser()
    functions = parser.extract_all_functions(js_code, 'javascript')
    
    print(f"\nExtracted: {len(functions)} items")
    
    for i, func in enumerate(functions, 1):
        print(f"\n[{i}] {func.get('name')}")
        print(f"    Type: {func.get('task_type')}")
        print(f"    Signature: {func.get('signature', '')[:80]}")
        print(f"    Output preview:")
        output = func.get('output', '')
        for line in output.split('\n')[:5]:
            print(f"      {line}")
    
    if len(functions) == 0:
        print("\n❌ NO FUNCTIONS EXTRACTED!")
    else:
        print(f"\n✅ JavaScript parser works! Extracted {len(functions)} items")

if __name__ == "__main__":
    main()
