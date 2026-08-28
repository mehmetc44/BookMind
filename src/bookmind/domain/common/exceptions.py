"""domain.common.exceptions — Domain-wide exception definitions."""


class BookMindException(Exception):
    """Base exception for all BookMind domain errors."""


class InvalidPDFException(BookMindException):
    """Raised when the provided PDF is invalid or cannot be parsed."""


class BookMapNotFoundException(BookMindException):
    """Raised when a requested book map is not found in the storage."""
