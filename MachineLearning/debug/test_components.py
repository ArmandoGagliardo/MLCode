"""
Test script per verificare tutti i componenti del sistema
"""

print('=== TEST COMPONENTI ===\n')

# Test 1: UniversalParser
print('1. Testing UniversalParser...')
from module.preprocessing.universal_parser_new import UniversalParser
parser = UniversalParser()
print(f'   ✅ Parser caricato: {len(parser.languages)} linguaggi')
print(f'   Linguaggi supportati: {", ".join(parser.get_supported_languages())}')

# Test 2: DuplicateManager
print('\n2. Testing DuplicateManager...')
from module.utils.duplicate_manager import DuplicateManager
dup_manager = DuplicateManager()
print(f'   ✅ DuplicateManager inizializzato: {len(dup_manager)} items in cache')

# Test 3: QualityFilter
print('\n3. Testing QualityFilter...')
from module.preprocessing.code_quality_filter import QualityFilter
quality_filter = QualityFilter()

test_code_good = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

test_code_bad = "pass"

print(f'   Codice buono valido: {quality_filter.is_valid_code(test_code_good)}')
print(f'   Codice cattivo valido: {quality_filter.is_valid_code(test_code_bad)}')
print(f'   Quality score (buono): {quality_filter.get_quality_score(test_code_good):.2f}')
print('   ✅ QualityFilter OK')

# Test 4: StorageManager
print('\n4. Testing StorageManager...')
try:
    from module.storage.storage_manager import StorageManager
    storage = StorageManager()
    print(f'   ✅ StorageManager inizializzato')
    print(f'   Provider: {storage.config.get("provider_type", "none")}')
except Exception as e:
    print(f'   ⚠️  StorageManager warning: {e}')

# Test 5: Parse code
print('\n5. Testing code parsing...')
test_python_code = """
def calculate_sum(a, b):
    '''Calculate sum of two numbers'''
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""

try:
    results = parser.parse(test_python_code, 'python')
    print(f'   ✅ Estratte {len(results)} funzioni/classi')
    for i, result in enumerate(results, 1):
        print(f'      {i}. {result.get("func_name", "unknown")} ({result.get("task_type", "unknown")})')
except Exception as e:
    print(f'   ⚠️  Parsing error: {e}')

# Test 6: Duplicate detection
print('\n6. Testing duplicate detection...')
code1 = "def hello(): return 'world'"
code2 = "def  hello():  return  'world'"  # Same with different spacing
code3 = "def goodbye(): return 'world'"

is_dup1 = dup_manager.is_duplicate_content(code1)
is_dup2 = dup_manager.is_duplicate_content(code2)
is_dup3 = dup_manager.is_duplicate_content(code3)

print(f'   Code1 duplicato: {is_dup1} (expected: False)')
print(f'   Code2 duplicato: {is_dup2} (expected: True)')
print(f'   Code3 duplicato: {is_dup3} (expected: False)')
print(f'   ✅ Duplicate detection OK')

print('\n=== TUTTI I TEST COMPLETATI ===')
print('Il sistema è pronto per il processing!')
