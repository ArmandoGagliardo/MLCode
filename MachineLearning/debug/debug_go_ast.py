#!/usr/bin/env python3
"""
Debug Go AST structure
"""

from tree_sitter import Language, Parser
import tree_sitter_go

go_code = '''func Add(a int, b int) int {
    return a + b
}'''

def show_tree(node, indent=0):
    """Show tree structure with node types"""
    prefix = "  " * indent
    text_preview = node.text[:40].decode('utf-8') if node.text and len(node.text) < 100 else ""
    print(f"{prefix}[{node.type}] {text_preview}")
    
    for child in node.children:
        show_tree(child, indent + 1)

# Parse
lang = Language(tree_sitter_go.language())
parser = Parser()
parser.language = lang

tree = parser.parse(bytes(go_code, "utf8"))
root = tree.root_node

print("="*70)
print("GO AST STRUCTURE")
print("="*70)
print(f"Code:\n{go_code}\n")
print("="*70)
print("AST Tree:")
print("="*70)
show_tree(root)

# Find function node
def find_function(node):
    if node.type == "function_declaration":
        return node
    for child in node.children:
        result = find_function(child)
        if result:
            return result
    return None

func_node = find_function(root)
if func_node:
    print("\n" + "="*70)
    print("FUNCTION NODE CHILDREN")
    print("="*70)
    
    for child in func_node.children:
        text = child.text.decode('utf-8') if child.text and len(child.text) < 100 else "[long]"
        print(f"  • {child.type}: {text}")
