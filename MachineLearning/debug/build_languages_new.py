#!/usr/bin/env python
"""
Build script for tree-sitter languages using modern API.
No compilation needed with pip-installed language bindings!
"""

import os
import sys
from pathlib import Path

# Try to import pre-built bindings
try:
    # Test imports
    import tree_sitter
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjs

    print("OK: Using pre-built language bindings (recommended)")
    print("   Tree-sitter language packages are already installed.")
    print("   No compilation needed!")

    # Check for additional languages
    languages_available = []
    languages_to_check = {
        "Python": "tree_sitter_python",
        "JavaScript": "tree_sitter_javascript",
        "Java": "tree_sitter_java",
        "C++": "tree_sitter_cpp",
        "Go": "tree_sitter_go",
        "PHP": "tree_sitter_php",
        "Ruby": "tree_sitter_ruby",
        "Rust": "tree_sitter_rust",
    }

    for lang_name, module_name in languages_to_check.items():
        try:
            __import__(module_name)
            languages_available.append(lang_name)
        except ImportError:
            pass

    if languages_available:
        print(f"\n   Available languages: {', '.join(languages_available)}")

except ImportError:
    print("WARNING: Pre-built language bindings not found.")
    print("   Install them with:")
    print("   pip install tree-sitter-python tree-sitter-javascript tree-sitter-java")
    print("   pip install tree-sitter-cpp tree-sitter-go tree-sitter-php")
    print("   pip install tree-sitter-ruby tree-sitter-rust")

# Check for vendor directory with old-style grammars
vendor_path = Path("vendor")
if vendor_path.exists():
    print(f"\nINFO: Found vendor directory with grammar sources")
    print("   For manual compilation, you would need to:")
    print("   1. Install tree-sitter-cli: pip install tree-sitter-cli")
    print("   2. Use Language.build_library() in older versions")
    print("   3. Or use the new tree_sitter.binding module in newer versions")
    print("\n   But with modern tree-sitter, using pip packages is recommended!")

# Create a test script
test_script = '''#!/usr/bin/env python
"""Quick test for tree-sitter setup."""

try:
    import tree_sitter
    print(f"OK: tree-sitter version {tree_sitter.__version__}")

    # Test language imports
    languages = []

    try:
        import tree_sitter_python
        languages.append("Python")
    except ImportError:
        pass

    try:
        import tree_sitter_javascript
        languages.append("JavaScript")
    except ImportError:
        pass

    try:
        import tree_sitter_java
        languages.append("Java")
    except ImportError:
        pass

    if languages:
        print(f"OK: Available languages: {', '.join(languages)}")

        # Test parsing
        import tree_sitter_python as tsp
        from tree_sitter import Parser

        parser = Parser(tsp.language())
        tree = parser.parse(b"def hello(): pass")
        print(f"OK: Successfully parsed Python code!")
    else:
        print("WARNING: No language packages installed")
        print("   Install with:")
        print("   pip install tree-sitter-python tree-sitter-javascript")

except ImportError as e:
    print(f"ERROR: tree-sitter not installed: {e}")
    print("   Install with: pip install tree-sitter")
    print("   Then install language packages:")
    print("   pip install tree-sitter-python tree-sitter-javascript")
except Exception as e:
    print(f"ERROR: Unexpected error: {e}")
'''

# Save test script with UTF-8 encoding
with open("test_tree_sitter.py", "w", encoding="utf-8") as f:
    f.write(test_script)

print("\nINFO: Created test_tree_sitter.py")
print("   Run it to verify your setup: python test_tree_sitter.py")

# Update requirements
print("\nREMINDER: Make sure your requirements.txt includes:")
print("   tree-sitter>=0.20.0")
print("   tree-sitter-python")
print("   tree-sitter-javascript")
print("   tree-sitter-java")
print("   tree-sitter-cpp")
print("   tree-sitter-go")
print("   tree-sitter-php")
print("   tree-sitter-ruby")
print("   tree-sitter-rust")

print("\nTo install all language packages at once:")
print("   python install_tree_sitter.py")