"""
Genera API Key Sicura per il Server Backend

Esegui questo script per generare una chiave sicura da usare come SERVER_API_KEY
"""

import secrets
import string
import hashlib
from datetime import datetime


def generate_api_key(length=32):
    """Genera una API key casuale e sicura"""
    return secrets.token_urlsafe(length)


def generate_custom_key(prefix="brev"):
    """Genera una chiave con prefisso personalizzato"""
    random_part = secrets.token_urlsafe(24)
    return f"{prefix}_{random_part}"


def generate_multiple_keys(count=5):
    """Genera multiple chiavi per diversi client"""
    keys = {}
    for i in range(1, count + 1):
        key_name = f"client_{i}"
        api_key = generate_api_key()
        keys[key_name] = api_key
    return keys


def hash_key(api_key):
    """Crea hash della chiave per storage sicuro"""
    return hashlib.sha256(api_key.encode()).hexdigest()


if __name__ == "__main__":
    print("=" * 70)
    print("GENERATORE API KEY - Brev Client")
    print("=" * 70)

    # Single key
    print("\n1️⃣  API Key Singola (per SERVER_API_KEY):")
    print("-" * 70)
    single_key = generate_api_key()
    print(f"   {single_key}")
    print(f"\n   Aggiungi al file .env:")
    print(f"   SERVER_API_KEY={single_key}")

    # Custom key with prefix
    print("\n2️⃣  API Key con Prefisso:")
    print("-" * 70)
    custom_key = generate_custom_key("brev")
    print(f"   {custom_key}")

    # Multiple keys for different clients
    print("\n3️⃣  Multiple API Keys (per diversi client):")
    print("-" * 70)
    multiple_keys = generate_multiple_keys(3)
    for name, key in multiple_keys.items():
        print(f"   {name:15s} = {key}")

    # Hash example
    print("\n4️⃣  Hash della Chiave (per database):")
    print("-" * 70)
    print(f"   Original: {single_key}")
    print(f"   Hash:     {hash_key(single_key)}")

    # Save to file
    print("\n5️⃣  Salvare Configurazione:")
    print("-" * 70)

    config_content = f"""# Generato il {datetime.now().isoformat()}

# API Key per il server backend
SERVER_API_KEY={single_key}

# API Key alternative (se necessario)
# CLIENT_1_KEY={multiple_keys.get('client_1', '')}
# CLIENT_2_KEY={multiple_keys.get('client_2', '')}
"""

    output_file = "generated_keys.txt"
    with open(output_file, 'w') as f:
        f.write(config_content)

    print(f"   ✓ Configurazione salvata in: {output_file}")
    print(f"   ⚠️  IMPORTANTE: NON committare questo file su Git!")

    print("\n" + "=" * 70)
    print("✅ Chiavi generate con successo!")
    print("=" * 70)
