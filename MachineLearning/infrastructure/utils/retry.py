"""
Retry Utilities
===============

Decorators and utilities for retrying failed operations.
"""

import time
import logging
from functools import wraps
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """
    Decorator for retrying failed operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function

    Example:
        >>> @retry(max_attempts=3, delay=1.0, backoff=2.0)
        ... def unstable_operation():
        ...     # May fail occasionally
        ...     return api.call()

        >>> @retry(max_attempts=5, exceptions=(NetworkError, TimeoutError))
        ... def network_call():
        ...     return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    attempt += 1

                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


class RetryManager:
    """
    Context manager for retry logic.

    Example:
        >>> manager = RetryManager(max_attempts=3, delay=1.0)
        >>> with manager:
        ...     result = unstable_operation()
    """

    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
        self.attempt = 0

    def __enter__(self):
        self.attempt = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.exceptions):
            self.attempt += 1

            if self.attempt < self.max_attempts:
                current_delay = self.delay * (self.backoff ** (self.attempt - 1))
                logger.warning(
                    f"Operation failed (attempt {self.attempt}/{self.max_attempts}): {exc_val}. "
                    f"Retrying in {current_delay:.1f}s..."
                )
                time.sleep(current_delay)
                return True  # Suppress exception and retry

        return False  # Don't suppress exception


def retry_on_exception(func: Callable, *args, **kwargs) -> any:
    """
    Execute function with retry logic.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function (can include retry params)

    Returns:
        Function result

    Example:
        >>> result = retry_on_exception(
        ...     api.get_data,
        ...     url='https://api.example.com',
        ...     max_attempts=3,
        ...     delay=2.0
        ... )
    """
    max_attempts = kwargs.pop('max_attempts', 3)
    delay = kwargs.pop('delay', 1.0)
    backoff = kwargs.pop('backoff', 2.0)
    exceptions_to_catch = kwargs.pop('exceptions', (Exception,))

    @retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        exceptions=exceptions_to_catch
    )
    def wrapped():
        return func(*args, **kwargs)

    return wrapped()
