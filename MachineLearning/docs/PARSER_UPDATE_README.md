# Tree-sitter Parser Update

## Overview

The universal parser has been updated to use the modern tree-sitter API (version >= 0.20.0) with pip-installable language bindings. This resolves the `AttributeError: type object 'tree_sitter.Language' has no attribute 'build_library'` error.

## What Changed

### Old Approach (Deprecated)
- Used `Language.build_library()` to compile language grammars from source
- Required cloning git repositories and building shared libraries
- Used a single `languages.so` file containing all languages

### New Approach (Current)
- Uses pre-built language bindings from PyPI
- Each language is a separate pip package (e.g., `tree-sitter-python`)
- No compilation needed - just `pip install`
- Automatic fallback to regex parsers if tree-sitter isn't available

## Installation

### Quick Install

```bash
# Windows
install_tree_sitter.bat

# Linux/Mac/Windows (Python)
python install_tree_sitter.py

# Or manually with pip
pip install -r requirements_fixed.txt
```

### Manual Installation

```bash
# Core package
pip install tree-sitter>=0.20.0

# Language packages
pip install tree-sitter-python
pip install tree-sitter-javascript
pip install tree-sitter-java
pip install tree-sitter-cpp
pip install tree-sitter-go
pip install tree-sitter-php
pip install tree-sitter-ruby
pip install tree-sitter-rust
```

## Files Modified

1. **module/preprocessing/universal_parser.py**
   - Updated to use modern tree-sitter API
   - Dynamic import of language modules
   - Added fallback parser support
   - Better error handling and logging

2. **requirements_fixed.txt**
   - Added all tree-sitter language packages
   - Specified compatible versions

## New Files Created

1. **install_tree_sitter.py** - Python installation script
2. **install_tree_sitter.bat** - Windows batch installation script
3. **test_new_parser.py** - Comprehensive test suite for the new parser

## Testing

Run the test script to verify everything works:

```bash
python test_new_parser.py
```

Expected output:
```
✅ Parser initialized successfully!
   Available languages: ['python', 'javascript', 'java', 'cpp', 'go', 'php', 'ruby', 'rust']
✅ Found X Python units
✅ Found Y JavaScript units
✅ Found Z Java units
✨ All tests passed successfully!
```

## Supported Languages

The parser now supports these languages out of the box:

- **Python** - Functions, classes, methods
- **JavaScript** - Functions, classes, arrow functions
- **Java** - Methods, constructors, classes
- **C++** - Functions, classes
- **Go** - Functions, methods
- **PHP** - Functions, classes
- **Ruby** - Methods, classes
- **Rust** - Functions, implementations

## Fallback Support

If tree-sitter packages are not installed, the system automatically falls back to regex-based parsers for:
- Python
- JavaScript
- Java
- C++
- Go
- PHP
- Ruby

## Troubleshooting

### Issue: "No language parsers available!"

**Solution**: Install the language packages:
```bash
python install_tree_sitter.py
```

### Issue: ImportError for specific language

**Solution**: Install that specific language:
```bash
pip install tree-sitter-python  # or whichever language is missing
```

### Issue: Old code still references build_library

**Solution**: The parser has been fully updated. If you have custom code, update it to use the new API:

```python
# Old (broken)
Language.build_library('build/languages.so', repos)

# New (working)
import tree_sitter_python
language = tree_sitter_python.language()
```

## Performance

The new implementation offers:
- **Faster startup** - No compilation needed
- **Smaller footprint** - Only install languages you need
- **Better maintenance** - Languages updated independently
- **Improved reliability** - Pre-built binaries tested by maintainers

## Migration from Old System

If you have existing code using the old parser:

1. Delete old build artifacts:
   ```bash
   rm -rf build/languages.so
   rm -rf build/my-languages.so
   rm -rf vendor/
   ```

2. Install new packages:
   ```bash
   python install_tree_sitter.py
   ```

3. The updated UniversalParser is backward compatible - no code changes needed!

## API Reference

### UniversalParser

```python
from module.preprocessing.universal_parser import UniversalParser

parser = UniversalParser()

# Parse code
results = parser.parse(code, "python")

# Extract all functions (alias for parse)
results = parser.extract_all_functions(code, "javascript")

# Check supported languages
languages = parser.get_supported_languages()

# Check if language is supported
if parser.is_language_supported("rust"):
    results = parser.parse(rust_code, "rust")
```

### FallbackParser

Automatically used when tree-sitter is unavailable:

```python
from module.preprocessing.universal_parser import get_parser

# Automatically selects best parser
parser = get_parser()  # UniversalParser or FallbackParser

results = parser.parse(code, "python")
```

## Development

To add support for a new language:

1. Install the language package:
   ```bash
   pip install tree-sitter-{language}
   ```

2. Add to `universal_parser.py`:
   ```python
   language_modules = {
       # ...existing languages...
       "your_language": ("tree_sitter_your_language", "YourLanguage"),
   }
   ```

3. Add node type mappings:
   ```python
   kind_map = {
       # ...existing mappings...
       "your_language": ["function_definition", "class_definition"],
   }
   ```

## Contributing

When contributing parser improvements:

1. Ensure all tests pass: `python test_new_parser.py`
2. Add tests for new languages in `test_new_parser.py`
3. Update this README with new language support
4. Add new language packages to `requirements_fixed.txt`

## License

The parser uses tree-sitter which is MIT licensed. Individual language parsers have their own licenses (mostly MIT).