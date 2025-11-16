import asyncio
import random
import logging
from typing import Dict

from config.settings import TypingConfig

logger = logging.getLogger(__name__)


class TypingSimulator:

    def __init__(self, typing_config: TypingConfig):
        self.config = typing_config
        logger.info(f"TypingSimulator initialized (enabled: {self.config.enabled})")

    def calculate_read_delay(self, message: str) -> float:
        if not self.config.enabled:
            return 0.0

        words = len(message.split())

        delay_ms = (
            random.randint(
                self.config.read_delay.min_ms,
                self.config.read_delay.max_ms
            ) +
            (words * self.config.read_delay.per_word_ms)
        )

        delay_seconds = delay_ms / 1000.0
        logger.debug(f"Read delay: {delay_ms}ms for {words} words")
        return delay_seconds

    def calculate_typing_delay(self, response: str) -> float:
        if not self.config.enabled or not self.config.typing_action.enabled:
            return 0.0

        char_count = len(response)

        base_delay = self.config.typing_action.base_delay_ms
        char_delay = char_count * self.config.typing_action.per_character_ms

        total_delay = base_delay + char_delay

        randomness = self.config.typing_action.randomness
        variation = total_delay * randomness * (random.random() * 2 - 1)
        total_delay += variation

        total_delay = max(
            self.config.typing_action.min_ms,
            min(total_delay, self.config.typing_action.max_ms)
        )

        delay_seconds = total_delay / 1000.0
        logger.debug(f"Typing delay: {int(total_delay)}ms for {char_count} chars")
        return delay_seconds

    def calculate_thinking_delay(self) -> float:
        if not self.config.enabled:
            return 0.0

        delay_ms = random.randint(
            self.config.thinking_delay.min_ms,
            self.config.thinking_delay.max_ms
        )

        delay_seconds = delay_ms / 1000.0
        logger.debug(f"Thinking delay: {delay_ms}ms")
        return delay_seconds

    async def simulate_read(self, client, chat_id: int, message: str):
        if not self.config.enabled:
            return

        delay = self.calculate_read_delay(message)
        if delay > 0:
            logger.debug(f"Simulating read for {delay:.2f}s")
            await asyncio.sleep(delay)

    async def simulate_typing(self, client, chat_id: int, response: str):
        if not self.config.enabled or not self.config.typing_action.enabled:
            return

        delay = self.calculate_typing_delay(response)
        if delay <= 0:
            return

        logger.debug(f"Showing typing action for {delay:.2f}s")

        try:
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(delay)
        except Exception as e:
            logger.warning(f"Failed to show typing action: {e}")
            await asyncio.sleep(delay)

    async def simulate_full_response_flow(
        self,
        client,
        chat_id: int,
        incoming_message: str,
        response: str
    ) -> Dict[str, int]:
        if not self.config.enabled:
            return {
                'read_delay_ms': 0,
                'thinking_delay_ms': 0,
                'typing_delay_ms': 0,
                'total_delay_ms': 0
            }

        read_delay_s = self.calculate_read_delay(incoming_message)
        thinking_delay_s = self.calculate_thinking_delay()
        typing_delay_s = self.calculate_typing_delay(response)

        total_delay_s = read_delay_s + thinking_delay_s + typing_delay_s

        logger.info(
            f"Simulating human-like flow: "
            f"read={read_delay_s:.1f}s + think={thinking_delay_s:.1f}s + type={typing_delay_s:.1f}s "
            f"= {total_delay_s:.1f}s total"
        )

        if read_delay_s > 0:
            logger.debug("Phase 1: Reading message...")
            await asyncio.sleep(read_delay_s)

        if thinking_delay_s > 0:
            logger.debug("Phase 2: Thinking...")
            await asyncio.sleep(thinking_delay_s)

        if typing_delay_s > 0 and self.config.typing_action.enabled:
            logger.debug("Phase 3: Typing...")
            try:
                async with client.action(chat_id, 'typing'):
                    await asyncio.sleep(typing_delay_s)
            except Exception as e:
                logger.warning(f"Typing action failed: {e}")
                await asyncio.sleep(typing_delay_s)

        return {
            'read_delay_ms': int(read_delay_s * 1000),
            'thinking_delay_ms': int(thinking_delay_s * 1000),
            'typing_delay_ms': int(typing_delay_s * 1000),
            'total_delay_ms': int(total_delay_s * 1000)
        }
