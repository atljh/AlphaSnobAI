"""Domain-specific exceptions and errors.

These exceptions represent business rule violations and domain constraints.
They should be caught and handled at the application layer.
"""

from typing import Any


class DomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize domain error with message and context.

        Args:
            message: Error description
            **context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        """Return string representation with context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, context={self.context!r})"


class ValidationError(DomainError):
    """Raised when domain validation rules are violated.

    Examples:
        - Invalid email format
        - Value out of allowed range
        - Missing required field
    """


class EntityNotFoundError(DomainError):
    """Raised when an entity cannot be found in repository.

    Examples:
        - User not found by ID
        - Message not found in database
    """


class InvalidOperationError(DomainError):
    """Raised when an operation is not allowed in current state.

    Examples:
        - Cannot send message when bot is stopped
        - Cannot delete message that doesn't belong to user
    """


class DuplicateEntityError(DomainError):
    """Raised when attempting to create duplicate entity.

    Examples:
        - User already exists
        - Message already processed
    """


class InsufficientPermissionsError(DomainError):
    """Raised when user lacks required permissions.

    Examples:
        - Non-owner trying to access owner features
        - Guest trying to modify settings
    """


class ResourceExhaustedError(DomainError):
    """Raised when resource limits are exceeded.

    Examples:
        - API rate limit reached
        - Database connection pool exhausted
        - Memory limit exceeded
    """


class ConfigurationError(DomainError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Missing API key
        - Invalid model name
        - Malformed config file
    """
