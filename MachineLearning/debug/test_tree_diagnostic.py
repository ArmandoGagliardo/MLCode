#!/usr/bin/env python3
"""
Deep diagnostic test for tree-sitter parsers
Shows AST structure and node types found
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tree_sitter import Language, Parser

# Simple test cases
TESTS = {
    'python': 'def hello():\n    return "world"',
    'javascript': 'function hello() { return "world"; }',
    'java': 'public class Test { public void hello() {} }',
    'go': 'func Hello() string { return "world" }',
    'rust': 'fn hello() -> String { "world".to_string() }',
    'ruby': 'def hello\n  "world"\nend',
    'cpp': 'int hello() { return 42; }'
}

def show_tree(node, indent=0, max_depth=5):
    """Show tree structure"""
    if indent > max_depth:
        return
    
    prefix = "  " * indent
    text = node.text[:50] if node.text else ""
    print(f"{prefix}[{node.type}] {text.decode('utf-8') if text else ''}")
    
    for child in node.children:
        show_tree(child, indent + 1, max_depth)

def test_parser(language, code):
    """Test parser and show what it finds"""
    print(f"\n{'='*70}")
    print(f"Testing {language.upper()}")
    print('='*70)
    print(f"Code: {code[:100]}")
    
    try:
        # Load language
        module_name = f"tree_sitter_{language}"
        module = __import__(module_name)
        
        if not hasattr(module, 'language'):
            print(f"❌ No language() function in {module_name}")
            return
        
        lang_capsule = module.language()
        lang = Language(lang_capsule)
        
        # Parse
        parser = Parser()
        parser.language = lang
        tree = parser.parse(bytes(code, "utf8"))
        root = tree.root_node
        
        print(f"\n✓ Parsed successfully")
        print(f"Root node type: {root.type}")
        print(f"Number of children: {len(root.children)}")
        
        # Show tree structure
        print(f"\nAST Structure:")
        show_tree(root, max_depth=4)
        
        # Collect all node types
        node_types = set()
        def collect_types(node):
            node_types.add(node.type)
            for child in node.children:
                collect_types(child)
        
        collect_types(root)
        
        print(f"\nAll node types found ({len(node_types)}):")
        for ntype in sorted(node_types):
            print(f"  • {ntype}")
        
        # Check what we're looking for
        kind_map = {
            "python": ["function_definition", "class_definition"],
            "cpp": ["function_definition", "class_specifier"],
            "java": ["method_declaration", "constructor_declaration", "class_declaration"],
            "javascript": ["function_declaration", "method_definition", "class_declaration", "arrow_function"],
            "go": ["function_declaration", "method_declaration"],
            "ruby": ["method", "class"],
            "rust": ["function_item", "impl_item"],
        }
        
        expected = kind_map.get(language, [])
        found = [t for t in expected if t in node_types]
        missing = [t for t in expected if t not in node_types]
        
        print(f"\nExpected node types: {expected}")
        print(f"Found: {found if found else 'NONE'}")
        if missing:
            print(f"Missing: {missing}")
        
        if found:
            print(f"✅ Parser can extract from this code")
        else:
            print(f"❌ Parser cannot find expected nodes!")
            
    except ImportError as e:
        print(f"❌ Module not installed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("="*70)
    print("TREE-SITTER DIAGNOSTIC TEST")
    print("="*70)
    
    for language, code in TESTS.items():
        test_parser(language, code)
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
