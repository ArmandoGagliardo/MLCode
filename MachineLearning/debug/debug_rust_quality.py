"""
Debug quality check per Rust
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter

RUST_CODE = """
pub fn calculate_sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}
"""

def debug_rust_quality():
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    results = parser.extract_all_functions(RUST_CODE, 'rust')
    
    if not results:
        print("No functions extracted")
        return
    
    func = results[0]
    print(f"Function: {func.get('name')}")
    print(f"Signature: '{func.get('signature')}'")
    print(f"Body: '{func.get('body')}'")
    
    full_code = f"{func.get('signature', '')}\n{func.get('body', '')}"
    print(f"\nFull code to validate:\n{full_code}")
    print(f"\nLength: {len(full_code)} chars")
    print(f"Lines: {len(full_code.splitlines())} lines")
    
    # Individual checks
    print("\nIndividual checks:")
    print(f"  valid_length: {quality_filter.is_valid_length(full_code)}")
    print(f"  valid_line_count: {quality_filter.is_valid_line_count(full_code)}")
    print(f"  no_bad_patterns: {not quality_filter.has_bad_patterns(full_code)}")
    print(f"  sufficient_complexity: {quality_filter.has_sufficient_complexity(full_code)}")
    print(f"  not_boilerplate: {quality_filter.is_not_boilerplate(full_code)}")
    print(f"  meaningful_content: {quality_filter.has_meaningful_content(full_code)}")
    
    print(f"\nOverall validation: {quality_filter.is_valid_code(full_code, language='rust')}")

if __name__ == "__main__":
    debug_rust_quality()
