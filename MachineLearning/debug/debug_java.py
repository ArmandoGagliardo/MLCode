"""
Debug Java extraction
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from module.preprocessing.universal_parser_new import UniversalParser
from module.preprocessing.code_quality_filter import QualityFilter

JAVA_CODE = """
public class Calculator {
    
    public int add(int a, int b) {
        return a + b;
    }
    
    private String formatResult(int result) {
        return "Result: " + result;
    }
}
"""

def debug_java():
    print("="*70)
    print("JAVA EXTRACTION DEBUG")
    print("="*70)
    
    parser = UniversalParser()
    quality_filter = QualityFilter()
    
    results = parser.extract_all_functions(JAVA_CODE, 'java')
    
    print(f"\nExtracted {len(results)} items:")
    
    for i, func in enumerate(results, 1):
        print(f"\n{i}. Type: {func.get('kind', 'unknown')}")
        print(f"   Name: {func.get('name', 'UNNAMED')}")
        print(f"   Signature: {func.get('signature', 'N/A')}")
        print(f"   Body: {len(func.get('body', ''))} chars")
        print(f"   Return type: {func.get('return_type', 'N/A')}")
        
        # Test quality
        full_code = f"{func.get('signature', '')}\n{func.get('body', '')}"
        is_valid = quality_filter.is_valid_code(full_code, language='java')
        print(f"   Quality: {'PASS' if is_valid else 'FAIL'}")

if __name__ == "__main__":
    debug_java()
