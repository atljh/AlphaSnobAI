"""Base Value Object class for all domain value objects.

Value Objects are immutable objects that are defined by their attributes,
not by an identity. Two value objects with the same attributes are considered equal.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    """Base class for all domain value objects.

    Value Objects have:
    - No unique identity
    - Immutability (frozen=True)
    - Equality based on attributes
    - Value semantics (can be freely replaced)

    Examples:
        Email, Money, Temperature, Probability, ChatId, UserId

    Usage:
        class Email(ValueObject):
            address: str

            @field_validator('address')
            def validate_email(cls, v: str) -> str:
                if '@' not in v:
                    raise ValueError('Invalid email')
                return v.lower()
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,  # Value objects are immutable
        validate_assignment=True,  # Validate on creation
        arbitrary_types_allowed=True,  # Allow custom types
        extra="forbid",  # Forbid extra attributes
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if all attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Hash based on all attributes for use in sets and dicts."""
        return hash(tuple(sorted(self.model_dump().items())))

    def __repr__(self) -> str:
        """Return detailed string representation."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items())
        return f"{self.__class__.__name__}({attrs})"

    def __str__(self) -> str:
        """Return human-readable string representation."""
        # If there's only one field, return its value
        fields = self.model_dump()
        if len(fields) == 1:
            return str(list(fields.values())[0])
        return repr(self)
