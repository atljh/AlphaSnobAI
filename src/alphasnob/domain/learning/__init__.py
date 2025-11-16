"""Learning domain - Owner style learning and mimicry."""

from alphasnob.domain.learning.entities.style_analysis import StyleAnalysis
from alphasnob.domain.learning.entities.style_sample import StyleSample
from alphasnob.domain.learning.value_objects.formality_score import FormalityScore

__all__ = [
    "StyleSample",
    "StyleAnalysis",
    "FormalityScore",
]
