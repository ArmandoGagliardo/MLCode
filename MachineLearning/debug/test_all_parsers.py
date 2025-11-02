#!/usr/bin/env python3
"""
Deep Parser Verification - Tests all language parsers in detail
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter
import json

# Real-world code samples
TEST_SAMPLES = {
    'python': '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def process(self):
        """Process the data"""
        return [x * 2 for x in self.data]
''',
    'javascript': '''
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
        return true;
    }
}

const sum = (a, b) => a + b;
''',
    'java': '''
public class Calculator {
    private int result;
    
    public Calculator() {
        this.result = 0;
    }
    
    public int add(int a, int b) {
        return a + b;
    }
    
    public int multiply(int a, int b) {
        int product = 0;
        for(int i = 0; i < b; i++) {
            product += a;
        }
        return product;
    }
}
''',
    'cpp': '''
#include <vector>
#include <string>

class StringProcessor {
private:
    std::string data;
public:
    StringProcessor(std::string d) : data(d) {}
    
    int length() {
        return data.length();
    }
    
    std::string uppercase() {
        std::string result = data;
        for(char& c : result) {
            c = toupper(c);
        }
        return result;
    }
};
''',
    'go': '''
package main

func Sum(numbers []int) int {
    total := 0
    for _, num := range numbers {
        total += num
    }
    return total
}

type Rectangle struct {
    Width  float64
    Height float64
}

func (r *Rectangle) Area() float64 {
    return r.Width * r.Height
}
''',
    'rust': '''
fn is_even(n: i32) -> bool {
    n % 2 == 0
}

struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fn new(x: f64, y: f64) -> Point {
        Point { x, y }
    }
    
    fn distance(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }
}
''',
    'ruby': '''
class BankAccount
  attr_reader :balance
  
  def initialize(initial_balance = 0)
    @balance = initial_balance
  end
  
  def deposit(amount)
    @balance += amount
  end
  
  def withdraw(amount)
    if @balance >= amount
      @balance -= amount
      true
    else
      false
    end
  end
end

def greet(name)
  "Hello, #{name}!"
end
'''
}

def test_language_parser(language, code, parser, quality_filter):
    """Test parser for a specific language"""
    print(f"\n{'='*70}")
    print(f"🔍 TESTING {language.upper()} PARSER")
    print('='*70)
    
    result = {
        'language': language,
        'extracted': 0,
        'valid': 0,
        'functions': [],
        'errors': []
    }
    
    try:
        # Extract functions
        functions = parser.extract_all_functions(code, language)
        result['extracted'] = len(functions)
        
        print(f"\n✓ Extracted {len(functions)} items")
        
        if not functions:
            print("  [WARNING] No functions extracted!")
            result['errors'].append("No functions extracted")
            return result
        
        # Analyze each function
        for i, func in enumerate(functions, 1):
            name = func.get('name', 'Unknown')
            func_type = func.get('task_type', 'unknown')
            
            print(f"\n  [{i}] {name}")
            print(f"      Type: {func_type}")
            
            # Check required fields
            checks = {
                'name': bool(func.get('name')),
                'body': bool(func.get('body')),
                'signature': bool(func.get('signature')),
                'output': bool(func.get('output'))
            }
            
            for field, present in checks.items():
                symbol = "✓" if present else "✗"
                print(f"      {symbol} {field}: {'present' if present else 'MISSING'}")
            
            # Preview signature
            if func.get('signature'):
                sig = func['signature'].replace('\n', ' ')[:60]
                print(f"      Signature: {sig}...")
            
            # Quality check
            code_to_check = func.get('output', '')
            if code_to_check:
                is_valid = quality_filter.is_valid_code(code_to_check, language)
                symbol = "✓" if is_valid else "✗"
                print(f"      {symbol} Quality: {'PASS' if is_valid else 'FAIL'}")
                
                if is_valid:
                    result['valid'] += 1
                    result['functions'].append({
                        'name': name,
                        'type': func_type,
                        'lines': len(code_to_check.split('\n'))
                    })
                else:
                    result['errors'].append(f"{name}: Quality check failed")
            else:
                print(f"      ✗ Quality: SKIP (no output)")
                result['errors'].append(f"{name}: No output code")
        
        # Summary for this language
        print(f"\n{'─'*70}")
        if result['valid'] > 0:
            print(f"✅ {language.upper()}: {result['valid']}/{result['extracted']} valid functions")
        else:
            print(f"❌ {language.upper()}: No valid functions extracted!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        result['errors'].append(f"Exception: {str(e)}")
    
    return result

def main():
    """Run comprehensive parser tests"""
    print("="*70)
    print("COMPREHENSIVE PARSER VERIFICATION TEST")
    print("="*70)
    
    # Initialize
    print("\n[Initializing components...]")
    parser = UniversalParser()
    quality_filter = QualityFilter()
    print(f"✓ Parser loaded with {len(parser.languages)} languages")
    print(f"✓ Supported: {', '.join(parser.languages)}")
    
    # Test each language
    results = []
    for language in sorted(TEST_SAMPLES.keys()):
        if language not in parser.languages:
            print(f"\n⚠️  SKIP {language.upper()}: Not supported by parser")
            continue
        
        code = TEST_SAMPLES[language]
        result = test_language_parser(language, code, parser, quality_filter)
        results.append(result)
    
    # Overall summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    total_extracted = sum(r['extracted'] for r in results)
    total_valid = sum(r['valid'] for r in results)
    languages_working = sum(1 for r in results if r['valid'] > 0)
    languages_tested = len(results)
    
    print(f"\nLanguages tested: {languages_tested}")
    print(f"Languages working: {languages_working}")
    print(f"Languages failing: {languages_tested - languages_working}")
    print(f"\nTotal extracted: {total_extracted}")
    print(f"Total valid: {total_valid}")
    print(f"Success rate: {(total_valid/total_extracted*100 if total_extracted > 0 else 0):.1f}%")
    
    # Per-language breakdown
    print(f"\n{'Language':<15} {'Extracted':<12} {'Valid':<10} {'Status':<10}")
    print("─" * 70)
    
    for result in results:
        lang = result['language']
        extracted = result['extracted']
        valid = result['valid']
        status = "✅ OK" if valid > 0 else "❌ FAIL"
        
        print(f"{lang:<15} {extracted:<12} {valid:<10} {status:<10}")
        
        if result['errors']:
            for error in result['errors'][:2]:  # Show first 2 errors
                print(f"  └─ {error}")
    
    # Detailed function list
    print(f"\n{'='*70}")
    print("VALID FUNCTIONS EXTRACTED")
    print('='*70)
    
    for result in results:
        if result['functions']:
            print(f"\n{result['language'].upper()}:")
            for func in result['functions']:
                print(f"  • {func['name']} ({func['type']}) - {func['lines']} lines")
    
    print("\n" + "="*70)
    
    if total_valid > 0:
        print("✅ VERIFICATION PASSED - Parser system is working!")
    else:
        print("❌ VERIFICATION FAILED - No valid functions extracted!")
    
    print("="*70)
    
    return total_valid > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
