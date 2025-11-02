"""
Debug Java AST structure
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tree_sitter import Language, Parser
import tree_sitter_java

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

def debug_java_ast():
    print("="*70)
    print("JAVA AST STRUCTURE ANALYSIS")
    print("="*70)
    
    # Create parser
    JAVA_LANGUAGE = Language(tree_sitter_java.language())
    parser = Parser(JAVA_LANGUAGE)
    
    # Parse code
    tree = parser.parse(bytes(JAVA_CODE, "utf8"))
    root = tree.root_node
    
    print(f"\nRoot node type: {root.type}")
    
    # Search for method nodes
    def find_nodes(node, depth=0):
        indent = "  " * depth
        text = JAVA_CODE[node.start_byte:node.end_byte].split('\n')[0][:50]
        print(f"{indent}{node.type}: '{text}...'")
        
        if 'method' in node.type.lower() or 'declaration' in node.type.lower():
            print(f"{indent}  *** POTENTIAL FUNCTION NODE ***")
            for child in node.children:
                child_text = JAVA_CODE[child.start_byte:child.end_byte].split('\n')[0][:40]
                print(f"{indent}    - {child.type}: '{child_text}...'")
        
        if depth < 5:
            for child in node.children:
                find_nodes(child, depth + 1)
    
    find_nodes(root)

if __name__ == "__main__":
    debug_java_ast()
