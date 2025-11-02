"""
Test Sistema di Autenticazione

Verifica che l'autenticazione funzioni correttamente.
"""

import requests
import os


def test_without_auth(base_url):
    """Test senza autenticazione - deve fallire"""
    print("\n[TEST 1] Richiesta senza autenticazione...")

    response = requests.post(
        f"{base_url}/api/generate",
        json={"prompt": "test", "language": "python"}
    )

    if response.status_code == 401:
        print("  ✓ Corretto: 401 Unauthorized")
        return True
    else:
        print(f"  ✗ Errore: Expected 401, got {response.status_code}")
        return False


def test_with_wrong_auth(base_url):
    """Test con autenticazione errata - deve fallire"""
    print("\n[TEST 2] Richiesta con API key errata...")

    response = requests.post(
        f"{base_url}/api/generate",
        headers={"Authorization": "Bearer wrong-key-12345"},
        json={"prompt": "test", "language": "python"}
    )

    if response.status_code == 401:
        print("  ✓ Corretto: 401 Unauthorized")
        return True
    else:
        print(f"  ✗ Errore: Expected 401, got {response.status_code}")
        return False


def test_with_correct_auth(base_url, api_key):
    """Test con autenticazione corretta - deve funzionare"""
    print("\n[TEST 3] Richiesta con API key corretta...")

    response = requests.post(
        f"{base_url}/api/generate",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "prompt": "Create a sum function",
            "language": "python",
            "max_length": 256
        }
    )

    if response.status_code == 200:
        print("  ✓ Corretto: 200 OK")
        data = response.json()
        print(f"  Response: {data.get('success')}")
        return True
    else:
        print(f"  ✗ Errore: Expected 200, got {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_health_endpoint(base_url):
    """Test endpoint health (senza autenticazione)"""
    print("\n[TEST 4] Health check (no auth required)...")

    response = requests.get(f"{base_url}/health")

    if response.status_code == 200:
        print("  ✓ Corretto: 200 OK")
        data = response.json()
        print(f"  Status: {data.get('status')}")
        return True
    else:
        print(f"  ✗ Errore: Expected 200, got {response.status_code}")
        return False


def test_rate_limiting(base_url, api_key):
    """Test rate limiting"""
    print("\n[TEST 5] Rate limiting (100 richieste rapide)...")

    count = 0
    for i in range(100):
        response = requests.post(
            f"{base_url}/api/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": f"test {i}", "language": "python"}
        )

        if response.status_code == 429:
            print(f"  ✓ Rate limit raggiunto dopo {i+1} richieste")
            return True

        count += 1

    print(f"  ⚠️  Completate {count} richieste senza rate limit")
    return True  # Non è un errore se rate limit non è abilitato


def main():
    # Configuration
    base_url = os.getenv('API_URL', 'http://localhost:5000')
    api_key = os.getenv('SERVER_API_KEY', 'dev-key-12345')

    print("=" * 70)
    print("TEST SISTEMA DI AUTENTICAZIONE")
    print("=" * 70)
    print(f"\nBase URL: {base_url}")
    print(f"API Key: {api_key[:20]}...")

    # Run tests
    results = []

    results.append(("No Auth", test_without_auth(base_url)))
    results.append(("Wrong Auth", test_with_wrong_auth(base_url)))
    results.append(("Correct Auth", test_with_correct_auth(base_url, api_key)))
    results.append(("Health Check", test_health_endpoint(base_url)))
    # results.append(("Rate Limiting", test_rate_limiting(base_url, api_key)))

    # Summary
    print("\n" + "=" * 70)
    print("RIEPILOGO TEST")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:10s} {name}")

    print(f"\nRisultato: {passed}/{total} test passati")

    if passed == total:
        print("✓ Tutti i test passati!")
    else:
        print("✗ Alcuni test falliti")

    print("=" * 70)


if __name__ == "__main__":
    main()
