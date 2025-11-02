"""
Test Rust extraction dopo l'implementazione
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

fn process_item(item: &str) -> Result<String, Error> {
    Ok(item.to_uppercase())
}

impl MyStruct {
    pub fn new(value: i32) -> Self {
        Self { value }
    }
    
    fn helper(&self) -> i32 {
        self.value * 2
    }
}
"""

def test_rust():
    print("="*70)
    print("RUST EXTRACTION TEST")
    print("="*70)
    
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    # Extract functions
    results = parser.extract_all_functions(RUST_CODE, 'rust')
    
    print(f"\nExtracted {len(results)} items:")
    
    for i, func in enumerate(results, 1):
        print(f"\n{i}. {func.get('name', 'UNNAMED')}")
        print(f"   Signature: {func.get('signature', 'N/A')}")
        print(f"   Body: {len(func.get('body', ''))} chars")
        print(f"   Return type: {func.get('return_type', 'N/A')}")
        
        # Test quality
        full_code = f"{func.get('signature', '')}\n{func.get('body', '')}"
        is_valid = quality_filter.is_valid_code(full_code, language='rust')
        print(f"   Quality check: {'PASS' if is_valid else 'FAIL'}")
    
    print(f"\n{'='*70}")
    print(f"RESULT: {'SUCCESS' if len(results) > 0 else 'FAIL'}")
    print(f"{'='*70}")

if __name__ == "__main__":
    test_rust()
