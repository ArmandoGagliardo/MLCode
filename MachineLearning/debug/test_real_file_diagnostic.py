#!/usr/bin/env python3
"""
Diagnostic: Clone a repo and analyze first JS/Go file
"""

import sys
import os
import subprocess
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.preprocessing.universal_parser_new import UniversalParser
from pathlib import Path

def clone_and_analyze(repo_url, language, file_extension):
    """Clone repo and analyze first file"""
    
    # Clone to temp
    temp_dir = tempfile.mkdtemp(prefix="test_")
    repo_name = repo_url.split('/')[-1]
    local_path = os.path.join(temp_dir, repo_name)
    
    print(f"Cloning {repo_url}...")
    result = subprocess.run(
        ['git', 'clone', '--depth', '1', repo_url, local_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Clone failed: {result.stderr}")
        return
    
    print(f"✓ Cloned to {local_path}")
    
    # Find first file
    for root, dirs, files in os.walk(local_path):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'test', 'tests']]
        
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(root, file)
                
                # Read file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if len(code) < 100:  # Skip tiny files
                        continue
                    
                    print(f"\n{'='*70}")
                    print(f"Analyzing: {file}")
                    print(f"Path: {file_path}")
                    print(f"Size: {len(code)} chars")
                    print('='*70)
                    
                    # Show first 20 lines
                    print("\nFirst 20 lines:")
                    for i, line in enumerate(code.split('\n')[:20], 1):
                        print(f"{i:3}: {line}")
                    
                    # Try to parse
                    print(f"\n{'='*70}")
                    print(f"PARSING WITH {language.upper()} PARSER")
                    print('='*70)
                    
                    parser = UniversalParser()
                    functions = parser.extract_all_functions(code, language)
                    
                    print(f"\nExtracted: {len(functions)} items")
                    
                    if functions:
                        for i, func in enumerate(functions[:5], 1):  # Show first 5
                            print(f"\n[{i}] {func.get('name')}")
                            print(f"    Type: {func.get('task_type')}")
                            print(f"    Signature: {func.get('signature', '')[:80]}")
                    else:
                        print("⚠️  No functions extracted!")
                        
                        # Debug: Show what tree-sitter sees
                        from tree_sitter import Language, Parser as TSParser
                        
                        if language == 'javascript':
                            import tree_sitter_javascript
                            lang = Language(tree_sitter_javascript.language())
                        elif language == 'go':
                            import tree_sitter_go
                            lang = Language(tree_sitter_go.language())
                        else:
                            return
                        
                        ts_parser = TSParser()
                        ts_parser.language = lang
                        tree = ts_parser.parse(bytes(code, "utf8"))
                        
                        # Collect node types
                        node_types = set()
                        def collect_types(node):
                            node_types.add(node.type)
                            for child in node.children:
                                collect_types(child)
                        
                        collect_types(tree.root_node)
                        
                        print(f"\nTree-sitter found {len(node_types)} node types:")
                        for ntype in sorted(node_types):
                            print(f"  • {ntype}")
                        
                        # Check expected types
                        expected_map = {
                            'javascript': ['function_declaration', 'method_definition', 'class_declaration', 'arrow_function'],
                            'go': ['function_declaration', 'method_declaration']
                        }
                        
                        expected = expected_map.get(language, [])
                        found = [t for t in expected if t in node_types]
                        missing = [t for t in expected if t not in node_types]
                        
                        print(f"\nExpected: {expected}")
                        print(f"Found: {found if found else 'NONE'}")
                        if missing:
                            print(f"Missing: {missing}")
                    
                    return  # Analyze only first file
                    
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    continue
    
    print("No suitable files found")

def main():
    print("="*70)
    print("DIAGNOSTIC: Real File Analysis")
    print("="*70)
    
    # Test JavaScript
    print("\n" + "="*70)
    print("JAVASCRIPT TEST")
    print("="*70)
    clone_and_analyze('https://github.com/lodash/lodash', 'javascript', '.js')
    
    # Test Go
    print("\n\n" + "="*70)
    print("GO TEST")
    print("="*70)
    clone_and_analyze('https://github.com/spf13/cobra', 'go', '.go')
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
