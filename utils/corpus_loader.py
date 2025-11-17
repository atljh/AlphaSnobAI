import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)


class CorpusLoader:
    def __init__(self, corpus_path: Path):
        self.corpus_path = corpus_path
        self.raw_text = ""
        self.lines: list[str] = []
        self.categorized: dict[str, list[str]] = {
            "trash": [],
            "aesthetic": [],
            "hyperbole": [],
            "threats": [],
            "general": [],
        }
        self._load_corpus()

    def _load_corpus(self):
        if not self.corpus_path.exists():
            logger.warning(f"Corpus file not found at {self.corpus_path}")
            return

        try:
            with open(self.corpus_path, encoding="utf-8", errors="ignore") as f:
                self.raw_text = f.read()

            self.lines = [line.strip() for line in self.raw_text.split("\n") if line.strip()]

            logger.info(f"Loaded {len(self.lines)} lines from corpus")

            self._categorize_lines()

        except Exception as e:
            logger.error(f"Error loading corpus: {e}")

    def _categorize_lines(self):
        trash_markers = ["омега", "дырявый", "обиженка", "выжатый", "портвешок", "урод", "тупой"]
        aesthetic_markers = [
            "уход",
            "аромат",
            "косметик",
            "богатств",
            "роскош",
            "нарцисс",
            "элегант",
            "вкус",
        ]
        hyperbole_markers = ["разорву", "уничтож", "бог", "царств", "миллион", "бесконечн"]
        threat_markers = ["убью", "сломаю", "разорву", "уничтож", "размаж", "раздав"]

        for line in self.lines:
            line_lower = line.lower()
            categorized = False

            if any(marker in line_lower for marker in trash_markers):
                self.categorized["trash"].append(line)
                categorized = True

            if any(marker in line_lower for marker in aesthetic_markers):
                self.categorized["aesthetic"].append(line)
                categorized = True

            if any(marker in line_lower for marker in hyperbole_markers):
                self.categorized["hyperbole"].append(line)
                categorized = True

            if any(marker in line_lower for marker in threat_markers):
                self.categorized["threats"].append(line)
                categorized = True

            if not categorized:
                self.categorized["general"].append(line)

        for category, lines in self.categorized.items():
            logger.info(f"Category '{category}': {len(lines)} lines")

    def get_random_samples(self, n: int = 10, category: str = None) -> list[str]:
        if category and category in self.categorized:
            source = self.categorized[category]
        else:
            source = self.lines

        if not source:
            return []

        k = min(n, len(source))
        return random.sample(source, k)  # nosec B311

    def get_mixed_samples(self, n: int = 10, weights: dict[str, float] = None) -> list[str]:
        if weights is None:
            weights = {
                "trash": 0.3,
                "aesthetic": 0.25,
                "hyperbole": 0.2,
                "threats": 0.15,
                "general": 0.1,
            }

        samples = []
        for category, weight in weights.items():
            count = int(n * weight)
            if count > 0 and category in self.categorized:
                category_samples = self.get_random_samples(count, category)
                samples.extend(category_samples)

        random.shuffle(samples)  # nosec B311

        return samples[:n]

    def get_adaptive_samples(self, tone: str, n: int = 10) -> list[str]:
        """Get samples adapted to the detected tone.

        Args:
            tone: Detected tone ("aggressive", "neutral", "friendly")
            n: Number of samples

        Returns:
            List of samples matching the tone
        """
        if tone == "aggressive":
            # More trash and threats
            weights = {"trash": 0.5, "threats": 0.3, "hyperbole": 0.2}
        elif tone == "neutral":
            # More aesthetic and general
            weights = {"aesthetic": 0.4, "hyperbole": 0.3, "general": 0.3}
        else:  # friendly
            # Sarcasm: aesthetic + light trash
            weights = {"aesthetic": 0.5, "trash": 0.3, "general": 0.2}

        return self.get_mixed_samples(n, weights)

    def get_full_corpus_text(self, max_chars: int = None) -> str:
        if max_chars and len(self.raw_text) > max_chars:
            return self.raw_text[:max_chars]
        return self.raw_text
