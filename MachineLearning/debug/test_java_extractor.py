from module.preprocessing.function_parser import FunctionExtractor
from tree_sitter import Parser, Language
import tree_sitter_java

code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

JAVA_LANGUAGE = Language(tree_sitter_java.language())
parser = Parser(JAVA_LANGUAGE)
tree = parser.parse(bytes(code, "utf8"))

# Find method_declaration node
def find_method(node):
    if node.type == "method_declaration":
        return node
    for child in node.children:
        result = find_method(child)
        if result:
            return result
    return None

method_node = find_method(tree.root_node)
if method_node:
    print(f"Found method node: {method_node.type}")
    
    extractor = FunctionExtractor(code)
    info = extractor.extract(method_node, 'java')
    
    print(f"\nExtracted info:")
    for key, value in info.items():
        if key == 'body':
            print(f"  {key}: {len(value)} chars")
        else:
            print(f"  {key}: {value}")
    
    # Test validation
    name = info.get("name", "")
    print(f"\nValidation:")
    print(f"  has name: {bool(name)}")
    print(f"  has body: {bool(info.get('body'))}")
    print(f"  name.isidentifier(): {name.isidentifier() if name else 'N/A'}")
    print(f"  has special chars: {any(c in name for c in '():') if name else 'N/A'}")
else:
    print("No method_declaration node found")
