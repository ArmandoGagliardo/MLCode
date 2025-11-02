"""
Debug Rust AST structure per capire i nodi corretti
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tree_sitter import Language, Parser
import tree_sitter_rust

# Simple Rust code
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

def debug_rust_ast():
    print("="*70)
    print("RUST AST STRUCTURE ANALYSIS")
    print("="*70)
    
    # Create parser
    RUST_LANGUAGE = Language(tree_sitter_rust.language())
    parser = Parser(RUST_LANGUAGE)
    
    # Parse code
    tree = parser.parse(bytes(RUST_CODE, "utf8"))
    root = tree.root_node
    
    print(f"\nRoot node type: {root.type}")
    print(f"Children: {len(root.children)}\n")
    
    # Analyze structure
    def print_tree(node, indent=0, max_depth=6):
        if indent > max_depth:
            return
        
        prefix = "  " * indent
        node_text = RUST_CODE[node.start_byte:node.end_byte]
        
        # Show first line only for readability
        first_line = node_text.split('\n')[0][:60]
        
        print(f"{prefix}{node.type}: '{first_line}...'")
        
        # Look for function-related nodes
        if 'function' in node.type.lower():
            print(f"{prefix}  *** FOUND FUNCTION NODE: {node.type} ***")
            
            # Show children
            for child in node.children:
                child_text = RUST_CODE[child.start_byte:child.end_byte].split('\n')[0][:40]
                print(f"{prefix}    - {child.type}: '{child_text}...'")
        
        # Recurse
        for child in node.children:
            print_tree(child, indent + 1, max_depth)
    
    print("AST Tree:")
    print_tree(root, max_depth=5)
    
    # Search for function nodes
    print("\n" + "="*70)
    print("SEARCHING FOR FUNCTION NODES")
    print("="*70)
    
    def find_functions(node):
        functions = []
        
        if 'function' in node.type.lower():
            functions.append(node)
        
        for child in node.children:
            functions.extend(find_functions(child))
        
        return functions
    
    functions = find_functions(root)
    print(f"\nFound {len(functions)} function nodes:")
    
    for i, func_node in enumerate(functions, 1):
        print(f"\n{i}. Type: {func_node.type}")
        
        # Analyze children
        print("   Children:")
        for child in func_node.children:
            child_text = RUST_CODE[child.start_byte:child.end_byte].split('\n')[0][:50]
            print(f"     - {child.type}: '{child_text}...'")

if __name__ == "__main__":
    debug_rust_ast()
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Identificare il node type corretto per funzioni Rust")
    print("2. Identificare il node type per il body")
    print("3. Aggiornare function_parser.py con i nodi Rust")
