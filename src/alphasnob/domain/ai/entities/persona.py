"""Persona entity - bot personality and behavior configuration."""

from typing import Optional

from alphasnob.domain.shared.base_entity import Entity


class Persona(Entity):
    """Bot persona configuration.

    A persona defines how the bot behaves, speaks, and responds.
    It includes system prompts, examples, and behavioral traits.

    Examples:
        persona = Persona(
            name="alphasnob",
            display_name="AlphaSnob",
            system_prompt="You are an arrogant, sophisticated bot...",
            traits=["sarcastic", "theatrical", "narcissistic"],
            examples=["Omega, you're so basic...", "I'll retreat to my kingdom..."],
        )

    Attributes:
        name: Internal persona identifier (e.g., "alphasnob", "normal", "owner")
        display_name: Human-readable name
        system_prompt: System/instruction prompt for LLM
        traits: List of personality traits
        examples: Example responses in this persona's style
        temperature_override: Optional temperature override for this persona
        is_active: Whether this persona is currently usable
    """

    name: str
    display_name: str
    system_prompt: str
    traits: list[str] = []
    examples: list[str] = []
    temperature_override: Optional[float] = None
    is_active: bool = True

    def has_examples(self) -> bool:
        """Check if persona has style examples.

        Returns:
            True if examples exist, False otherwise
        """
        return len(self.examples) > 0

    def get_example_count(self) -> int:
        """Get number of style examples.

        Returns:
            Number of examples
        """
        return len(self.examples)

    def add_example(self, example: str) -> None:
        """Add style example to persona.

        Args:
            example: Example text

        Side effects:
            - Appends example to examples list
            - Marks entity as updated
        """
        if example and example not in self.examples:
            self.examples.append(example)
            self.mark_updated()

    def remove_example(self, example: str) -> None:
        """Remove style example from persona.

        Args:
            example: Example text to remove

        Side effects:
            - Removes example from list if present
            - Marks entity as updated
        """
        if example in self.examples:
            self.examples.remove(example)
            self.mark_updated()

    def add_trait(self, trait: str) -> None:
        """Add personality trait.

        Args:
            trait: Trait name

        Side effects:
            - Appends trait to traits list
            - Marks entity as updated
        """
        if trait and trait not in self.traits:
            self.traits.append(trait)
            self.mark_updated()

    def has_trait(self, trait: str) -> bool:
        """Check if persona has specific trait.

        Args:
            trait: Trait name

        Returns:
            True if trait exists, False otherwise
        """
        return trait in self.traits

    def deactivate(self) -> None:
        """Deactivate persona (make unavailable).

        Side effects:
            - Sets is_active to False
            - Marks entity as updated
        """
        self.is_active = False
        self.mark_updated()

    def activate(self) -> None:
        """Activate persona (make available).

        Side effects:
            - Sets is_active to True
            - Marks entity as updated
        """
        self.is_active = True
        self.mark_updated()

    def __str__(self) -> str:
        """Return human-readable string."""
        return f"Persona({self.display_name}, traits={len(self.traits)})"
