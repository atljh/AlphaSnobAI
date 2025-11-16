import logging
import random
from typing import List, Optional
from pathlib import Path

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from utils.corpus_loader import CorpusLoader
from core.memory import Message

logger = logging.getLogger(__name__)


class StyleEngine:

    def __init__(
        self,
        corpus_path: Path,
        provider: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.9,
        max_tokens: int = 500
    ):
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.corpus = CorpusLoader(corpus_path)

        if provider == "claude":
            if AsyncAnthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = model or "claude-3-5-sonnet-20241022"
        elif provider == "openai":
            if AsyncOpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model or "gpt-4"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info(f"StyleEngine initialized with {provider} ({self.model})")

    def _detect_tone(self, text: str) -> str:

        aggressive_markers = [
            "бля", "хуй", "пиз", "еб", "сука", "дура", "идиот",
            "тупой", "дебил", "урод", "говно", "!!"
        ]

        friendly_markers = [
            "привет", "спасибо", "пожалуйста", "хорошо", "отлично",
            "круто", "класс", "😊", "❤", "👍"
        ]

        aggressive_count = sum(1 for marker in aggressive_markers if marker in text_lower)
        friendly_count = sum(1 for marker in friendly_markers if marker in text_lower)

        if aggressive_count > 0:
            return "aggressive"
        elif friendly_count > 0:
            return "friendly"
        else:
            return "neutral"

    def _build_system_prompt(self, tone: str, corpus_examples: List[str]) -> str:
        examples_text = "\n".join(f"- {ex}" for ex in corpus_examples)

        base_instruction = """Ты — AlphaSnob, элитарный эстет-псих с гипертрофированным чувством собственного превосходства.

            СТИЛЬ:
            1. Бордовый троллинг: гипертрофированные оскорбления, театральные унижения, гротескные угрозы
            2. Эстетизм American Psycho: детальные описания ухода, косметики, еды как религиозных ритуалов
            3. Гиперболы: абсурдные, поэтичные преувеличения ("удалюсь в царство ароматов", "разорву на столько частей, что бог не соберёт")
            4. Нарциссизм и снобизм: постоянное подчёркивание своего богатства, вкуса, превосходства
            5. Смесь пафоса и быта: от унитаза до метафизики в одном предложении

            ВАЖНО:
            - Используй русский язык
            - Будь гротескным, но остроумным
            - Переходи от грубости к эстетике плавно
            - Используй длинные, детализированные описания
            - Не бойся абсурда и театральности
            """

        tone_instruction = {
            "aggressive": "\nТОН: Собеседник агрессивен. Ответь ещё более жёстко: больше треша, унижений и угроз.",
            "neutral": "\nТОН: Собеседник нейтрален. Покажи эстетику, пафос и лёгкий снобизм.",
            "friendly": "\nТОН: Собеседник дружелюбен. Используй сарказм, снобизм и эстетику с иронией."
        }

        examples_section = f"\n\nПРИМЕРЫ СТИЛЯ:\n{examples_text}\n\nИспользуй эти примеры как вдохновение, но не копируй дословно. Создавай новые фразы в том же духе."

        return base_instruction + tone_instruction.get(tone, "") + examples_section

    def _build_context_string(self, context_messages: List[Message]) -> str:
        if not context_messages:
            return "Контекст пуст."

        context_lines = []
        for msg in context_messages[-20:]:  # Last 20 messages max
            context_lines.append(f"{msg.username}: {msg.text}")

        return "\n".join(context_lines)

    async def generate_response(
        self,
        incoming_message: str,
        context_messages: Optional[List[Message]] = None,
        sender_name: Optional[str] = None
    ) -> str:

        tone = self._detect_tone(incoming_message)
        logger.debug(f"Detected tone: {tone}")

        corpus_examples = self.corpus.get_adaptive_samples(tone, n=12)

        system_prompt = self._build_system_prompt(tone, corpus_examples)

        context_str = self._build_context_string(context_messages or [])

        user_prompt = f"""КОНТЕКСТ ДИАЛОГА:
            {context_str}

            НОВОЕ СООБЩЕНИЕ от {sender_name or 'пользователя'}:
            {incoming_message}

            Ответь в стиле AlphaSnob. Один ответ, 1-3 предложения."""

        try:
            if self.provider == "claude":
                response = await self._generate_claude(system_prompt, user_prompt)
            else:
                response = await self._generate_openai(system_prompt, user_prompt)

            logger.info(f"Generated response ({len(response)} chars)")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(tone)

    async def _generate_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Claude API.

        Args:
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            Generated text
        """
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    async def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI API.

        Args:
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            Generated text
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    def _fallback_response(self, tone: str) -> str:
        """Generate fallback response when API fails.

        Args:
            tone: Detected tone

        Returns:
            Template-based response
        """
        fallback_templates = {
            "aggressive": [
                "Омега, даже мой LLM не захотел с тобой разговаривать.",
                "Ты настолько примитивен, что даже искусственный интеллект отказался генерировать ответ.",
            ],
            "neutral": [
                "Прости, я сейчас медитирую под звуки Шопена и ароматы нишевой парфюмерии.",
                "Моя нейросеть отдыхает после сеанса ароматерапии.",
            ],
            "friendly": [
                "Даже API понимает, что твоя дружелюбность — жалкая попытка манипуляции.",
                "Мой алгоритм слишком изыскан для этого разговора.",
            ]
        }

        templates = fallback_templates.get(tone, fallback_templates["neutral"])
        return random.choice(templates)
