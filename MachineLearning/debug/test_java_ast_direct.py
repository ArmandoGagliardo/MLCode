from module.preprocessing.universal_parser_new import UniversalParser
from tree_sitter import Parser, Language
import tree_sitter_java

code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

# Test diretto con tree-sitter
JAVA_LANGUAGE = Language(tree_sitter_java.language())
parser = Parser(JAVA_LANGUAGE)
tree = parser.parse(bytes(code, "utf8"))
root = tree.root_node

print("AST Nodes:")
def print_nodes(node, depth=0):
    print("  " * depth + f"{node.type}")
    if depth < 4:
        for child in node.children:
            print_nodes(child, depth + 1)

print_nodes(root)

# Now test with UniversalParser
print("\n\nUniversalParser extraction:")
p = UniversalParser()
results = p.parse(code, 'java')
print(f"Extracted: {len(results)} items")

for r in results:
    print(f"- {r.get('kind')}: {r.get('name')} - sig: {r.get('signature')}")
