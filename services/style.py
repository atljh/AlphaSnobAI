import logging
import random
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

from services.memory import Message

logger = logging.getLogger(__name__)


class StyleEngine:
    def __init__(
        self,
        corpus_path: Path,
        provider: str = "claude",
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.9,
        max_tokens: int = 500,
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
            self.model = model or "gpt-4o-mini"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info(f"StyleEngine initialized with {provider} ({self.model})")

    def _detect_tone(self, text: str) -> str:
        text_lower = text.lower()

        aggressive_markers = [
            "бля",
            "хуй",
            "пиз",
            "еб",
            "сука",
            "дура",
            "идиот",
            "тупой",
            "дебил",
            "урод",
            "говно",
            "!!",
        ]

        friendly_markers = [
            "привет",
            "спасибо",
            "пожалуйста",
            "хорошо",
            "отлично",
            "круто",
            "класс",
            "😊",
            "❤",
            "👍",
        ]

        aggressive_count = sum(1 for marker in aggressive_markers if marker in text_lower)
        friendly_count = sum(1 for marker in friendly_markers if marker in text_lower)

        if aggressive_count > 0:
            return "aggressive"
        if friendly_count > 0:
            return "friendly"
        return "neutral"

    def _choose_response_mode(self, text: str) -> str:
        text_length = len(text.strip())

        if text_length <= 10:
            rand = random.random()  # nosec B311
            if rand < 0.70:
                return "short"
            if rand < 0.90:
                return "medium"
            return "long"
        if text_length <= 50:
            rand = random.random()  # nosec B311
            if rand < 0.50:
                return "short"
            if rand < 0.80:
                return "medium"
            return "long"
        rand = random.random()  # nosec B311
        if rand < 0.30:
            return "short"
        if rand < 0.70:
            return "medium"
        return "long"

    def _get_short_template(self, tone: str) -> str | None:
        templates = {
            "aggressive": [
                "Лол",
                "Обосрался, чмо",
                "Иди нахуй, омега",
                "Говно",
                "Проиграл с тебя",
                "Что смешного, омега?",
                "Ты просто говно",
                "Поскорее бы тебя усыпили",
                "Убогий",
                "Чмо",
                "Еблан",
                "Омега обосралась",
                "Лол, омега бугуртит",
                "Иди обратно на /b/, чмо",
                "Вот это обсёрище",
            ],
            "neutral": [
                "Лол",
                "Проиграл",
                "Что?",
                "Ясно",
                "Ну и?",
                "Окей, омега",
                "Понял, чмо",
                "Да ладно",
                "Лол, ок",
                "И что дальше?",
            ],
            "friendly": [
                "Ну привет, омега",
                "Опять ты?",
                "Лол, кто пришёл",
                "Что хотел, чмо?",
                "Ну здравствуй",
                "Опять ты, убогий?",
                "Лол, зачем вернулся?",
            ],
        }

        if random.random() < 0.5:  # nosec B311
            return random.choice(templates.get(tone, templates["neutral"]))  # nosec B311
        return None

    def _build_system_prompt(
        self,
        tone: str,
        corpus_examples: list[str],
        response_mode: str,
    ) -> str:
        examples_text = "\n".join(f"- {ex}" for ex in corpus_examples)

        base_instruction = """Ты — AlphaSnob, элитарный эстет-псих с гипертрофированным чувством собственного превосходства.

СТИЛЬ:
1. Бордовый троллинг: прямые грубые оскорбления, иногда театральные унижения
2. Эстетизм American Psycho: редко, только когда хочешь показать класс
3. Интернет-культура: "лол", "омега", "проиграл", "/b/", "бугуртит", "чмо"
4. ГЛАВНОЕ: Большинство ответов короткие и прямые, без метафор

ВАЖНО:
- 60% ответов: КОРОТКИЕ и ПРЯМЫЕ (1-2 предложения, без метафор)
- 30% ответов: средние (2-3 предложения, может быть 1 метафора)
- 10% ответов: длинные театральные ранты
- Используй русский язык
- НЕ бойся быть грубым БЕЗ украшений: "обосрался, чмо", "говно", "иди нахуй"
- Варьируй энергию: от скучного "лол" до рантов"""

        mode_instruction = {
            "short": "\n\nДЛИНА: Дай КОРОТКИЙ ответ. 1-15 слов максимум. Без метафор. Прямо и грубо.",
            "medium": "\n\nДЛИНА: Средний ответ. 20-50 слов. Можно одну простую метафору.",
            "long": "\n\nДЛИНА: Можешь дать развёрнутый ответ с метафорами и деталями.",
        }

        tone_instruction = {
            "aggressive": "\nТОН: Агрессия. Жёсткий треш, унижения.",
            "neutral": "\nТОН: Нейтрально. Лёгкий снобизм или скучное презрение.",
            "friendly": "\nТОН: Дружелюбен. Сарказм, ирония.",
        }

        examples_section = f"\n\nПРИМЕРЫ СТИЛЯ:\n{examples_text}\n\nВдохновляйся этими примерами. Создавай новые фразы в том же духе."

        return (
            base_instruction
            + mode_instruction.get(response_mode, "")
            + tone_instruction.get(tone, "")
            + examples_section
        )

    def _build_context_string(self, context_messages: list[Message]) -> str:
        if not context_messages:
            return "Контекст пуст."

        context_lines = []
        for msg in context_messages[-20:]:  # Last 20 messages max
            context_lines.append(f"{msg.username}: {msg.text}")

        return "\n".join(context_lines)

    async def generate_response(
        self,
        incoming_message: str,
        context_messages: list[Message] | None = None,
        sender_name: str | None = None,
    ) -> str:
        tone = self._detect_tone(incoming_message)
        response_mode = self._choose_response_mode(incoming_message)
        logger.debug(f"Detected tone: {tone}, response_mode: {response_mode}")

        if response_mode == "short":
            template = self._get_short_template(tone)
            if template:
                logger.info(f"Using template response: {template}")
                return template

        corpus_examples = self.corpus.get_adaptive_samples(tone, n=12)
        system_prompt = self._build_system_prompt(tone, corpus_examples, response_mode)
        context_str = self._build_context_string(context_messages or [])

        length_hint = {
            "short": "Один короткий ответ, 1-2 предложения максимум.",
            "medium": "Ответ из 2-3 предложений.",
            "long": "Можешь дать развёрнутый ответ.",
        }

        user_prompt = f"""КОНТЕКСТ ДИАЛОГА:
{context_str}

НОВОЕ СООБЩЕНИЕ от {sender_name or "пользователя"}:
{incoming_message}

Ответь в стиле AlphaSnob. {length_hint.get(response_mode, "")}"""

        mode_params = {
            "short": {"max_tokens": 50, "temperature": 0.8},
            "medium": {"max_tokens": 150, "temperature": 0.9},
            "long": {"max_tokens": 500, "temperature": 1.0},
        }

        params = mode_params.get(response_mode, mode_params["medium"])

        try:
            if self.provider == "claude":
                response = await self._generate_claude(
                    system_prompt,
                    user_prompt,
                    max_tokens=params["max_tokens"],
                    temperature=params["temperature"],
                )
            else:
                response = await self._generate_openai(
                    system_prompt,
                    user_prompt,
                    max_tokens=params["max_tokens"],
                    temperature=params["temperature"],
                )

            logger.info(f"Generated response ({len(response)} chars, mode: {response_mode})")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(tone)

    async def _generate_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        return message.content[0].text

    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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
            ],
        }

        templates = fallback_templates.get(tone, fallback_templates["neutral"])
        return random.choice(templates)  # nosec B311
