"""Emotion estimate data contracts adhering to responsible AI principles."""

from enum import Enum
from typing import Annotated

from pydantic import Field, field_validator

from eon.schemas.base import EonBaseModel
from eon.schemas.common import ConfidenceScore, UncertaintyScore
from eon.schemas.identifiers import EventId, generate_event_id

# Bounded dimensional affective values
ValenceScore = Annotated[
    float,
    Field(
        ge=-1.0,
        le=1.0,
        description="Pleasure-displeasure dimensional coordinate bounded in [-1.0, +1.0].",
    ),
]

ArousalScore = Annotated[
    float,
    Field(
        ge=-1.0,
        le=1.0,
        description="Activation-deactivation coordinate bounded in [-1.0, +1.0].",
    ),
]

DominanceScore = Annotated[
    float,
    Field(
        ge=-1.0,
        le=1.0,
        description="Control-submission dimensional coordinate bounded in [-1.0, +1.0].",
    ),
]


class PrimaryEmotionCategory(str, Enum):
    """Categorical emotion descriptors used for social interaction modeling."""

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    ENGAGED = "engaged"
    DISTRACTED = "distracted"


class DiscreteEmotionScore(EonBaseModel):
    """Individual categorical emotion estimate with associated probability."""

    category: PrimaryEmotionCategory = Field(
        ...,
        description="Categorical emotion label.",
    )
    probability: ConfidenceScore = Field(
        ...,
        description="Estimated probability or activation strength in [0.0, 1.0].",
    )


class EmotionEstimatePayload(EonBaseModel):
    """Contract representing an automated emotion estimate.

    CRITICAL RESPONSIBLE AI REQUIREMENT:
    Emotion outputs are algorithmic ESTIMATES derived from behavioral and
    physiological features. They are not medical, psychiatric, or established
    factual determinations of a human's internal subjective state.
    """

    estimate_id: EventId = Field(
        default_factory=generate_event_id,
        description="Unique UUID4 identifier for this emotion estimate.",
    )
    source_observation_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of upstream observation UUIDs providing evidence for this estimate.",
    )
    valence: ValenceScore = Field(
        ...,
        description="Dimensional valence score in [-1.0, 1.0]. Missing value not coerced to 0.",
    )
    arousal: ArousalScore = Field(
        ...,
        description="Dimensional arousal score in [-1.0, 1.0]. Missing value not coerced to 0.",
    )
    dominance: DominanceScore | None = Field(
        default=None,
        description="Optional dimensional dominance score in [-1.0, 1.0].",
    )
    primary_category: PrimaryEmotionCategory = Field(
        ...,
        description="Primary categorical classification based on model inferences.",
    )
    confidence: ConfidenceScore = Field(
        ...,
        description="Statistical confidence score within [0.0, 1.0].",
    )
    uncertainty: UncertaintyScore = Field(
        ...,
        description="Epistemic/aleatoric uncertainty score within [0.0, 1.0].",
    )
    discrete_scores: list[DiscreteEmotionScore] = Field(
        default_factory=list,
        description="Distribution of discrete emotion probabilities across categories.",
    )
    model_metadata: dict[str, str] | None = Field(
        default=None,
        description="Model identifier, weights checksum, or calibration profile version.",
    )
    disclaimer: str = Field(
        default="Automated affective estimation; not a certified psychological diagnosis.",
        description="Non-negotiable ethical disclaimer embedded in all emotion estimate payloads.",
    )

    @field_validator("disclaimer")
    @classmethod
    def validate_disclaimer_preserved(cls, value: str) -> str:
        """Enforce that the ethical disclaimer is never stripped or emptied."""
        if not value or len(value.strip()) < 10:
            raise ValueError(
                "Ethical disclaimer must be preserved on all emotion estimate payloads."
            )
        return value
