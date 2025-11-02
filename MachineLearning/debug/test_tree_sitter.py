#!/usr/bin/env python
"""Quick test for tree-sitter setup."""

try:
    import tree_sitter
    # Check version if available (not all versions have __version__)
    if hasattr(tree_sitter, '__version__'):
        print(f"OK: tree-sitter version {tree_sitter.__version__}")
    else:
        print("OK: tree-sitter imported successfully")

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

    try:
        import tree_sitter_cpp
        languages.append("C++")
    except ImportError:
        pass

    try:
        import tree_sitter_go
        languages.append("Go")
    except ImportError:
        pass

    try:
        import tree_sitter_ruby
        languages.append("Ruby")
    except ImportError:
        pass

    try:
        import tree_sitter_rust
        languages.append("Rust")
    except ImportError:
        pass

    if languages:
        print(f"OK: Available languages: {', '.join(languages)}")

        # Test parsing with new API
        import tree_sitter_python as tsp
        from tree_sitter import Parser, Language

        # New API: Wrap the PyCapsule with Language, then use with Parser
        lang = Language(tsp.language())
        parser = Parser(lang)
        tree = parser.parse(b"def hello(): pass")
        print(f"OK: Successfully parsed Python code!")

        # Test our UniversalParser
        print("\nTesting UniversalParser...")
        from module.preprocessing.universal_parser import UniversalParser

        up = UniversalParser()
        if up.languages:
            print(f"OK: UniversalParser loaded {len(up.languages)} languages")

            # Test parsing
            code = "def test_function(x, y):\n    return x + y"
            results = up.parse(code, "python")
            if results:
                print(f"OK: UniversalParser extracted {len(results)} units")
            else:
                print("WARNING: UniversalParser didn't extract any units")
        else:
            print("WARNING: UniversalParser couldn't load any languages")

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
    import traceback
    traceback.print_exc()