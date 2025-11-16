"""Message sent domain event."""

from uuid import UUID

from alphasnob.domain.shared.domain_event import DomainEvent


class MessageSent(DomainEvent):
    """Event emitted when bot sends a message to Telegram.

    This event is useful for:
    - Logging
    - Analytics
    - Triggering follow-up actions
    - Learning from sent messages

    Examples:
        event = MessageSent(
            message_id=UUID(...),
            chat_id=-987654321,
            text="Hello! How are you?",
            persona_mode="alphasnob",
            response_delay_ms=2500,
        )

    Attributes:
        message_id: Internal message UUID
        chat_id: Telegram chat ID
        text: Message text that was sent
        persona_mode: Persona used for generation
        response_delay_ms: Total delay before sending
        decision_score: Decision score that led to response
    """

    message_id: UUID
    chat_id: int
    text: str
    persona_mode: str
    response_delay_ms: int
    decision_score: float | None = None
