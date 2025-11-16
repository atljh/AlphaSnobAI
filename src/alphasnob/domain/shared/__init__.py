"""Shared kernel - Base classes, value objects, and utilities used across all domains."""

from alphasnob.domain.shared.base_entity import Entity
from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.domain_event import DomainEvent
from alphasnob.domain.shared.errors import (
    DomainError,
    EntityNotFoundError,
    InvalidOperationError,
    ValidationError,
)

__all__ = [
    "Entity",
    "ValueObject",
    "DomainEvent",
    "DomainError",
    "ValidationError",
    "EntityNotFoundError",
    "InvalidOperationError",
]
