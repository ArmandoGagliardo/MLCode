"""
Brev NVIDIA Instance API Client

Client per comunicare con istanze Brev di NVIDIA per l'inferenza di modelli.
Supporta code generation, text classification, e security analysis.

Usage:
    client = BrevClient(api_url="https://your-brev-instance.com")
    response = client.generate_code("Create a sum function in Python")
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class BrevResponse:
    """Response from Brev API"""
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BrevClient:
    """Client for Brev NVIDIA instance API"""

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Brev client

        Args:
            api_url: URL dell'istanza Brev (es: https://your-instance.brev.dev)
            api_key: API key opzionale per autenticazione
            timeout: Timeout per le richieste in secondi
            max_retries: Numero massimo di retry in caso di errore
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        # Headers predefiniti
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'BrevClient/1.0'
        }

        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def _make_request(
        self,
        endpoint: str,
        method: str = 'POST',
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> BrevResponse:
        """
        Effettua una richiesta HTTP all'API

        Args:
            endpoint: Endpoint API
            method: Metodo HTTP
            data: Dati da inviare
            retry_count: Contatore retry

        Returns:
            BrevResponse con risultato
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            logger.info(f"Request to {url} (attempt {retry_count + 1}/{self.max_retries + 1})")

            if method == 'POST':
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout
                )
            elif method == 'GET':
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=data,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check status code
            response.raise_for_status()

            # Parse response
            result = response.json()

            return BrevResponse(
                success=True,
                data=result,
                request_id=response.headers.get('X-Request-ID')
            )

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")

            if retry_count < self.max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(endpoint, method, data, retry_count + 1)

            return BrevResponse(
                success=False,
                data=None,
                error="Request timeout"
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")

            return BrevResponse(
                success=False,
                data=None,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")

            if retry_count < self.max_retries:
                time.sleep(2 ** retry_count)
                return self._make_request(endpoint, method, data, retry_count + 1)

            return BrevResponse(
                success=False,
                data=None,
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}")

            return BrevResponse(
                success=False,
                data=None,
                error=str(e)
            )

    def health_check(self) -> BrevResponse:
        """
        Verifica lo stato dell'istanza Brev

        Returns:
            BrevResponse con stato del servizio
        """
        return self._make_request('/health', method='GET')

    def generate_code(
        self,
        prompt: str,
        language: str = 'python',
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> BrevResponse:
        """
        Genera codice da un prompt

        Args:
            prompt: Descrizione del codice da generare
            language: Linguaggio di programmazione
            max_length: Lunghezza massima output
            temperature: Creatività (0.0-1.0)
            top_p: Nucleus sampling parameter

        Returns:
            BrevResponse con codice generato
        """
        data = {
            'task': 'code_generation',
            'prompt': prompt,
            'language': language,
            'max_length': max_length,
            'temperature': temperature,
            'top_p': top_p
        }

        return self._make_request('/api/generate', data=data)

    def classify_text(
        self,
        text: str,
        classes: Optional[List[str]] = None
    ) -> BrevResponse:
        """
        Classifica un testo

        Args:
            text: Testo da classificare
            classes: Lista di classi possibili (opzionale)

        Returns:
            BrevResponse con classe predetta
        """
        data = {
            'task': 'text_classification',
            'text': text,
            'classes': classes
        }

        return self._make_request('/api/classify', data=data)

    def analyze_security(
        self,
        code: str,
        language: str = 'python',
        scan_type: str = 'quick'
    ) -> BrevResponse:
        """
        Analizza il codice per vulnerabilità

        Args:
            code: Codice da analizzare
            language: Linguaggio di programmazione
            scan_type: Tipo di scan ('quick' o 'deep')

        Returns:
            BrevResponse con vulnerabilità trovate
        """
        data = {
            'task': 'security_analysis',
            'code': code,
            'language': language,
            'scan_type': scan_type
        }

        return self._make_request('/api/security', data=data)

    def batch_generate(
        self,
        prompts: List[str],
        language: str = 'python'
    ) -> BrevResponse:
        """
        Genera codice per multiple richieste

        Args:
            prompts: Lista di prompt
            language: Linguaggio di programmazione

        Returns:
            BrevResponse con lista di codici generati
        """
        data = {
            'task': 'batch_code_generation',
            'prompts': prompts,
            'language': language
        }

        return self._make_request('/api/batch', data=data)

    def get_model_info(self) -> BrevResponse:
        """
        Ottiene informazioni sul modello caricato

        Returns:
            BrevResponse con info del modello
        """
        return self._make_request('/api/model/info', method='GET')

    def get_statistics(self) -> BrevResponse:
        """
        Ottiene statistiche di utilizzo

        Returns:
            BrevResponse con statistiche
        """
        return self._make_request('/api/stats', method='GET')


class BrevClientPool:
    """Pool di client Brev per load balancing"""

    def __init__(self, instance_urls: List[str], api_key: Optional[str] = None):
        """
        Initialize client pool

        Args:
            instance_urls: Lista di URL delle istanze Brev
            api_key: API key condivisa
        """
        self.clients = [
            BrevClient(url, api_key)
            for url in instance_urls
        ]
        self.current_index = 0

    def get_client(self) -> BrevClient:
        """Ottiene il prossimo client (round-robin)"""
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.clients)
        return client

    def health_check_all(self) -> Dict[str, BrevResponse]:
        """Verifica lo stato di tutte le istanze"""
        results = {}
        for i, client in enumerate(self.clients):
            results[f"instance_{i}"] = client.health_check()
        return results


if __name__ == "__main__":
    # Example usage
    import os

    logging.basicConfig(level=logging.INFO)

    # Initialize client
    api_url = os.getenv('BREV_API_URL', 'http://localhost:8000')
    api_key = os.getenv('BREV_API_KEY')

    client = BrevClient(api_url, api_key)

    # Health check
    print("\n[TEST] Health Check...")
    response = client.health_check()
    print(f"Success: {response.success}")
    if response.success:
        print(f"Data: {response.data}")
    else:
        print(f"Error: {response.error}")

    # Generate code
    print("\n[TEST] Code Generation...")
    response = client.generate_code(
        "Create a sum function in Python that takes two numbers"
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Generated code:\n{response.data.get('code', 'N/A')}")
    else:
        print(f"Error: {response.error}")

    # Security analysis
    print("\n[TEST] Security Analysis...")
    test_code = """
def execute_command(user_input):
    import os
    os.system(user_input)  # Vulnerable!
"""
    response = client.analyze_security(test_code)
    print(f"Success: {response.success}")
    if response.success:
        vulns = response.data.get('vulnerabilities', [])
        print(f"Found {len(vulns)} vulnerabilities")
    else:
        print(f"Error: {response.error}")
