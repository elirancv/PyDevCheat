"""
Custom exceptions for the PyDevCheat package.
"""


class PyDevCheatError(Exception):
    """Base exception for all PyDevCheat errors."""

    pass


class SourceError(PyDevCheatError):
    """Exception raised when a source-specific error occurs."""

    pass


class NetworkError(PyDevCheatError):
    """Exception raised when a network-related error occurs."""

    pass


class TimeoutError(PyDevCheatError):
    """Exception raised when an operation times out."""

    pass
