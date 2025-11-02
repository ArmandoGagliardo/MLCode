"""
Test Cloud Storage Upload

Script per verificare che il salvataggio su cloud storage funzioni correttamente.
Utile per diagnosticare problemi su istanze GPU remote.

Uso:
    python test_cloud_upload.py
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module.storage.storage_manager import StorageManager


def print_env_status():
    """Stampa stato variabili ambiente"""
    print("=" * 70)
    print("🔍 VERIFICA VARIABILI AMBIENTE")
    print("=" * 70)
    print()
    
    # Storage provider
    provider = os.getenv('STORAGE_PROVIDER', 'NOT SET')
    print(f"STORAGE_PROVIDER: {provider}")
    
    # DigitalOcean
    if provider == 'digitalocean':
        print("\nDigitalOcean Spaces:")
        print(f"  DO_SPACES_KEY: {'✓ SET' if os.getenv('DO_SPACES_KEY') else '✗ NOT SET'}")
        print(f"  DO_SPACES_SECRET: {'✓ SET' if os.getenv('DO_SPACES_SECRET') else '✗ NOT SET'}")
        print(f"  DO_SPACES_NAME: {os.getenv('DO_SPACES_NAME', '✗ NOT SET')}")
        print(f"  DO_SPACES_REGION: {os.getenv('DO_SPACES_REGION', '✗ NOT SET')}")
    
    # Backblaze
    elif provider == 'backblaze':
        print("\nBackblaze B2:")
        print(f"  BACKBLAZE_KEY_ID: {'✓ SET' if os.getenv('BACKBLAZE_KEY_ID') else '✗ NOT SET'}")
        print(f"  BACKBLAZE_APPLICATION_KEY: {'✓ SET' if os.getenv('BACKBLAZE_APPLICATION_KEY') else '✗ NOT SET'}")
        print(f"  BACKBLAZE_BUCKET_NAME: {os.getenv('BACKBLAZE_BUCKET_NAME', '✗ NOT SET')}")
    
    print()


def test_connection():
    """Test connessione al storage"""
    print("=" * 70)
    print("🔌 TEST CONNESSIONE")
    print("=" * 70)
    print()
    
    try:
        storage = StorageManager()
        print(f"Storage provider: {storage.config.get('provider_type')}")
        print()
        
        print("Connessione in corso...")
        if storage.connect():
            print("✅ Connessione riuscita!")
            return storage
        else:
            print("❌ Connessione fallita!")
            return None
    
    except Exception as e:
        print(f"❌ Errore durante connessione: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_upload(storage):
    """Test upload di un file"""
    print()
    print("=" * 70)
    print("📤 TEST UPLOAD")
    print("=" * 70)
    print()
    
    # Crea file di test
    test_data = {
        "test": "cloud_storage_test",
        "timestamp": datetime.now().isoformat(),
        "message": "This is a test file to verify cloud storage upload",
        "functions": [
            {
                "func_name": "test_function",
                "language": "python",
                "input": "Write a python function named test_function",
                "output": "def test_function():\n    return 'test'"
            }
        ]
    }
    
    test_file = "test_cloud_upload.json"
    
    try:
        # Salva locale
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ File di test creato: {test_file}")
        print(f"   Dimensione: {os.path.getsize(test_file)} bytes")
        print()
        
        # Upload
        remote_path = f"test/{test_file}"
        print(f"Upload a: {remote_path}")
        
        if storage.upload_file(test_file, remote_path):
            print("✅ Upload riuscito!")
            
            # Verifica upload
            print()
            print("Verifica file su cloud...")
            files = storage.list_files("test/")
            
            if any(test_file in f for f in files):
                print("✅ File verificato su cloud!")
                print(f"   File trovato: {remote_path}")
                
                # Cleanup
                print()
                print("Pulizia...")
                storage.delete_file(remote_path)
                print("✅ File di test rimosso")
                
                return True
            else:
                print("⚠️  File non trovato nella lista cloud")
                print(f"   File presenti in test/: {files}")
                return False
        else:
            print("❌ Upload fallito!")
            return False
    
    except Exception as e:
        print(f"❌ Errore durante upload: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Rimuovi file locale di test
        if os.path.exists(test_file):
            os.remove(test_file)


def test_save_dataset(storage):
    """Test salvataggio dataset (come fa github_repo_processor)"""
    print()
    print("=" * 70)
    print("💾 TEST SALVATAGGIO DATASET")
    print("=" * 70)
    print()
    
    # Simula dataset estratto
    dataset = [
        {
            "task_type": "code_generation",
            "language": "python",
            "func_name": "calculate_sum",
            "input": "Write a python function named calculate_sum",
            "output": "def calculate_sum(a, b):\n    return a + b"
        },
        {
            "task_type": "code_generation",
            "language": "javascript",
            "func_name": "getData",
            "input": "Write a javascript function named getData",
            "output": "function getData() {\n  return data;\n}"
        }
    ]
    
    # Salva locale
    local_dir = Path("datasets/local_backup/code_generation")
    local_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_repo_{timestamp}_{len(dataset)}.json"
    local_file = local_dir / filename
    
    try:
        # Salva locale
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Dataset salvato locale: {local_file}")
        print(f"   Funzioni: {len(dataset)}")
        print()
        
        # Upload al cloud
        remote_path = f"datasets/code_generation/{filename}"
        print(f"Upload a cloud: {remote_path}")
        
        if storage.upload_file(str(local_file), remote_path):
            print("✅ Dataset uploadato al cloud!")
            
            # Verifica
            print()
            print("Verifica su cloud...")
            files = storage.list_files("datasets/code_generation/")
            
            if any(filename in f for f in files):
                print("✅ Dataset verificato su cloud!")
                
                # Cleanup cloud
                print()
                print("Pulizia cloud...")
                storage.delete_file(remote_path)
                print("✅ Dataset test rimosso dal cloud")
                
                return True
            else:
                print("⚠️  Dataset non trovato su cloud")
                return False
        else:
            print("❌ Upload dataset fallito!")
            return False
    
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup locale
        if local_file.exists():
            local_file.unlink()
            print(f"✅ File locale rimosso: {local_file}")


def main():
    print()
    print("=" * 70)
    print("☁️  TEST CLOUD STORAGE UPLOAD")
    print("=" * 70)
    print()
    
    # 1. Verifica environment
    print_env_status()
    
    # 2. Test connessione
    storage = test_connection()
    
    if not storage:
        print()
        print("=" * 70)
        print("❌ CONNESSIONE FALLITA - FIX NECESSARI:")
        print("=" * 70)
        print()
        print("1. Verifica file .env esista:")
        print("   ls .env")
        print()
        print("2. Verifica contenuto .env:")
        print("   cat .env")
        print()
        print("3. Verifica variabili caricate:")
        print("   python -c \"from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('STORAGE_PROVIDER'))\"")
        print()
        print("4. Crea .env se mancante:")
        print("   cp .env.example .env")
        print("   nano .env  # Compila con le tue credenziali")
        print()
        return
    
    # 3. Test upload semplice
    success1 = test_upload(storage)
    
    # 4. Test salvataggio dataset
    success2 = test_save_dataset(storage)
    
    # Summary
    print()
    print("=" * 70)
    print("📊 RISULTATI")
    print("=" * 70)
    print()
    print(f"Connessione: {'✅ OK' if storage else '❌ FAILED'}")
    print(f"Upload Test: {'✅ OK' if success1 else '❌ FAILED'}")
    print(f"Dataset Save: {'✅ OK' if success2 else '❌ FAILED'}")
    print()
    
    if storage and success1 and success2:
        print("=" * 70)
        print("🎉 TUTTI I TEST SUPERATI!")
        print("=" * 70)
        print()
        print("Il cloud storage funziona correttamente.")
        print("Puoi procedere con:")
        print("  - python example_single_repo.py")
        print("  - python example_bulk_processing.py")
        print()
        print("I dati verranno automaticamente uploadati al cloud.")
    else:
        print("=" * 70)
        print("⚠️  ALCUNI TEST FALLITI")
        print("=" * 70)
        print()
        print("Verifica:")
        print("  1. Credenziali in .env corrette")
        print("  2. Connessione internet funzionante")
        print("  3. Bucket/Space esistente e accessibile")
        print()
        print("Per debug dettagliato:")
        print("  python debug/test_storage_quick.py")


if __name__ == "__main__":
    main()
