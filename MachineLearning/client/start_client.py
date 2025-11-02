"""
Quick Start Script for Brev Client

Avvia automaticamente il server backend e apre il frontend nel browser.

Usage:
    python client/start_client.py
    python client/start_client.py --port 5000
    python client/start_client.py --config client/config/.env
"""

import subprocess
import webbrowser
import time
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_dependencies():
    """Verifica che le dipendenze siano installate"""
    required = ['fastapi', 'uvicorn', 'requests', 'pydantic']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"[ERROR] Dipendenze mancanti: {', '.join(missing)}")
        print(f"\nInstalla con:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


def load_env_file(env_path):
    """Carica variabili d'ambiente da file .env"""
    if not os.path.exists(env_path):
        print(f"[WARNING] File .env non trovato: {env_path}")
        print(f"[INFO] Usando configurazione predefinita")
        return

    print(f"[INFO] Caricamento configurazione da {env_path}")

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def start_backend(port=5000):
    """Avvia il server backend"""
    print(f"\n[BACKEND] Avvio server FastAPI sulla porta {port}...")

    # Avvia uvicorn dalla root del progetto
    # Usa il path completo del modulo
    process = subprocess.Popen(
        [
            sys.executable, '-m', 'uvicorn',
            'client.backend.server:app',
            '--host', '0.0.0.0',
            '--port', str(port),
            '--reload'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    print("[BACKEND] Attesa avvio server...")
    time.sleep(3)

    # Check if server is running
    if process.poll() is None:
        print(f"[BACKEND] Server avviato con successo!")
        print(f"[BACKEND] API disponibili su: http://localhost:{port}")
        print(f"[BACKEND] Documentazione: http://localhost:{port}/docs")
        return process
    else:
        stderr = process.stderr.read()
        print(f"[ERROR] Errore avvio server:")
        print(stderr)
        return None


def start_frontend(backend_port=5000):
    """Avvia il frontend"""
    print(f"\n[FRONTEND] Apertura interfaccia web...")

    frontend_dir = Path(__file__).parent / 'frontend'
    index_file = frontend_dir / 'index.html'

    if not index_file.exists():
        print(f"[ERROR] File index.html non trovato: {index_file}")
        return None

    # Open in default browser
    webbrowser.open(f'file://{index_file.absolute()}')

    print(f"[FRONTEND] Interfaccia aperta nel browser")
    print(f"[FRONTEND] Se non si apre automaticamente, vai su:")
    print(f"[FRONTEND] file://{index_file.absolute()}")

    return True


def print_info():
    """Stampa informazioni di utilizzo"""
    print("\n" + "=" * 70)
    print("BREV CLIENT - QUICK START")
    print("=" * 70)
    print("\n📚 Come usare:")
    print("   1. Il server backend è attivo")
    print("   2. L'interfaccia web è aperta nel browser")
    print("   3. Vai su Settings (⚙️) per configurare URL e API key")
    print("   4. Inizia a generare codice!")

    print("\n⚙️  Configurazione predefinita:")
    print(f"   - Backend URL: http://localhost:5000")
    print(f"   - API Key: {os.getenv('SERVER_API_KEY', 'dev-key-12345')}")

    print("\n🛑 Per fermare:")
    print("   Premi Ctrl+C in questo terminale")

    print("\n📖 Documentazione completa:")
    print("   Vedi client/README.md")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Quick start Brev Client")
    parser.add_argument('--port', type=int, default=5000,
                       help="Porta per il server backend (default: 5000)")
    parser.add_argument('--config', type=str, default='client/config/.env',
                       help="Percorso file .env (default: client/config/.env)")
    parser.add_argument('--no-browser', action='store_true',
                       help="Non aprire il browser automaticamente")

    args = parser.parse_args()

    print("\n🚀 Brev Client - Quick Start\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Load environment
    load_env_file(args.config)

    # Start backend
    backend_process = start_backend(args.port)

    if backend_process is None:
        print("\n[ERROR] Impossibile avviare il backend")
        sys.exit(1)

    # Start frontend
    if not args.no_browser:
        start_frontend(args.port)

    # Print info
    print_info()

    try:
        # Keep running
        print("\n[INFO] Server in esecuzione. Premi Ctrl+C per fermare.\n")
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n\n[INFO] Arresto server...")
        backend_process.terminate()
        backend_process.wait()
        print("[INFO] Server arrestato. Arrivederci!")


if __name__ == "__main__":
    main()
