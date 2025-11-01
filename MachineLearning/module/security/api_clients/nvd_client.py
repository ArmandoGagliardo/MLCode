"""
NVD (National Vulnerability Database) API Client

Fetches vulnerability data from NIST's National Vulnerability Database.
API Documentation: https://nvd.nist.gov/developers/vulnerabilities

Usage:
    client = NVDAPIClient(api_key='your_key')
    cves = client.get_cves(start_date='2023-01-01', end_date='2023-12-31')
"""

import requests
import time
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NVDAPIClient:
    """Client for NVD REST API v2.0"""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RATE_LIMIT_DELAY = 6  # seconds between requests (public API: 5 req/30sec)
    RATE_LIMIT_DELAY_WITH_KEY = 0.6  # With API key: 50 req/30sec

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NVD API client

        Args:
            api_key: Optional API key for higher rate limits
                    Get one at: https://nvd.nist.gov/developers/request-an-api-key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.delay = self.RATE_LIMIT_DELAY_WITH_KEY if api_key else self.RATE_LIMIT_DELAY
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, params: Dict) -> Dict:
        """
        Make API request with rate limiting and error handling

        Args:
            params: Query parameters

        Returns:
            API response JSON
        """
        self._rate_limit()

        headers = {}
        if self.api_key:
            headers['apiKey'] = self.api_key

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"NVD API request failed: {e}")
            return {'vulnerabilities': []}

    def get_cves(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cve_id: Optional[str] = None,
        keyword: Optional[str] = None,
        results_per_page: int = 100,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch CVEs from NVD

        Args:
            start_date: Publication start date (ISO 8601 format: YYYY-MM-DD)
            end_date: Publication end date
            cve_id: Specific CVE ID (e.g., 'CVE-2023-12345')
            keyword: Keyword search in description
            results_per_page: Number of results per API call (max 2000)
            max_results: Maximum total results to fetch

        Returns:
            List of CVE dictionaries
        """
        params = {
            'resultsPerPage': min(results_per_page, 2000)
        }

        if cve_id:
            params['cveId'] = cve_id
        if start_date:
            params['pubStartDate'] = f"{start_date}T00:00:00.000"
        if end_date:
            params['pubEndDate'] = f"{end_date}T23:59:59.999"
        if keyword:
            params['keywordSearch'] = keyword

        all_cves = []
        start_index = 0

        while True:
            params['startIndex'] = start_index

            logger.info(f"Fetching CVEs from index {start_index}...")
            data = self._make_request(params)

            if 'vulnerabilities' not in data:
                break

            vulnerabilities = data['vulnerabilities']
            if not vulnerabilities:
                break

            # Parse CVEs
            for item in vulnerabilities:
                cve_data = self._parse_cve(item)
                if cve_data:
                    all_cves.append(cve_data)

            logger.info(f"Fetched {len(vulnerabilities)} CVEs (total: {len(all_cves)})")

            # Check if we should continue
            if max_results and len(all_cves) >= max_results:
                all_cves = all_cves[:max_results]
                break

            # Check if there are more results
            total_results = data.get('totalResults', 0)
            if start_index + len(vulnerabilities) >= total_results:
                break

            start_index += len(vulnerabilities)

        logger.info(f"Total CVEs fetched: {len(all_cves)}")
        return all_cves

    def _parse_cve(self, vulnerability_item: Dict) -> Optional[Dict]:
        """
        Parse CVE item from API response

        Args:
            vulnerability_item: CVE item from API

        Returns:
            Parsed CVE dictionary
        """
        try:
            cve = vulnerability_item.get('cve', {})
            cve_id = cve.get('id', '')

            # Get description
            descriptions = cve.get('descriptions', [])
            description = next(
                (desc['value'] for desc in descriptions if desc.get('lang') == 'en'),
                ''
            )

            # Get CVSS scores
            metrics = cve.get('metrics', {})
            cvss_v3 = metrics.get('cvssMetricV31', [{}])[0] if 'cvssMetricV31' in metrics else {}
            cvss_data = cvss_v3.get('cvssData', {})

            cvss_score = cvss_data.get('baseScore', 0.0)
            cvss_severity = cvss_data.get('baseSeverity', 'UNKNOWN')
            cvss_vector = cvss_data.get('vectorString', '')

            # Get CWE IDs
            weaknesses = cve.get('weaknesses', [])
            cwe_ids = []
            for weakness in weaknesses:
                for desc in weakness.get('description', []):
                    value = desc.get('value', '')
                    if value.startswith('CWE-'):
                        cwe_ids.append(value)

            # Get references
            references = []
            for ref in cve.get('references', []):
                references.append({
                    'url': ref.get('url', ''),
                    'source': ref.get('source', ''),
                    'tags': ref.get('tags', [])
                })

            # Get published date
            published = cve.get('published', '')

            return {
                'cve_id': cve_id,
                'description': description,
                'cvss_score': cvss_score,
                'cvss_severity': cvss_severity,
                'cvss_vector': cvss_vector,
                'cwe_ids': cwe_ids,
                'references': references,
                'published_date': published,
                'source': 'NVD'
            }

        except Exception as e:
            logger.error(f"Error parsing CVE: {e}")
            return None

    def get_recent_cves(self, days: int = 30, max_results: Optional[int] = 1000) -> List[Dict]:
        """
        Get CVEs from the last N days

        Args:
            days: Number of days to look back
            max_results: Maximum results to return

        Returns:
            List of recent CVEs
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.get_cves(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=max_results
        )

    def save_cves_to_file(self, cves: List[Dict], output_path: str):
        """
        Save CVEs to JSON file

        Args:
            cves: List of CVE dictionaries
            output_path: Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cves, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(cves)} CVEs to {output_path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize client (add API key for better rate limits)
    client = NVDAPIClient(api_key=None)  # Add your API key here

    # Get recent CVEs
    print("Fetching recent CVEs...")
    recent_cves = client.get_recent_cves(days=7, max_results=100)

    print(f"\nFound {len(recent_cves)} recent CVEs")

    # Display first few
    for cve in recent_cves[:5]:
        print(f"\n{cve['cve_id']} - {cve['cvss_severity']} ({cve['cvss_score']})")
        print(f"CWE: {', '.join(cve['cwe_ids'])}")
        print(f"Description: {cve['description'][:100]}...")

    # Save to file
    output_file = 'dataset/security/nvd_recent.json'
    client.save_cves_to_file(recent_cves, output_file)
    print(f"\nSaved to {output_file}")
