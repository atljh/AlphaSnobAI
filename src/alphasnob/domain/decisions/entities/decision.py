"""Decision entity - result of decision-making process."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from alphasnob.domain.decisions.value_objects.decision_factors import DecisionFactors
from alphasnob.domain.decisions.value_objects.probability import Probability
from alphasnob.domain.shared.base_entity import Entity


class Decision(Entity):
    """Decision on whether to respond to a message.

    Encapsulates the result of the decision-making process along with
    reasoning and timing information.

    This entity is created for every incoming message and stored for analytics.

    Examples:
        decision = Decision(
            message_id=UUID(...),
            should_respond=True,
            probability=Probability(0.85),
            factors=DecisionFactors(...),
            reasoning="High trust user in private chat",
            persona_mode="alphasnob",
        )

    Attributes:
        message_id: UUID of message this decision is for
        should_respond: Whether bot should respond
        probability: Final probability score
        factors: Decision factors used
        reasoning: Human-readable explanation
        persona_mode: Persona selected for response (if responding)
        estimated_delay_ms: Estimated response delay
    """

    message_id: UUID
    should_respond: bool
    probability: Probability
    factors: DecisionFactors
    reasoning: str
    persona_mode: Optional[str] = None
    estimated_delay_ms: Optional[int] = None

    def get_summary(self) -> str:
        """Get summary of decision.

        Returns:
            One-line summary of decision
        """
        action = "RESPOND" if self.should_respond else "SKIP"
        prob = self.probability.as_percentage()
        persona = f" as {self.persona_mode}" if self.persona_mode else ""
        return f"{action} ({prob}){persona}: {self.reasoning}"

    def get_detailed_report(self) -> str:
        """Get detailed decision report.

        Returns:
            Multi-line detailed report
        """
        lines = [
            "=== Decision Report ===",
            f"Message ID: {self.message_id}",
            f"Should Respond: {self.should_respond}",
            f"Probability: {self.probability.as_percentage()}",
            f"Reasoning: {self.reasoning}",
        ]

        if self.persona_mode:
            lines.append(f"Persona: {self.persona_mode}")

        if self.estimated_delay_ms:
            lines.append(f"Estimated Delay: {self.estimated_delay_ms}ms")

        lines.append("\n=== Decision Factors ===")
        lines.append(self.factors.get_explanation())

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return summary string."""
        return self.get_summary()
