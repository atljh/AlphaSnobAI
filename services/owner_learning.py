import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class OwnerStyleAnalysis:
    total_messages: int
    avg_message_length: float
    avg_sentence_length: float
    emoji_frequency: float
    common_emojis: list[str]
    common_words: list[str]
    common_phrases: list[str]
    punctuation_patterns: dict[str, int]
    formality_score: float
    language_distribution: dict[str, float]

    def __repr__(self):
        return f"OwnerStyleAnalysis(messages={self.total_messages}, avg_len={self.avg_message_length:.1f})"


class OwnerLearningSystem:
    def __init__(self, manual_samples_path: Path, min_samples: int = 50):
        self.manual_samples_path = manual_samples_path
        self.min_samples = min_samples
        self.samples: list[str] = []
        self.analysis: OwnerStyleAnalysis | None = None

        self._load_samples()
        if len(self.samples) >= self.min_samples:
            self._analyze_style()

    def _load_samples(self):
        if not self.manual_samples_path.exists():
            logger.warning(f"Owner samples file not found: {self.manual_samples_path}")
            return

        try:
            with open(self.manual_samples_path, encoding="utf-8") as f:
                lines = f.readlines()

            self.samples = [
                line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
            ]

            logger.info(f"Loaded {len(self.samples)} owner message samples")

            if len(self.samples) < self.min_samples:
                logger.warning(
                    f"Only {len(self.samples)} samples found, need {self.min_samples} for good learning. "
                    f"Owner mode will use conservative style.",
                )
        except Exception as e:
            logger.error(f"Error loading owner samples: {e}")

    def _analyze_style(self):
        if not self.samples:
            return

        total_messages = len(self.samples)
        total_chars = sum(len(msg) for msg in self.samples)
        avg_message_length = total_chars / total_messages if total_messages > 0 else 0

        all_sentences = []
        for msg in self.samples:
            sentences = re.split(r"[.!?]+", msg)
            all_sentences.extend([s.strip() for s in sentences if s.strip()])

        avg_sentence_length = (
            sum(len(s.split()) for s in all_sentences) / len(all_sentences) if all_sentences else 0
        )

        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )

        all_emojis = []
        for msg in self.samples:
            emojis = emoji_pattern.findall(msg)
            all_emojis.extend(emojis)

        emoji_frequency = len(all_emojis) / total_messages if total_messages > 0 else 0
        emoji_counter = Counter(all_emojis)
        common_emojis = [emoji for emoji, _ in emoji_counter.most_common(10)]

        all_words = []
        for msg in self.samples:
            words = re.findall(r"\b\w+\b", msg.lower())
            all_words.extend(words)

        stop_words = {
            "и",
            "в",
            "на",
            "с",
            "по",
            "для",
            "не",
            "а",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
        }
        filtered_words = [w for w in all_words if w not in stop_words and len(w) > 2]

        word_counter = Counter(filtered_words)
        common_words = [word for word, _ in word_counter.most_common(20)]

        bigrams = []
        for msg in self.samples:
            words = msg.split()
            for i in range(len(words) - 1):
                bigrams.append(f"{words[i]} {words[i + 1]}")

        bigram_counter = Counter(bigrams)
        common_phrases = [phrase for phrase, _ in bigram_counter.most_common(10)]

        punctuation_patterns = {
            "exclamation_single": sum(
                msg.count("!") for msg in self.samples if msg.count("!") == 1
            ),
            "exclamation_multiple": sum(1 for msg in self.samples if msg.count("!") > 1),
            "question": sum(msg.count("?") for msg in self.samples),
            "ellipsis": sum(msg.count("...") for msg in self.samples),
            "caps_usage": sum(1 for msg in self.samples if any(c.isupper() for c in msg)),
        }

        formal_markers = ["please", "thank you", "пожалуйста", "спасибо", "would you", "could you"]
        casual_markers = ["lol", "лол", "yeah", "да", "nah", "нет", "ok", "ок"]

        formal_count = sum(
            1 for msg in self.samples for marker in formal_markers if marker in msg.lower()
        )

        casual_count = sum(
            1 for msg in self.samples for marker in casual_markers if marker in msg.lower()
        )

        formality_score = (
            formal_count / (formal_count + casual_count)
            if (formal_count + casual_count) > 0
            else 0.5
        )

        russian_chars = sum(1 for msg in self.samples for c in msg if "\u0400" <= c <= "\u04ff")
        english_chars = sum(1 for msg in self.samples for c in msg if c.isalpha() and ord(c) < 128)
        total_alpha = russian_chars + english_chars

        if total_alpha > 0:
            language_distribution = {
                "ru": russian_chars / total_alpha,
                "en": english_chars / total_alpha,
            }
        else:
            language_distribution = {"ru": 0.5, "en": 0.5}

        self.analysis = OwnerStyleAnalysis(
            total_messages=total_messages,
            avg_message_length=avg_message_length,
            avg_sentence_length=avg_sentence_length,
            emoji_frequency=emoji_frequency,
            common_emojis=common_emojis,
            common_words=common_words,
            common_phrases=common_phrases,
            punctuation_patterns=punctuation_patterns,
            formality_score=formality_score,
            language_distribution=language_distribution,
        )

        logger.info(f"Owner style analysis complete: {self.analysis}")

    def get_samples(self, n: int = 20) -> list[str]:
        import random

        if not self.samples:
            return []

        return random.sample(self.samples, min(n, len(self.samples)))  # nosec B311

    def get_analysis(self) -> OwnerStyleAnalysis | None:
        return self.analysis

    def has_sufficient_samples(self) -> bool:
        return len(self.samples) >= self.min_samples

    def get_style_description(self) -> str:
        if not self.analysis:
            return "No style analysis available (insufficient samples)"

        desc = f"""Owner Style Profile:
- Messages analyzed: {self.analysis.total_messages}
- Average message length: {self.analysis.avg_message_length:.1f} characters
- Average sentence length: {self.analysis.avg_sentence_length:.1f} words
- Emoji frequency: {self.analysis.emoji_frequency:.2f} per message
- Common emojis: {", ".join(self.analysis.common_emojis[:5])}
- Formality: {"Formal" if self.analysis.formality_score > 0.6 else "Casual" if self.analysis.formality_score < 0.4 else "Mixed"}
- Language: {max(self.analysis.language_distribution.items(), key=lambda x: x[1])[0].upper()} dominant
"""
        return desc

    def generate_style_instructions(self) -> str:
        if not self.analysis:
            return "Use conservative, neutral style (insufficient samples for learning)"

        instructions = []

        if self.analysis.avg_message_length < 50:
            instructions.append("Keep messages SHORT (under 50 characters typically)")
        elif self.analysis.avg_message_length < 150:
            instructions.append("Use MEDIUM length messages (50-150 characters)")
        else:
            instructions.append("Owner writes LONG messages (150+ characters)")

        if self.analysis.emoji_frequency > 0.5:
            instructions.append(
                f"Use emojis FREQUENTLY (especially: {', '.join(self.analysis.common_emojis[:3])})",
            )
        elif self.analysis.emoji_frequency > 0.2:
            instructions.append(
                f"Use emojis occasionally: {', '.join(self.analysis.common_emojis[:3])}",
            )
        else:
            instructions.append("Rarely use emojis")

        if self.analysis.formality_score > 0.6:
            instructions.append("Maintain FORMAL tone")
        elif self.analysis.formality_score < 0.4:
            instructions.append("Use CASUAL, informal language")
        else:
            instructions.append("Mix formal and casual tone")

        if self.analysis.punctuation_patterns.get("exclamation_multiple", 0) > 5:
            instructions.append("Use multiple exclamation marks!!! for emphasis")

        if self.analysis.punctuation_patterns.get("ellipsis", 0) > 5:
            instructions.append("Use ellipsis... for pauses")

        if self.analysis.common_words:
            instructions.append(
                f"Common words to use: {', '.join(self.analysis.common_words[:10])}",
            )

        primary_lang = max(self.analysis.language_distribution.items(), key=lambda x: x[1])
        if primary_lang[1] > 0.8:
            instructions.append(f"Primarily use {primary_lang[0].upper()}")
        else:
            instructions.append("Mix Russian and English naturally")

        return "\n".join(f"- {inst}" for inst in instructions)
