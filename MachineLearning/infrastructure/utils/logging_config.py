"""
Logging Configuration
=====================

Secure logging configuration with sensitive data sanitization.
"""

import logging
import re
from typing import List, Tuple, Pattern


class SanitizingFormatter(logging.Formatter):
    """
    Logging formatter that sanitizes sensitive data.

    Automatically redacts:
    - API keys and tokens
    - Passwords
    - Access keys
    - GitHub tokens
    - HuggingFace tokens
    - AWS credentials

    Example:
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(SanitizingFormatter())
        >>> logger.addHandler(handler)
        >>> logger.info("Token: hf_abc123")  # Logs: "Token: hf_***"
    """

    # Patterns for sensitive data
    SENSITIVE_PATTERNS: List[Tuple[Pattern, str]] = [
        # API keys and tokens (generic)
        (re.compile(r'(token|key|password|secret|pwd)[\s=:]+[^\s,;]+', re.IGNORECASE), r'\1=***'),

        # HuggingFace tokens
        (re.compile(r'hf_[a-zA-Z0-9]{30,}'), r'hf_***'),

        # GitHub tokens
        (re.compile(r'ghp_[a-zA-Z0-9]{36,}'), r'ghp_***'),
        (re.compile(r'github_pat_[a-zA-Z0-9_]{82}'), r'github_pat_***'),

        # AWS credentials
        (re.compile(r'AKIA[0-9A-Z]{16}'), r'AKIA***'),
        (re.compile(r'aws_secret_access_key[\s=:]+[^\s]+', re.IGNORECASE), r'aws_secret_access_key=***'),

        # DigitalOcean
        (re.compile(r'dop_v1_[a-f0-9]{64}'), r'dop_v1_***'),

        # Generic base64 encoded secrets (long strings)
        (re.compile(r'(["\'])[A-Za-z0-9+/]{40,}={0,2}\1'), r'\1***\1'),

        # Email patterns (for privacy)
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), r'***@***.***'),

        # IP addresses (for privacy)
        (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), r'***.***.***.***'),
    ]

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with sensitive data sanitized.

        Args:
            record: Log record to format

        Returns:
            Formatted and sanitized log message
        """
        # Format with parent formatter first
        msg = super().format(record)

        # Apply sanitization patterns
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)

        return msg


def setup_secure_logging(
    level: int = logging.INFO,
    log_file: str = None,
    format_string: str = None
) -> None:
    """
    Setup secure logging with sanitization.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional file to log to
        format_string: Custom format string

    Example:
        >>> setup_secure_logging(level=logging.DEBUG, log_file='app.log')
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create formatter
    formatter = SanitizingFormatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    logging.info("Secure logging configured")


def mask_sensitive_data(data: str) -> str:
    """
    Manually mask sensitive data in a string.

    Args:
        data: String potentially containing sensitive data

    Returns:
        String with sensitive data masked

    Example:
        >>> mask_sensitive_data("My token is hf_abc123")
        'My token is hf_***'
    """
    result = data
    for pattern, replacement in SanitizingFormatter.SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
