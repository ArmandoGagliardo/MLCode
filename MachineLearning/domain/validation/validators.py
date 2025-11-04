"""
Validation Layer
================

Reusable validators for input validation across the system.
"""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from domain.exceptions import ValidationError


class Validator:
    """Base validator with common validation methods"""

    @staticmethod
    def validate_url(url: str) -> None:
        """Validate URL format"""
        if not url:
            raise ValidationError("URL cannot be empty")

        if not url.startswith(('http://', 'https://', 'git@')):
            raise ValidationError(f"Invalid URL scheme: {url}")

        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError(f"Invalid URL format: {url}")
        except Exception as e:
            raise ValidationError(f"Invalid URL: {url} - {e}")

    @staticmethod
    def validate_path(path: str, must_exist: bool = False) -> None:
        """Validate file system path"""
        if not path:
            raise ValidationError("Path cannot be empty")

        # Check for path traversal
        if '..' in path:
            raise ValidationError(f"Path traversal not allowed: {path}")

        # Check for absolute paths on Windows/Unix
        if path.startswith(('/etc', '/sys', '/proc', 'C:\\Windows', 'C:\\Program')):
            raise ValidationError(f"Access to system path not allowed: {path}")

        if must_exist and not Path(path).exists():
            raise ValidationError(f"Path does not exist: {path}")

    @staticmethod
    def validate_file_size(path: str, max_mb: int = 100) -> None:
        """Validate file size"""
        if not Path(path).exists():
            raise ValidationError(f"File not found: {path}")

        size_bytes = Path(path).stat().st_size
        max_bytes = max_mb * 1024 * 1024

        if size_bytes > max_bytes:
            raise ValidationError(
                f"File too large: {size_bytes/1024/1024:.1f}MB > {max_mb}MB"
            )

    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, name: str = "Value") -> None:
        """Validate numeric range"""
        if value < min_val or value > max_val:
            raise ValidationError(
                f"{name} must be between {min_val} and {max_val}, got {value}"
            )

    @staticmethod
    def validate_not_empty(value: str, name: str = "Value") -> None:
        """Validate string is not empty"""
        if not value or not value.strip():
            raise ValidationError(f"{name} cannot be empty")

    @staticmethod
    def validate_language(language: str, supported: list) -> None:
        """Validate programming language"""
        if language.lower() not in [lang.lower() for lang in supported]:
            raise ValidationError(
                f"Unsupported language: {language}. Supported: {', '.join(supported)}"
            )


class URLValidator(Validator):
    """Specialized URL validator"""

    @staticmethod
    def validate_github_url(url: str) -> None:
        """Validate GitHub repository URL"""
        Validator.validate_url(url)

        if 'github.com' not in url.lower():
            raise ValidationError(f"Not a GitHub URL: {url}")

        # Pattern: https://github.com/owner/repo
        pattern = r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?(?:/|$)'
        if not re.search(pattern, url):
            raise ValidationError(f"Invalid GitHub URL format: {url}")


class PathValidator(Validator):
    """Specialized path validator"""

    @staticmethod
    def validate_directory(path: str, create: bool = False) -> None:
        """Validate directory path"""
        Validator.validate_path(path)

        p = Path(path)
        if create:
            p.mkdir(parents=True, exist_ok=True)
        elif not p.is_dir():
            raise ValidationError(f"Not a directory: {path}")


class CodeValidator(Validator):
    """Specialized code validator"""

    @staticmethod
    def validate_code_length(code: str, max_length: int = 50000) -> None:
        """Validate code length"""
        if len(code) > max_length:
            raise ValidationError(
                f"Code too long: {len(code)} characters > {max_length}"
            )

    @staticmethod
    def validate_code_syntax(code: str, language: str) -> None:
        """Basic syntax validation"""
        if not code or not code.strip():
            raise ValidationError("Code cannot be empty")

        # Basic checks
        if language == 'python':
            # Check for basic syntax errors
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                raise ValidationError(f"Python syntax error: {e}")
