from module.preprocessing.universal_parser_new import UniversalParser

code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

p = UniversalParser()
r = p.extract_all_functions(code, 'java')
print(f"Extracted: {len(r)} items")
for i, f in enumerate(r, 1):
    print(f"{i}. {f.get('name')} - kind: {f.get('kind')}")
    print(f"   signature: {f.get('signature')}")
    print(f"   body: {len(f.get('body', ''))} chars")
