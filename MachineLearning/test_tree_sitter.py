#!/usr/bin/env python
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
