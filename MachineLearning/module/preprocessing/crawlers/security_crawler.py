"""
Security Data Crawler

Crawls security-focused repositories and databases to collect vulnerable code examples.

Sources:
- OWASP vulnerable applications (DVWA, WebGoat, Juice Shop, etc.)
- CVE database via NVD API
- Exploit-DB proof-of-concepts
- Security tools repositories (for pattern learning)

Usage:
    crawler = SecurityDataCrawler()
    dataset = crawler.crawl_all()
    crawler.save_dataset('dataset/security/security_dataset.json')
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class SecurityDataCrawler:
    """Crawler for security-focused repositories and databases"""

    # Intentionally vulnerable applications for training data
    VULNERABLE_REPOS = {
        # Python
        'pygoat': {
            'url': 'OWASP/PyGoat',
            'language': 'python',
            'description': 'Intentionally vulnerable Python web app'
        },
        # JavaScript/Node.js
        'juice-shop': {
            'url': 'juice-shop/juice-shop',
            'language': 'javascript',
            'description': 'OWASP Juice Shop - Vulnerable web app'
        },
        'nodegoat': {
            'url': 'OWASP/NodeGoat',
            'language': 'javascript',
            'description': 'Node.js vulnerable application'
        },
        # PHP
        'dvwa': {
            'url': 'digininja/DVWA',
            'language': 'php',
            'description': 'Damn Vulnerable Web Application'
        },
        'mutillidae': {
            'url': 'webpwnized/mutillidae',
            'language': 'php',
            'description': 'OWASP Mutillidae II'
        },
        # Java
        'webgoat': {
            'url': 'WebGoat/WebGoat',
            'language': 'java',
            'description': 'OWASP WebGoat'
        },
        # Ruby
        'railsgoat': {
            'url': 'OWASP/railsgoat',
            'language': 'ruby',
            'description': 'Ruby on Rails vulnerable app'
        },
    }

    # Security tools repositories (for learning detection patterns)
    SECURITY_TOOLS_REPOS = {
        'bandit': {
            'url': 'PyCQA/bandit',
            'language': 'python',
            'description': 'Python security linter'
        },
        'safety-db': {
            'url': 'pyupio/safety-db',
            'language': 'python',
            'description': 'Known Python vulnerabilities database'
        },
        'semgrep-rules': {
            'url': 'returntocorp/semgrep-rules',
            'language': 'multi',
            'description': 'Security rules for Semgrep'
        },
    }

    def __init__(self, github_token: Optional[str] = None, output_dir: str = 'dataset/security'):
        """
        Initialize security crawler

        Args:
            github_token: GitHub API token for higher rate limits
            output_dir: Directory to save crawled data
        """
        self.github_token = github_token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.dataset = []
        self.seen_hashes = set()

        # GitHub API setup
        self.github_api_base = "https://api.github.com/repos"
        self.github_headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if github_token:
            self.github_headers['Authorization'] = f'token {github_token}'

    def crawl_all(self) -> List[Dict]:
        """
        Crawl all configured sources

        Returns:
            List of vulnerability examples
        """
        logger.info("Starting security data crawling...")

        # Crawl vulnerable applications
        logger.info("Crawling vulnerable repositories...")
        for repo_name, repo_info in tqdm(self.VULNERABLE_REPOS.items(), desc="Vulnerable Repos"):
            try:
                examples = self.crawl_vulnerable_repo(repo_info['url'], repo_info['language'])
                self.dataset.extend(examples)
                logger.info(f"  {repo_name}: {len(examples)} examples")
            except Exception as e:
                logger.error(f"  Error crawling {repo_name}: {e}")

        # Crawl security tools (for pattern learning)
        logger.info("\nCrawling security tools repositories...")
        for tool_name, tool_info in tqdm(self.SECURITY_TOOLS_REPOS.items(), desc="Security Tools"):
            try:
                examples = self.crawl_security_tool_repo(tool_info['url'], tool_info['language'])
                self.dataset.extend(examples)
                logger.info(f"  {tool_name}: {len(examples)} examples")
            except Exception as e:
                logger.error(f"  Error crawling {tool_name}: {e}")

        logger.info(f"\nTotal examples collected: {len(self.dataset)}")
        return self.dataset

    def crawl_vulnerable_repo(self, repo: str, language: str) -> List[Dict]:
        """
        Crawl a vulnerable repository for code examples

        Args:
            repo: Repository in format 'owner/repo'
            language: Programming language

        Returns:
            List of vulnerability examples
        """
        examples = []

        # Get file tree
        files = self._get_repo_files(repo, language)

        for file_path in files[:50]:  # Limit to avoid rate limits
            try:
                content = self._download_file(repo, file_path)
                if content:
                    # Extract vulnerabilities from file
                    vulns = self._extract_vulnerabilities(content, language, file_path, repo)
                    examples.extend(vulns)
            except Exception as e:
                logger.debug(f"Error processing {file_path}: {e}")
                continue

        return examples

    def crawl_security_tool_repo(self, repo: str, language: str) -> List[Dict]:
        """
        Crawl security tool repository to learn detection patterns

        Args:
            repo: Repository in format 'owner/repo'
            language: Programming language

        Returns:
            List of examples with security patterns
        """
        examples = []

        # For Bandit, look for test cases
        if 'bandit' in repo.lower():
            examples = self._crawl_bandit_tests(repo)

        # For Semgrep, look for rules
        elif 'semgrep' in repo.lower():
            examples = self._crawl_semgrep_rules(repo)

        return examples

    def _get_repo_files(self, repo: str, language: str) -> List[str]:
        """Get list of source files from repository"""
        extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.ts'],
            'php': ['.php'],
            'java': ['.java'],
            'ruby': ['.rb'],
            'go': ['.go'],
            'cpp': ['.cpp', '.c', '.h'],
        }

        url = f"{self.github_api_base}/{repo}/git/trees/main?recursive=1"

        try:
            response = requests.get(url, headers=self.github_headers, timeout=30)
            if response.status_code != 200:
                # Try master branch
                url = f"{self.github_api_base}/{repo}/git/trees/master?recursive=1"
                response = requests.get(url, headers=self.github_headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                files = []
                for item in data.get('tree', []):
                    path = item.get('path', '')
                    if any(path.endswith(ext) for ext in extensions.get(language, [])):
                        # Skip test files for now (we want vulnerable code, not test code)
                        if 'test' not in path.lower() and 'spec' not in path.lower():
                            files.append(path)
                return files
        except Exception as e:
            logger.error(f"Error getting file tree: {e}")

        return []

    def _download_file(self, repo: str, file_path: str) -> Optional[str]:
        """Download file content from GitHub"""
        url = f"https://raw.githubusercontent.com/{repo}/main/{file_path}"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                # Try master branch
                url = f"https://raw.githubusercontent.com/{repo}/master/{file_path}"
                response = requests.get(url, timeout=30)

            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.debug(f"Error downloading file: {e}")

        return None

    def _extract_vulnerabilities(
        self,
        code: str,
        language: str,
        file_path: str,
        repo: str
    ) -> List[Dict]:
        """
        Extract vulnerabilities from code

        This is a simple heuristic-based extraction.
        Later phases will use more sophisticated pattern detection.
        """
        vulnerabilities = []

        # Common vulnerability patterns (simplified for initial crawling)
        patterns = {
            'sql_injection': [
                'execute(',
                'executemany(',
                'raw(',
                'query(',
            ],
            'command_injection': [
                'os.system(',
                'subprocess.',
                'eval(',
                'exec(',
            ],
            'xss': [
                'innerHTML',
                'document.write',
                'dangerouslySetInnerHTML',
            ],
            'path_traversal': [
                'open(',
                'file(',
                'readFile',
            ],
        }

        # Check for patterns
        for vuln_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in code:
                    # Create hash for deduplication
                    content_hash = hashlib.sha256(
                        f"{repo}{file_path}{keyword}".encode()
                    ).hexdigest()

                    if content_hash not in self.seen_hashes:
                        self.seen_hashes.add(content_hash)

                        vulnerabilities.append({
                            'code': code[:1000],  # First 1000 chars
                            'language': language,
                            'vulnerability_type': vuln_type,
                            'is_vulnerable': True,
                            'source': 'vulnerable_repo',
                            'repository': repo,
                            'file_path': file_path,
                            'severity': 'HIGH',  # Default for vulnerable repos
                            'cwe_id': self._map_vuln_to_cwe(vuln_type),
                        })
                        break  # One vuln per file for now

        return vulnerabilities

    def _crawl_bandit_tests(self, repo: str) -> List[Dict]:
        """Extract examples from Bandit test cases"""
        # TODO: Implement Bandit test case parsing
        return []

    def _crawl_semgrep_rules(self, repo: str) -> List[Dict]:
        """Extract patterns from Semgrep rules"""
        # TODO: Implement Semgrep rule parsing
        return []

    def _map_vuln_to_cwe(self, vuln_type: str) -> str:
        """Map vulnerability type to CWE ID"""
        mapping = {
            'sql_injection': 'CWE-89',
            'command_injection': 'CWE-78',
            'xss': 'CWE-79',
            'path_traversal': 'CWE-22',
            'rce': 'CWE-94',
            'xxe': 'CWE-611',
            'ssrf': 'CWE-918',
            'deserialization': 'CWE-502',
        }
        return mapping.get(vuln_type, 'CWE-UNKNOWN')

    def save_dataset(self, output_path: str):
        """Save dataset to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.dataset)} examples to {output_path}")

    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = {
            'total_examples': len(self.dataset),
            'by_language': {},
            'by_vulnerability_type': {},
            'by_severity': {},
        }

        for example in self.dataset:
            # Count by language
            lang = example.get('language', 'unknown')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

            # Count by vulnerability type
            vuln = example.get('vulnerability_type', 'unknown')
            stats['by_vulnerability_type'][vuln] = stats['by_vulnerability_type'].get(vuln, 0) + 1

            # Count by severity
            severity = example.get('severity', 'UNKNOWN')
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

        return stats


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize crawler (add GitHub token for better rate limits)
    from config import GITHUB_TOKEN
    crawler = SecurityDataCrawler(github_token=GITHUB_TOKEN)

    # Crawl all sources
    dataset = crawler.crawl_all()

    # Save dataset
    crawler.save_dataset('dataset/security/security_crawled.json')

    # Print statistics
    stats = crawler.get_statistics()
    print("\n=== Dataset Statistics ===")
    print(f"Total examples: {stats['total_examples']}")
    print("\nBy language:")
    for lang, count in stats['by_language'].items():
        print(f"  {lang}: {count}")
    print("\nBy vulnerability type:")
    for vuln, count in stats['by_vulnerability_type'].items():
        print(f"  {vuln}: {count}")
    print("\nBy severity:")
    for severity, count in stats['by_severity'].items():
        print(f"  {severity}: {count}")
