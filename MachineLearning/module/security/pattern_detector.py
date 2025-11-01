"""
Pattern-Based Vulnerability Detector

Fast, rule-based vulnerability detection using regex and pattern matching.
Suitable for quick scans and known vulnerability patterns.

Usage:
    from module.security.pattern_detector import PatternBasedDetector

    detector = PatternBasedDetector()
    vulnerabilities = detector.scan_code(code, language='python')
"""

import re
from typing import List, Dict, Optional
from pathlib import Path
import logging

from .patterns.vulnerability_patterns import (
    VULNERABILITY_PATTERNS,
    get_patterns_for_language,
    get_vulnerability_info,
    SEVERITY_LEVELS
)

logger = logging.getLogger(__name__)


class PatternBasedDetector:
    """Fast pattern-based vulnerability detector"""

    def __init__(self):
        """Initialize pattern detector"""
        self.patterns = VULNERABILITY_PATTERNS
        self.stats = {
            'files_scanned': 0,
            'vulnerabilities_found': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0},
            'by_type': {},
        }

    def scan_code(
        self,
        code: str,
        language: str = 'python',
        file_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Scan code for vulnerabilities using pattern matching

        Args:
            code: Source code to scan
            language: Programming language
            file_path: Optional file path for reporting

        Returns:
            List of detected vulnerabilities
        """
        self.stats['files_scanned'] += 1
        vulnerabilities = []

        # Get patterns for this language
        language_patterns = get_patterns_for_language(language)

        if not language_patterns:
            logger.warning(f"No patterns available for language: {language}")
            return []

        # Check each vulnerability type
        for vuln_type, vuln_data in language_patterns.items():
            patterns = vuln_data['patterns']
            info = vuln_data['info']

            # Check if this is a false positive (safe pattern detected)
            safe_patterns = info.get('safe_patterns', [])
            has_safe_pattern = any(
                re.search(pattern, code, re.IGNORECASE)
                for pattern in safe_patterns
            )

            # Scan for vulnerable patterns
            for pattern in patterns:
                try:
                    matches = list(re.finditer(pattern, code, re.IGNORECASE))

                    for match in matches:
                        # Skip if safe pattern is nearby
                        if has_safe_pattern:
                            # Check if safe pattern is within 3 lines
                            match_line = code[:match.start()].count('\n')
                            nearby_code = '\n'.join(
                                code.split('\n')[max(0, match_line-3):match_line+4]
                            )
                            if any(re.search(sp, nearby_code, re.IGNORECASE) for sp in safe_patterns):
                                continue

                        # Calculate line number
                        line_num = code[:match.start()].count('\n') + 1

                        # Extract code snippet (full line)
                        lines = code.split('\n')
                        if line_num <= len(lines):
                            code_snippet = lines[line_num - 1].strip()
                        else:
                            code_snippet = match.group(0)

                        # Create vulnerability report
                        vulnerability = {
                            'type': vuln_type,
                            'severity': info['severity'],
                            'cwe': info['cwe'],
                            'owasp': info.get('owasp', 'N/A'),
                            'line': line_num,
                            'column': match.start() - code.rfind('\n', 0, match.start()),
                            'code_snippet': code_snippet,
                            'matched_pattern': match.group(0)[:100],  # First 100 chars
                            'description': info['description'],
                            'fix': info['fix'],
                            'references': info.get('references', []),
                            'file': file_path or '<string>',
                            'confidence': 'HIGH' if not has_safe_pattern else 'MEDIUM',
                        }

                        vulnerabilities.append(vulnerability)

                        # Update stats
                        self.stats['vulnerabilities_found'] += 1
                        self.stats['by_severity'][info['severity']] += 1
                        self.stats['by_type'][vuln_type] = self.stats['by_type'].get(vuln_type, 0) + 1

                except re.error as e:
                    logger.error(f"Regex error in pattern {pattern}: {e}")
                    continue

        # Sort by severity
        vulnerabilities.sort(
            key=lambda v: SEVERITY_LEVELS.get(v['severity'], 0),
            reverse=True
        )

        return vulnerabilities

    def scan_file(self, file_path: str, language: Optional[str] = None) -> List[Dict]:
        """
        Scan a file for vulnerabilities

        Args:
            file_path: Path to file
            language: Programming language (auto-detected if None)

        Returns:
            List of vulnerabilities
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        # Auto-detect language from extension
        if language is None:
            language = self._detect_language(path)

        if language is None:
            logger.warning(f"Could not detect language for: {file_path}")
            return []

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            return self.scan_code(code, language, str(path))

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Scan all files in a directory

        Args:
            directory: Directory path
            recursive: Scan recursively
            extensions: List of file extensions to scan (e.g., ['.py', '.js'])

        Returns:
            Dictionary mapping file paths to vulnerability lists
        """
        path = Path(directory)

        if not path.is_dir():
            logger.error(f"Not a directory: {directory}")
            return {}

        # Default extensions
        if extensions is None:
            extensions = ['.py', '.js', '.java', '.php', '.rb', '.go', '.cpp', '.c', '.h']

        results = {}

        # Find all files
        pattern = '**/*' if recursive else '*'
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix in extensions:
                logger.info(f"Scanning: {file_path}")
                vulnerabilities = self.scan_file(str(file_path))

                if vulnerabilities:
                    results[str(file_path)] = vulnerabilities

        return results

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Auto-detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.java': 'java',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.sh': 'shell',
        }

        return extension_map.get(file_path.suffix)

    def get_statistics(self) -> Dict:
        """Get scanning statistics"""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset statistics counters"""
        self.stats = {
            'files_scanned': 0,
            'vulnerabilities_found': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0},
            'by_type': {},
        }

    def format_report(self, vulnerabilities: List[Dict], verbose: bool = False) -> str:
        """
        Format vulnerabilities as a human-readable report

        Args:
            vulnerabilities: List of vulnerabilities
            verbose: Include detailed information

        Returns:
            Formatted report string
        """
        if not vulnerabilities:
            return "✅ No vulnerabilities found!"

        report = []
        report.append(f"\n⚠️  Found {len(vulnerabilities)} potential vulnerabilities:\n")
        report.append("=" * 80)

        for i, vuln in enumerate(vulnerabilities, 1):
            severity_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🔵',
                'INFO': '⚪'
            }

            emoji = severity_emoji.get(vuln['severity'], '⚪')

            report.append(f"\n{i}. {emoji} [{vuln['severity']}] {vuln['type'].upper().replace('_', ' ')}")
            report.append(f"   CWE: {vuln['cwe']} | OWASP: {vuln['owasp']}")
            report.append(f"   File: {vuln['file']} (Line {vuln['line']})")
            report.append(f"   Code: {vuln['code_snippet']}")
            report.append(f"   Issue: {vuln['description']}")

            if verbose:
                report.append(f"   Fix: {vuln['fix']}")
                report.append(f"   Confidence: {vuln['confidence']}")

                if vuln.get('references'):
                    report.append("   References:")
                    for ref in vuln['references'][:2]:  # Limit to 2 refs
                        report.append(f"     - {ref}")

            report.append("-" * 80)

        # Summary
        report.append("\n📊 Summary:")
        severity_counts = {}
        for vuln in vulnerabilities:
            sev = vuln['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                report.append(f"   {severity}: {count}")

        return '\n'.join(report)


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    detector = PatternBasedDetector()

    # Example vulnerable code
    test_code = """
import os
import subprocess

def get_user(user_id):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id='{user_id}'"
    cursor.execute(query)

def run_command(filename):
    # Command Injection vulnerability
    os.system(f"cat {filename}")

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"

def fetch_url(url):
    # SSRF vulnerability
    import requests
    return requests.get(url)
"""

    print("Scanning test code...")
    vulnerabilities = detector.scan_code(test_code, language='python')

    print(detector.format_report(vulnerabilities, verbose=True))
