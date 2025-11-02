"""
Debug Quality Filter per capire perché fallisce con JS/Go/Rust
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter

TEST_CODE = {
    'javascript': """
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
""",
    'go': """
func Add(a, b int) int {
    return a + b
}
""",
    'rust': """
pub fn calculate_sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}
"""
}

def test_language(language: str, code: str):
    print(f"\n{'='*70}")
    print(f"Testing {language.upper()}")
    print(f"{'='*70}\n")
    
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    # Extract functions
    results = parser.extract_all_functions(code, language)
    print(f"✅ Extracted {len(results)} functions")
    
    if not results:
        print(f"❌ No functions extracted for {language}")
        return
    
    for i, func in enumerate(results, 1):
        name = func.get('name', 'UNNAMED')
        signature = func.get('signature', '')
        body = func.get('body', '')
        params = func.get('parameters', [])
        
        print(f"\n--- Function {i}: {name} ---")
        print(f"Signature: '{signature}'")
        print(f"Body: {len(body)} chars, {len(body.splitlines())} lines")
        print(f"Parameters: {len(params)} - {params}")
        
        # Combine for full code
        full_code = f"{signature}\n{body}"
        
        print(f"\nQuality checks:")
        
        # Individual checks
        checks = {
            'valid_length': quality_filter.is_valid_length(full_code),
            'valid_line_count': quality_filter.is_valid_line_count(full_code),
            'no_bad_patterns': not quality_filter.has_bad_patterns(full_code),
            'sufficient_complexity': quality_filter.has_sufficient_complexity(full_code),
            'not_boilerplate': quality_filter.is_not_boilerplate(full_code),
            'meaningful_content': quality_filter.has_meaningful_content(full_code),
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}: {passed}")
        
        # Overall validation
        print(f"\n  Testing with language='{language}':")
        is_valid = quality_filter.is_valid_code(full_code, language=language)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"  {status} Overall validation: {is_valid}")
        
        # Try with language='python' to see difference
        if language != 'python':
            print(f"\n  Testing with language='python' (for comparison):")
            is_valid_as_python = quality_filter.is_valid_code(full_code, language='python')
            status = "✅ PASS" if is_valid_as_python else "❌ FAIL"
            print(f"  {status} As Python: {is_valid_as_python}")

if __name__ == "__main__":
    for lang, code in TEST_CODE.items():
        test_language(lang, code)
    
    print("\n\n" + "="*70)
    print("🎯 ANALISI")
    print("="*70)
    print("Se quality_filter.is_valid_code() passa con language corretta")
    print("ma il repository test fallisce, il problema è altrove:")
    print("  1. Estrazione parametri incompleta")
    print("  2. Formato signature non standard")
    print("  3. Body malformato")
    print("  4. File reali hanno syntax diverse")
