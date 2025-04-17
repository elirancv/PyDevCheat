import logging
from typing import TypeVar, Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
from httpx import HTTPError, RequestError
import concurrent.futures
import textwrap

logger = logging.getLogger(__name__)

T = TypeVar('T')

def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retry_on_exceptions: tuple = (HTTPError, RequestError)
) -> Callable:
    """
    Create a retry decorator with configurable parameters.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_on_exceptions: Tuple of exceptions to retry on
        
    Returns:
        A retry decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_on_exceptions),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG)
    )

class RetryableError(Exception):
    """Base class for retryable errors."""
    pass

class NetworkError(RetryableError):
    """Raised when a network-related error occurs."""
    pass

class SourceError(RetryableError):
    """Raised when a source-specific error occurs."""
    pass

def handle_source_error(source: str, error: Exception) -> None:
    """
    Handle source-specific errors with proper logging and error transformation.
    
    Args:
        source: Name of the source where the error occurred
        error: The original exception
    """
    error_msg = f"Error in {source} source: {str(error)}"
    logger.error(error_msg)
    
    if isinstance(error, (HTTPError, RequestError)):
        raise NetworkError(error_msg) from error
    else:
        raise SourceError(error_msg) from error

def with_timeout(func: Callable[..., T], timeout: float) -> T:
    """
    Execute a function with a timeout.

    Args:
        func: The function to execute
        timeout: Timeout in seconds

    Returns:
        The result of the function

    Raises:
        TimeoutError: If the function execution exceeds the timeout
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"Function execution timed out after {timeout} seconds")

def wrap_text(text, width=80):
    """
    Wrap text to a specified width.

    Args:
        text: Text to wrap (string or list of strings)
        width: Maximum width of wrapped lines (default: 80)

    Returns:
        Wrapped text as a string
    """
    if isinstance(text, list):
        text = '\n'.join(text)
    return textwrap.fill(text, width=width) 