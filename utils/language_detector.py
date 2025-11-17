import logging
import re

logger = logging.getLogger(__name__)


class LanguageDetector:
    def __init__(self, supported_languages: list = None, default_language: str = "ru"):
        self.supported_languages = supported_languages or ["ru", "en"]
        self.default_language = default_language

        self.russian_chars = re.compile(r"[а-яА-ЯёЁ]")
        self.english_chars = re.compile(r"[a-zA-Z]")

        self.russian_common_words = {
            "привет",
            "пока",
            "спасибо",
            "да",
            "нет",
            "как",
            "что",
            "это",
            "быть",
            "мой",
            "твой",
            "его",
            "она",
            "они",
            "мы",
            "вы",
            "хорошо",
            "плохо",
            "здравствуй",
            "до",
            "свидания",
            "можно",
            "нужно",
            "хочу",
            "могу",
            "буду",
            "был",
            "была",
            "были",
        }

        self.english_common_words = {
            "hello",
            "hi",
            "bye",
            "goodbye",
            "thanks",
            "thank",
            "yes",
            "no",
            "what",
            "how",
            "why",
            "when",
            "where",
            "this",
            "that",
            "is",
            "are",
            "was",
            "were",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "can",
            "could",
            "will",
            "would",
            "should",
            "may",
            "might",
            "must",
        }

    def detect(self, text: str) -> str:
        if not text or not text.strip():
            return self.default_language

        text_lower = text.lower()

        russian_chars_count = len(self.russian_chars.findall(text))
        english_chars_count = len(self.english_chars.findall(text))

        total_chars = russian_chars_count + english_chars_count

        if total_chars == 0:
            words = text_lower.split()
            return self._detect_by_words(words)

        russian_ratio = russian_chars_count / total_chars if total_chars > 0 else 0
        english_ratio = english_chars_count / total_chars if total_chars > 0 else 0

        if russian_ratio > 0.3:
            return "ru"
        if english_ratio > 0.3:
            return "en"

        words = text_lower.split()
        return self._detect_by_words(words)

    def _detect_by_words(self, words: list) -> str:
        russian_word_count = sum(1 for word in words if word in self.russian_common_words)
        english_word_count = sum(1 for word in words if word in self.english_common_words)

        if russian_word_count > english_word_count:
            return "ru"
        if english_word_count > russian_word_count:
            return "en"

        return self.default_language

    def get_language_name(self, code: str) -> str:
        lang_names = {
            "ru": "Russian",
            "en": "English",
        }
        return lang_names.get(code, code.upper())

    def is_supported(self, language_code: str) -> bool:
        return language_code in self.supported_languages


def detect_language(text: str, supported: list | None = None, default: str = "ru") -> str:
    detector = LanguageDetector(supported, default)
    return detector.detect(text)
