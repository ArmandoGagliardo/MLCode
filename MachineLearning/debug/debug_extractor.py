#!/usr/bin/env python3
"""
Debug what FunctionExtractor returns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tree_sitter import Language, Parser
from module.preprocessing.function_parser import FunctionExtractor

code = '''def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    result = a + b
    return result'''

# Load Python parser
import tree_sitter_python
lang = Language(tree_sitter_python.language())
parser = Parser()
parser.language = lang

# Parse
tree = parser.parse(bytes(code, "utf8"))
root = tree.root_node

# Find function node
def find_function(node):
    if node.type == "function_definition":
        return node
    for child in node.children:
        result = find_function(child)
        if result:
            return result
    return None

func_node = find_function(root)

if func_node:
    print("Found function node")
    print(f"Node type: {func_node.type}")
    print(f"Start: {func_node.start_point}")
    print(f"End: {func_node.end_point}")
    
    # Extract with FunctionExtractor
    extractor = FunctionExtractor(code)
    info = extractor.extract(func_node, 'python')
    
    print("\n" + "="*70)
    print("EXTRACTED INFO")
    print("="*70)
    
    for key, value in info.items():
        if key == 'body':
            print(f"\n{key}:")
            print(f"  repr: {repr(value)}")
            print(f"  formatted:")
            for i, line in enumerate(value.split('\n'), 1):
                print(f"    {i}: |{line}|")
        else:
            print(f"{key}: {value}")

