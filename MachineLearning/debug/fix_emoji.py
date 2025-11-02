#!/usr/bin/env python3
"""
Script to remove emoji from logger messages for Windows compatibility.
Windows PowerShell with CP1252 encoding cannot display Unicode emoji.
"""

import os
import re
from pathlib import Path

# Mapping of emoji to ASCII alternatives
EMOJI_REPLACEMENTS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '📦': '[INFO]',
    '🎉': '[SUCCESS]',
    '🚀': '[START]',
    '📋': '[INFO]',
    '🔒': '[SECURE]',
    '🧹': '[CLEANUP]',
    '📊': '[STATS]',
    '👥': '[USER]',
    '⚡': '[FAST]',
    '🛑': '[STOP]',
    '🔄': '[REFRESH]',
    '⏸️': '[PAUSE]',
    '💾': '[SAVE]',
    '📁': '[FOLDER]',
    '📄': '[FILE]',
    '🔍': '[SEARCH]',
    '⏱️': '[TIME]',
    '🌐': '[WEB]',
}

def remove_emoji_from_file(file_path: Path) -> tuple[int, int]:
    """
    Remove emoji from a Python file's logger statements.
    
    Returns:
        Tuple of (lines_modified, total_replacements)
    """
    if not file_path.exists():
        return 0, 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    lines_modified = 0
    total_replacements = 0
    
    # Replace each emoji
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        if emoji in content:
            # Count occurrences in logger statements
            pattern = rf'logger\.(info|warning|error|debug)\([^)]*{re.escape(emoji)}[^)]*\)'
            matches = re.findall(pattern, content)
            count = len(matches)
            
            if count > 0:
                content = content.replace(emoji, replacement)
                lines_modified += count
                total_replacements += count
                print(f"  - Replaced '{emoji}' with '{replacement}' ({count} times)")
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return lines_modified, total_replacements
    
    return 0, 0

def process_directory(directory: Path):
    """Process all Python files in a directory recursively."""
    print(f"Processing directory: {directory}")
    print("=" * 70)
    
    total_files = 0
    total_modified = 0
    total_replacements = 0
    
    # Find all Python files
    python_files = list(directory.rglob('*.py'))
    
    for py_file in python_files:
        # Skip virtual environments and caches
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'venv', 'env']):
            continue
        
        total_files += 1
        lines, replacements = remove_emoji_from_file(py_file)
        
        if lines > 0:
            total_modified += 1
            total_replacements += replacements
            print(f"\n✓ {py_file.relative_to(directory)}")
    
    print("\n" + "=" * 70)
    print(f"Summary:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Files modified: {total_modified}")
    print(f"  Total replacements: {total_replacements}")
    print("=" * 70)

if __name__ == "__main__":
    # Get current directory
    current_dir = Path(__file__).parent
    
    print("=" * 70)
    print("Emoji to ASCII Converter for Windows Compatibility")
    print("=" * 70)
    print()
    
    process_directory(current_dir)
    
    print("\n✅ Done! All emoji have been replaced with ASCII alternatives.")
    print("   Your code is now Windows PowerShell compatible!")
