"""
Dependency Checker for Machine Learning Project

Checks that all necessary dependencies are installed and functional:
- PyTorch and CUDA
- Transformers
- Tree-sitter and languages
- Storage providers (DigitalOcean Spaces)
- Dataset libraries

Usage:
    python check_dependencies.py
    python main.py --check-deps
"""

import sys
import importlib
from typing import Dict, List, Tuple


def check_dependencies() -> Dict[str, bool]:
    """
    Checks all project dependencies.

    Returns:
        Dict with dependency name -> status (True = OK, False = Missing)
    """
    results = {}

    print("\n" + "="*70)
    print("[*] DEPENDENCY CHECK")
    print("="*70 + "\n")

    # Core Dependencies
    print("[*] Core Dependencies:")
    core_deps = [
        ("torch", "PyTorch"),
        ("transformers", "HuggingFace Transformers"),
        ("datasets", "HuggingFace Datasets"),
        ("numpy", "NumPy"),
        ("tqdm", "Progress Bars"),
    ]

    for module_name, display_name in core_deps:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {display_name}")
            results[module_name] = True
        except ImportError:
            print(f"  [FAIL] {display_name} - NOT INSTALLED")
            results[module_name] = False

    print()

    # Tree-sitter Languages
    print("[*] Tree-sitter Language Parsers:")
    tree_sitter_langs = [
        ("tree_sitter", "Tree-sitter Core"),
        ("tree_sitter_python", "Python"),
        ("tree_sitter_javascript", "JavaScript"),
        ("tree_sitter_java", "Java"),
        ("tree_sitter_cpp", "C++"),
        ("tree_sitter_go", "Go"),
        ("tree_sitter_ruby", "Ruby"),
        ("tree_sitter_rust", "Rust"),
    ]

    for module_name, display_name in tree_sitter_langs:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {display_name}")
            results[module_name] = True
        except ImportError:
            print(f"  [FAIL] {display_name} - NOT INSTALLED")
            results[module_name] = False

    print()

    # Storage Dependencies
    print("[*] Storage Providers:")
    storage_deps = [
        ("boto3", "AWS S3 / DigitalOcean Spaces"),
        ("google.cloud.storage", "Google Cloud Storage"),
    ]

    for module_name, display_name in storage_deps:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {display_name}")
            results[module_name] = True
        except ImportError:
            print(f"  [WARN] {display_name} - NOT INSTALLED (optional)")
            results[module_name] = False

    print()

    # Check PyTorch CUDA
    print("[*] GPU Support:")
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_version = torch.version.cuda
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            print(f"  [OK] CUDA Available: {cuda_version}")
            print(f"  [OK] GPU Count: {gpu_count}")
            print(f"  [OK] GPU: {gpu_name}")
            results['cuda'] = True
        else:
            print(f"  [WARN] CUDA Not Available (CPU only)")
            results['cuda'] = False
    except Exception as e:
        print(f"  [FAIL] Error checking CUDA: {e}")
        results['cuda'] = False

    print()

    # Check Transformers Cache
    print("[*] Transformers Cache:")
    try:
        from transformers import AutoTokenizer
        import os
        cache_dir = os.getenv('HF_HOME', os.path.join(os.path.expanduser("~"), ".cache", "huggingface"))
        print(f"  [INFO] Cache Directory: {cache_dir}")

        # Try to load a small tokenizer to verify cache is working
        try:
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
            print(f"  [OK] Cache Working (tested with gpt2)")
            results['transformers_cache'] = True
        except Exception as e:
            print(f"  [WARN] Cache test failed: {e}")
            results['transformers_cache'] = False
    except Exception as e:
        print(f"  [FAIL] Error checking cache: {e}")
        results['transformers_cache'] = False

    print()

    # Summary
    print("="*70)
    print("[*] SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\n  Total: {total}")
    print(f"  [OK] Passed: {passed}")
    print(f"  [FAIL] Failed: {failed}")

    if failed == 0:
        print(f"\n  [SUCCESS] All dependencies are installed!")
    else:
        print(f"\n  [WARN] Some dependencies are missing. Install with:")
        print(f"         pip install -r requirements.txt")

    print("\n" + "="*70 + "\n")

    return results


def get_missing_dependencies() -> List[str]:
    """
    Gets list of missing dependencies.

    Returns:
        List of missing module names
    """
    results = check_dependencies()
    return [name for name, status in results.items() if not status]


def install_missing_dependencies(missing: List[str]) -> bool:
    """
    Installs missing dependencies (experimental).

    Args:
        missing: List of modules to install

    Returns:
        True if installation successful
    """
    if not missing:
        print("[OK] No missing dependencies")
        return True

    print(f"\n[*] Installing {len(missing)} missing dependencies...")
    print(f"    {', '.join(missing)}")
    print()

    try:
        import subprocess

        # Map internal names to pip package names
        package_map = {
            'tree_sitter': 'tree-sitter',
            'tree_sitter_python': 'tree-sitter-python',
            'tree_sitter_javascript': 'tree-sitter-javascript',
            'tree_sitter_java': 'tree-sitter-java',
            'tree_sitter_cpp': 'tree-sitter-cpp',
            'tree_sitter_go': 'tree-sitter-go',
            'tree_sitter_ruby': 'tree-sitter-ruby',
            'tree_sitter_rust': 'tree-sitter-rust',
            'google.cloud.storage': 'google-cloud-storage',
        }

        packages = [package_map.get(name, name) for name in missing]

        # Install
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] Installation successful!")
            return True
        else:
            print(f"[FAIL] Installation failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"[FAIL] Error during installation: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check project dependencies')
    parser.add_argument(
        '--install',
        action='store_true',
        help='Automatically install missing dependencies'
    )
    parser.add_argument(
        '--missing-only',
        action='store_true',
        help='Only show missing dependencies'
    )
    
    args = parser.parse_args()
    
    if args.missing_only:
        missing = get_missing_dependencies()
        if missing:
            print("Missing dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            sys.exit(1)
        else:
            print("[OK] All dependencies installed")
            sys.exit(0)

    results = check_dependencies()

    if args.install:
        missing = [name for name, status in results.items() if not status]
        if missing:
            install_missing_dependencies(missing)
        else:
            print("[OK] All dependencies already installed")
    
    # Exit with error code if any dependency is missing
    missing_count = sum(1 for v in results.values() if not v)
    sys.exit(0 if missing_count == 0 else 1)


if __name__ == "__main__":
    main()
