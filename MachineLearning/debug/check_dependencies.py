"""
Dependency Checker

Verifica che tutti i pacchetti Python richiesti siano installati.
Controlla le versioni e fornisce istruzioni per l'installazione.

Uso:
    python debug/check_dependencies.py
    python debug/check_dependencies.py --verbose
    python debug/check_dependencies.py --auto-install
    python debug/check_dependencies.py --fix
"""

import sys
import subprocess
import os
from typing import Dict, List, Tuple
from pathlib import Path

import safetensors

try:
    import importlib.metadata as metadata
except ImportError:
    # Fallback per Python < 3.8
    try:
        import importlib_metadata as metadata
    except ImportError:
        metadata = None
        print("❌ ERRORE: importlib.metadata non disponibile")
        print("   pip install importlib-metadata")

try:
    from packaging import version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    print("⚠️  Warning: 'packaging' non installato, controllo versioni disabilitato")
    print("   pip install packaging")

CRITICAL_PACKAGES = {
    "torch": "2.6.0",
    "transformers": "4.51.3",
    "datasets": "3.5.0",
    "numpy": "1.20.0",
    "pandas": "1.3.0",
    "requests": "2.25.0",
    "python-dotenv": "0.19.0",
    "tqdm": None,
    "packaging": "21.0",
}

def check_python_version() -> Tuple[bool, str]:
    """Controlla la versione di Python"""
    min_python = (3, 8)
    current = sys.version_info[:2]

    if current >= min_python:
        return True, f"Python {current[0]}.{current[1]} (OK)"
    else:
        return False, f"Python {current[0]}.{current[1]} (RICHIESTO: >= {min_python[0]}.{min_python[1]})"


def is_package_installed(package_name: str) -> Tuple[bool, str]:
    """Controlla se un pacchetto è installato e restituisce la versione"""
    if metadata is None:
        return False, None

    try:
        pkg_version = metadata.version(package_name)
        return True, pkg_version
    except Exception:
        # Catch all exceptions (PackageNotFoundError, etc.)
        return False, None


def compare_versions(installed: str, required: str) -> bool:
    """Confronta le versioni dei pacchetti"""
    if not HAS_PACKAGING:
        return True  # Salta controllo se packaging non disponibile
    try:
        return version.parse(installed) >= version.parse(required)
    except Exception:
        return True  # Se non riusciamo a confrontare, assumiamo sia OK

def read_packages_requirements() -> List[Tuple[str, str]]:
    """Legge i pacchetti e le versioni da requirements.txt"""
    requirements_path = Path(__file__).parent / 'requirements.txt'
    packages = []

    if not requirements_path.is_file():
        print("❌ ERRORE: requirements.txt non trovato")
        return packages

    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '>=' in line:
                    pkg, ver = line.split('>=', 1)
                    packages.append((pkg.strip(), ver.strip()))
                elif '==' in line:
                    pkg, ver = line.split('==', 1)
                    packages.append((pkg.strip(), ver.strip()))
                else:
                    packages.append((line.strip(), None))

    return packages

def install_all_packages():
    """Installa tutti i pacchetti elencati in requirements.txt"""
    packages = read_packages_requirements()
    for pkg, ver in packages:
        if not is_package_installed(pkg)[0]:
            install_package(pkg)
        else:
            print(f"[OK] {pkg} già installato.")
    
def install_package(package: str) -> bool:
    """Installa un pacchetto automaticamente"""
    print(f"\n[INSTALL] Installazione di {package}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"[OK] {package} installato con successo!")
        return True
    except subprocess.CalledProcessError:
        print(f"[X] Errore durante l'installazione di {package}")
        return False

def install_critical_package(package: str, version: str = None) -> bool:
    """Installa un pacchetto critico automaticamente"""
    pkg_str = f"{package}>={version}" if version else package
    print(f"\n[INSTALL] Installazione di {pkg_str}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg_str])
        print(f"[OK] {pkg_str} installato con successo!")
        return True
    except subprocess.CalledProcessError:
        print(f"[X] Errore durante l'installazione di {pkg_str}")
        return False
    
def check_critical_packages(verbose: bool = False, auto_install: bool = False) -> bool:
    """
    Controlla i pacchetti critici

    Args:
        verbose: Mostra informazioni dettagliate
        auto_install: Installa automaticamente i pacchetti mancanti

    Returns:
        True se tutte le dipendenze critiche sono soddisfatte
    """
    all_ok = True

    for pkg, req_version in CRITICAL_PACKAGES.items():
        installed, inst_version = is_package_installed(pkg)

        if not installed:
            all_ok = False
            print(f"❌ Pacchetto mancante: {pkg}")
            if auto_install:
                install_critical_package(pkg, req_version)
        else:
            if req_version and not compare_versions(inst_version, req_version):
                all_ok = False
                print(f"❌ Versione non compatibile per {pkg}: {inst_version} (RICHIESTO: >= {req_version})")
                if auto_install:
                    install_critical_package(pkg, req_version)
            else:
                if verbose:
                    print(f"✅ {pkg} versione {inst_version} (OK)")

    return all_ok

def check_dependencies(verbose: bool = False, auto_install: bool = False) -> bool:
    """
    Funzione principale per controllare le dipendenze

    Args:
        verbose: Mostra informazioni dettagliate
        auto_install: Installa automaticamente i pacchetti mancanti

    Returns:
        True se tutte le dipendenze critiche sono soddisfatte
    """
    # Check Python version
    python_ok, python_msg = check_python_version()

    # Check critical packages
    critical_ok = check_critical_packages(verbose=verbose, auto_install=auto_install)

    # install all packages
    install_all_packages()

    return python_ok and critical_ok


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Controlla le dipendenze Python")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Mostra informazioni dettagliate")
    parser.add_argument("--auto-install", "-a", action="store_true",
                       help="Installa automaticamente i pacchetti mancanti")

    args = parser.parse_args()

    success = check_dependencies(verbose=args.verbose, auto_install=args.auto_install)

    sys.exit(0 if success else 1)
