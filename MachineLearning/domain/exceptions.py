"""
Custom Exceptions
=================

Domain-specific exceptions for better error handling and debugging.
"""


class MLProjectException(Exception):
    """Base exception for all project errors"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParsingError(MLProjectException):
    """Error during code parsing"""
    pass


class StorageError(MLProjectException):
    """Error during storage operations"""
    pass


class ValidationError(MLProjectException):
    """Error during validation"""
    pass


class ConfigurationError(MLProjectException):
    """Error in configuration"""
    pass


class TrainingError(MLProjectException):
    """Error during model training"""
    pass


class QualityError(MLProjectException):
    """Error in quality filtering"""
    pass


class DuplicationError(MLProjectException):
    """Error in duplicate detection"""
    pass


class RepositoryError(MLProjectException):
    """Error accessing repository"""
    pass


class AuthenticationError(MLProjectException):
    """Authentication failure"""
    pass


class NetworkError(MLProjectException):
    """Network-related error"""
    pass
