"""
Debug extraction pipeline per capire dove falliscono JS/Go/Rust
"""
import sys
from pathlib import Path

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter

# Test samples
TEST_CODE = {
    'javascript': """
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

export async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
}
""",
    'go': """
package main

func Add(a, b int) int {
    return a + b
}

func ProcessData(data []string) error {
    for _, item := range data {
        fmt.Println(item)
    }
    return nil
}
""",
    'rust': """
pub fn calculate_sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}

fn process_item(item: &str) -> Result<String, Error> {
    Ok(item.to_uppercase())
}
"""
}

def debug_language(language: str, code: str):
    print(f"\n{'='*70}")
    print(f"🔍 DEBUGGING {language.upper()}")
    print(f"{'='*70}\n")
    
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    # Step 1: Parse
    print("STEP 1: Parsing...")
    try:
        results = parser.extract_all_functions(code, language)
        print(f"✅ Parsed: {len(results)} items found")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('name', 'UNNAMED')} - Type: {result.get('type', 'UNKNOWN')}")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return
    
    if not results:
        print("⚠️  No items extracted by parser")
        return
    
    # Step 2: Check each result
    print(f"\nSTEP 2: Analyzing {len(results)} extracted items...")
    for i, result in enumerate(results, 1):
        print(f"\n--- Item {i}: {result.get('name', 'UNNAMED')} ---")
        
        # Check signature
        signature = result.get('signature', '')
        print(f"Signature ({len(signature)} chars):")
        print(f"  '{signature[:100]}{'...' if len(signature) > 100 else ''}'")
        
        # Check body
        body = result.get('body', '')
        print(f"Body ({len(body)} chars, {len(body.splitlines())} lines):")
        if body:
            body_preview = body[:200].replace('\n', '\\n')
            print(f"  '{body_preview}{'...' if len(body) > 200 else ''}'")
        else:
            print(f"  ⚠️  EMPTY BODY")
        
        # Check parameters
        params = result.get('parameters', [])
        print(f"Parameters: {len(params)} - {params}")
        
        # Check return type
        return_type = result.get('return_type', '')
        print(f"Return type: '{return_type}'")
    
    # Step 3: Quality filter
    print(f"\nSTEP 3: Quality Filter...")
    passed = 0
    failed = 0
    
    for i, result in enumerate(results, 1):
        name = result.get('name', 'UNNAMED')
        print(f"\n  Testing {i}. {name}...")
        
        # Test individual checks
        signature = result.get('signature', '')
        body = result.get('body', '')
        
        # Check 1: Has content
        has_content = bool(signature and body)
        print(f"    Has content: {has_content} (sig={len(signature)}, body={len(body)})")
        
        if not has_content:
            print(f"    ❌ FAIL: Missing signature or body")
            failed += 1
            continue
        
        # Check 2: Signature validation
        try:
            sig_valid = quality_filter._is_valid_signature(signature)
            print(f"    Signature valid: {sig_valid}")
            if not sig_valid:
                print(f"    ❌ FAIL: Invalid signature")
                failed += 1
                continue
        except Exception as e:
            print(f"    ❌ FAIL: Signature validation error: {e}")
            failed += 1
            continue
        
        # Check 3: Body validation  
        try:
            body_valid = quality_filter._is_valid_body(body)
            print(f"    Body valid: {body_valid}")
            if not body_valid:
                print(f"    ❌ FAIL: Invalid body")
                failed += 1
                continue
        except Exception as e:
            print(f"    ❌ FAIL: Body validation error: {e}")
            failed += 1
            continue
        
        # Check 4: Meaningful content
        try:
            has_meaningful = quality_filter._has_meaningful_content(body)
            print(f"    Meaningful content: {has_meaningful}")
            if not has_meaningful:
                print(f"    ❌ FAIL: No meaningful content")
                failed += 1
                continue
        except Exception as e:
            print(f"    ❌ FAIL: Meaningful content error: {e}")
            failed += 1
            continue
        
        # Check 5: Full validation
        try:
            is_valid = quality_filter.is_valid_function(result)
            print(f"    Full validation: {is_valid}")
            if is_valid:
                print(f"    ✅ PASS")
                passed += 1
            else:
                print(f"    ❌ FAIL: Full validation failed")
                failed += 1
        except Exception as e:
            print(f"    ❌ FAIL: Full validation error: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY for {language.upper()}:")
    print(f"  Parsed: {len(results)} items")
    print(f"  Passed quality filter: {passed}")
    print(f"  Failed quality filter: {failed}")
    print(f"  Success rate: {passed}/{len(results)} ({100*passed/len(results) if results else 0:.0f}%)")
    print(f"{'='*70}")

if __name__ == "__main__":
    for language, code in TEST_CODE.items():
        debug_language(language, code)
    
    print("\n\n" + "="*70)
    print("🎯 NEXT STEPS:")
    print("="*70)
    print("1. Identifica quale validation check fallisce")
    print("2. Controlla se quality filter è Python-specific")
    print("3. Considera di disabilitare alcuni check per non-Python")
    print("4. O implementa language-specific validators")
