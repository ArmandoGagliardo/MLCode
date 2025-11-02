"""
Sistema di Autenticazione Avanzato

Supporta multiple API keys, rate limiting, e gestione permessi.
"""

import os
import hashlib
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Security
security = HTTPBearer()


class APIKeyManager:
    """Gestisce multiple API keys con permessi"""

    def __init__(self):
        # Carica chiavi da ambiente o file
        self.keys = self._load_keys()

        # Rate limiting: {api_key: [(timestamp, count)]}
        self.rate_limits = defaultdict(list)

        # Statistics
        self.stats = defaultdict(lambda: {
            'requests': 0,
            'last_used': None,
            'created': datetime.now()
        })

    def _load_keys(self) -> Dict[str, Dict]:
        """Carica API keys da configurazione"""
        keys = {}

        # Chiave principale dal .env
        main_key = os.getenv('SERVER_API_KEY')
        if main_key:
            keys[main_key] = {
                'name': 'main',
                'permissions': ['all'],
                'rate_limit': 100  # richieste/minuto
            }

        # Chiavi aggiuntive (esempio)
        # Puoi caricarle da database o file JSON
        additional_keys = {
            'client-key-123': {
                'name': 'web_client',
                'permissions': ['generate', 'security'],
                'rate_limit': 60
            },
            'admin-key-456': {
                'name': 'admin',
                'permissions': ['all'],
                'rate_limit': 200
            }
        }

        keys.update(additional_keys)
        return keys

    def verify_key(self, api_key: str) -> Dict:
        """Verifica che l'API key sia valida"""
        if api_key not in self.keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update statistics
        self.stats[api_key]['requests'] += 1
        self.stats[api_key]['last_used'] = datetime.now()

        return self.keys[api_key]

    def check_rate_limit(self, api_key: str) -> bool:
        """Verifica rate limit"""
        if api_key not in self.keys:
            return False

        max_requests = self.keys[api_key].get('rate_limit', 60)
        now = time.time()
        minute_ago = now - 60

        # Rimuovi richieste più vecchie di 1 minuto
        self.rate_limits[api_key] = [
            ts for ts in self.rate_limits[api_key]
            if ts > minute_ago
        ]

        # Controlla limite
        if len(self.rate_limits[api_key]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per minute."
            )

        # Aggiungi richiesta corrente
        self.rate_limits[api_key].append(now)
        return True

    def check_permission(self, api_key: str, action: str) -> bool:
        """Verifica permessi per azione specifica"""
        if api_key not in self.keys:
            return False

        permissions = self.keys[api_key].get('permissions', [])

        if 'all' in permissions or action in permissions:
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for action: {action}"
        )

    def get_stats(self, api_key: Optional[str] = None) -> Dict:
        """Ottiene statistiche utilizzo"""
        if api_key:
            return self.stats.get(api_key, {})
        return dict(self.stats)


# Istanza globale
api_key_manager = APIKeyManager()


# Dependency per FastAPI
def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency per verificare API key nelle route FastAPI

    Usage:
        @app.post("/api/generate")
        async def generate(api_key: str = Depends(verify_api_key)):
            # Route protetta
    """
    api_key = credentials.credentials

    # Verifica validità
    key_info = api_key_manager.verify_key(api_key)

    # Verifica rate limit
    api_key_manager.check_rate_limit(api_key)

    return api_key


def require_permission(action: str):
    """
    Dependency per verificare permessi specifici

    Usage:
        @app.post("/api/admin")
        async def admin_action(
            api_key: str = Depends(verify_api_key),
            _: None = Depends(require_permission('admin'))
        ):
            # Solo utenti con permesso 'admin'
    """
    def permission_checker(api_key: str = Depends(verify_api_key)):
        api_key_manager.check_permission(api_key, action)
        return None

    return permission_checker


# Utility functions
def hash_api_key(api_key: str) -> str:
    """Hash API key per storage sicuro"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(prefix: str = "sk") -> str:
    """Genera nuova API key"""
    import secrets
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


if __name__ == "__main__":
    # Test
    manager = APIKeyManager()

    print("API Keys caricate:")
    for key, info in manager.keys.items():
        print(f"  {key[:20]}... -> {info['name']} (permissions: {info['permissions']})")

    print("\nTest verifica chiave:")
    try:
        main_key = os.getenv('SERVER_API_KEY', 'dev-key-12345')
        info = manager.verify_key(main_key)
        print(f"  ✓ Chiave valida: {info}")
    except HTTPException as e:
        print(f"  ✗ Errore: {e.detail}")

    print("\nStatistiche:")
    print(manager.get_stats())
