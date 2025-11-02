"""
Dependency Checker

Verifica che tutti i pacchetti Python richiesti siano installati.
Controlla le versioni e fornisce istruzioni per l'installazione.
"""

import sys
import subprocess
from typing import Dict, List, Tuple
import importlib.metadata
from packaging import version


# Dipendenze critiche richieste per il funzionamento base
CRITICAL_DEPENDENCIES = {
    'torch': '2.0.0',
    'transformers': '4.30.0',
    'datasets': '2.0.0',
    'numpy': '1.20.0',
    'pandas': '1.3.0',
    'requests': '2.25.0',
    'python-dotenv': '0.19.0',
}

# Dipendenze opzionali per funzionalità specifiche
OPTIONAL_DEPENDENCIES = {
    # Storage providers
    'boto3': {
        'min_version': '1.20.0',
        'feature': 'Cloud Storage (Backblaze, Wasabi, S3, DigitalOcean, Cloudflare R2)',
        'install': 'pip install boto3'
    },

    # UI
    'streamlit': {
        'min_version': '1.20.0',
        'feature': 'Web UI Interface',
        'install': 'pip install streamlit'
    },

    # Web crawling
    'beautifulsoup4': {
        'min_version': '4.9.0',
        'feature': 'Web Crawling',
        'install': 'pip install beautifulsoup4'
    },
    'selenium': {
        'min_version': '4.0.0',
        'feature': 'Dynamic Web Crawling',
        'install': 'pip install selenium'
    },

    # Security scanning
    'PyYAML': {
        'min_version': '5.4.0',
        'feature': 'YAML parsing (security scanning)',
        'install': 'pip install PyYAML'
    },

    # Machine Learning extras
    'scikit-learn': {
        'min_version': '0.24.0',
        'feature': 'Additional ML algorithms',
        'install': 'pip install scikit-learn'
    },
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
    try:
        pkg_version = importlib.metadata.version(package_name)
        return True, pkg_version
    except importlib.metadata.PackageNotFoundError:
        return False, None


def compare_versions(installed: str, required: str) -> bool:
    """Confronta le versioni dei pacchetti"""
    try:
        return version.parse(installed) >= version.parse(required)
    except Exception:
        return True  # Se non riusciamo a confrontare, assumiamo sia OK


def check_critical_dependencies() -> Tuple[bool, List[Dict]]:
    """Controlla le dipendenze critiche"""
    results = []
    all_ok = True

    for package, min_version in CRITICAL_DEPENDENCIES.items():
        installed, pkg_version = is_package_installed(package)

        if not installed:
            all_ok = False
            results.append({
                'package': package,
                'status': 'MISSING',
                'installed': None,
                'required': min_version,
                'critical': True
            })
        else:
            version_ok = compare_versions(pkg_version, min_version)
            if not version_ok:
                all_ok = False

            results.append({
                'package': package,
                'status': 'OK' if version_ok else 'OLD_VERSION',
                'installed': pkg_version,
                'required': min_version,
                'critical': True
            })

    return all_ok, results


def check_optional_dependencies() -> List[Dict]:
    """Controlla le dipendenze opzionali"""
    results = []

    for package, info in OPTIONAL_DEPENDENCIES.items():
        installed, pkg_version = is_package_installed(package)

        if not installed:
            results.append({
                'package': package,
                'status': 'MISSING',
                'installed': None,
                'required': info['min_version'],
                'feature': info['feature'],
                'install': info['install'],
                'critical': False
            })
        else:
            version_ok = compare_versions(pkg_version, info['min_version'])

            results.append({
                'package': package,
                'status': 'OK' if version_ok else 'OLD_VERSION',
                'installed': pkg_version,
                'required': info['min_version'],
                'feature': info['feature'],
                'install': info['install'],
                'critical': False
            })

    return results


def print_dependency_report(python_ok: bool, python_msg: str,
                           critical_results: List[Dict],
                           optional_results: List[Dict],
                           verbose: bool = False):
    """Stampa il report delle dipendenze"""

    print("\n" + "=" * 80)
    print("CONTROLLO DIPENDENZE")
    print("=" * 80)

    # Python version
    print(f"\nVersione Python: {python_msg}")
    if not python_ok:
        print("[X] ERRORE: Versione Python non supportata!")
        print("   Aggiorna Python a versione >= 3.8")

    # Critical dependencies
    print("\n[CRITICHE] DIPENDENZE CRITICHE:")
    print("-" * 80)

    critical_missing = []
    critical_old = []

    for result in critical_results:
        status_symbol = {
            'OK': '[OK]',
            'MISSING': '[X]',
            'OLD_VERSION': '[!]'
        }.get(result['status'], '[?]')

        if result['status'] == 'OK':
            if verbose:
                print(f"{status_symbol} {result['package']:20s} v{result['installed']:15s} (>= {result['required']})")
        else:
            installed_str = result['installed'] or 'Non installato'
            print(f"{status_symbol} {result['package']:20s} {installed_str:15s} (richiesto: >= {result['required']})")

            if result['status'] == 'MISSING':
                critical_missing.append(result['package'])
            elif result['status'] == 'OLD_VERSION':
                critical_old.append(result['package'])

    # Optional dependencies
    print("\n[OPZIONALI] DIPENDENZE OPZIONALI:")
    print("-" * 80)

    optional_missing = []
    optional_old = []

    for result in optional_results:
        status_symbol = {
            'OK': '[OK]',
            'MISSING': '[!]',
            'OLD_VERSION': '[!]'
        }.get(result['status'], '[?]')

        if result['status'] == 'OK':
            if verbose:
                print(f"{status_symbol} {result['package']:20s} v{result['installed']:15s} - {result['feature']}")
        else:
            installed_str = result['installed'] or 'Non installato'
            print(f"{status_symbol} {result['package']:20s} {installed_str:15s}")
            print(f"   Feature: {result['feature']}")
            print(f"   Install: {result['install']}")

            if result['status'] == 'MISSING':
                optional_missing.append(result)
            elif result['status'] == 'OLD_VERSION':
                optional_old.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("RIEPILOGO")
    print("=" * 80)

    if critical_missing or critical_old:
        print("\n[X] AZIONE RICHIESTA - Dipendenze critiche mancanti o obsolete!")

        if critical_missing:
            print(f"\n[INSTALLA] Installa i pacchetti mancanti:")
            packages = ' '.join(critical_missing)
            print(f"   pip install {packages}")

        if critical_old:
            print(f"\n[AGGIORNA] Aggiorna i pacchetti obsoleti:")
            packages = ' '.join(critical_old)
            print(f"   pip install --upgrade {packages}")

        print("\nOppure installa tutte le dipendenze:")
        print("   pip install -r requirements.txt")

        return False

    else:
        print("\n[OK] Tutte le dipendenze critiche sono installate e aggiornate!")

    if optional_missing:
        print(f"\n[INFO] {len(optional_missing)} dipendenze opzionali mancanti")
        print("   Alcune funzionalita' potrebbero non essere disponibili:")
        for result in optional_missing[:3]:  # Mostra solo le prime 3
            print(f"   - {result['package']:20s} ({result['feature']})")
        if len(optional_missing) > 3:
            print(f"   ... e altre {len(optional_missing) - 3}")

        print("\n   Usa --verbose per vedere i comandi di installazione")

    if optional_old:
        print(f"\n[INFO] {len(optional_old)} dipendenze opzionali obsolete")
        print("   Considera l'aggiornamento per funzionalita' migliorate")

    print("\n" + "=" * 80)
    return True


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


def auto_install_missing(critical_results: List[Dict]) -> bool:
    """Installa automaticamente i pacchetti critici mancanti"""
    missing = [r for r in critical_results if r['status'] == 'MISSING']

    if not missing:
        return True

    print(f"\n[SETUP] Trovati {len(missing)} pacchetti critici mancanti")
    response = input("Vuoi installarli automaticamente? (s/n): ").lower().strip()

    if response not in ['s', 'si', 'y', 'yes']:
        print("[X] Installazione annullata. Installa manualmente i pacchetti richiesti.")
        return False

    all_success = True
    for result in missing:
        if not install_package(result['package']):
            all_success = False

    return all_success


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

    # Check critical dependencies
    critical_ok, critical_results = check_critical_dependencies()

    # Check optional dependencies
    optional_results = check_optional_dependencies()

    # Print report
    print_dependency_report(python_ok, python_msg, critical_results,
                          optional_results, verbose)

    # Auto-install if requested
    if auto_install and not critical_ok:
        if auto_install_missing(critical_results):
            print("\n[OK] Tutti i pacchetti critici sono ora installati!")
            print("   Riavvia il programma per utilizzare le nuove dipendenze.")
        return False  # Richiede riavvio

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
