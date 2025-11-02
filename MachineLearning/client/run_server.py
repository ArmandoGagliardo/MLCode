"""
Simple Server Runner

Script semplice per avviare il server backend senza complicazioni.

Usage:
    python client/run_server.py
    python client/run_server.py --port 8000
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_env_file():
    """Carica file .env se esiste"""
    env_file = Path(__file__).parent / 'config' / '.env'

    if env_file.exists():
        print(f"[INFO] Caricamento configurazione da {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"[WARNING] File .env non trovato: {env_file}")
        print("[INFO] Usando configurazione predefinita")


def main():
    parser = argparse.ArgumentParser(description="Avvia il server backend")
    parser.add_argument('--port', type=int, default=5000,
                       help="Porta del server (default: 5000)")
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help="Host del server (default: 0.0.0.0)")
    parser.add_argument('--reload', action='store_true',
                       help="Abilita auto-reload")

    args = parser.parse_args()

    # Load environment
    load_env_file()

    # Import uvicorn
    try:
        import uvicorn
    except ImportError:
        print("[ERROR] uvicorn non installato!")
        print("[FIX] Esegui: pip install uvicorn")
        sys.exit(1)

    # Print info
    print("\n" + "=" * 70)
    print("BREV CLIENT - SERVER BACKEND")
    print("=" * 70)
    print(f"\n🚀 Avvio server su http://{args.host}:{args.port}")
    print(f"📚 Documentazione API: http://localhost:{args.port}/docs")
    print(f"🔑 API Key: {os.getenv('SERVER_API_KEY', 'dev-key-12345')[:20]}...")
    print(f"\n🛑 Premi Ctrl+C per fermare")
    print("=" * 70 + "\n")

    # Start server
    uvicorn.run(
        "client.backend.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
