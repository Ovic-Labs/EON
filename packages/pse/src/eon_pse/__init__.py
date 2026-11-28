"""Offline personality and delivery policy for the OVIC EON SDK."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated, Literal

from eon_ere import ResponsePlan, ResponseStrategy
from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["DeliveryPlan", "PersonalityEngine", "PersonalityProfile"]

_Formality = Literal["professional", "conversational", "formal"]
_Pace = Literal["measured", "standard"]
_Warmth = Literal["reserved", "steady", "warm"]
_ProfileId = Annotated[str, Field(min_length=1, max_length=48, pattern=r"^[a-z][a-z0-9_-]*$")]


class PersonalityProfile(BaseModel):
    """A host-approved set of bounded style controls."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: _ProfileId
    revision: int = Field(default=1, ge=1, strict=True)
    formality: _Formality = "professional"
    pace: _Pace = "standard"
    supportive_warmth: _Warmth = "steady"
    concise_sentence_limit: int = Field(default=2, ge=1, le=4, strict=True)
    detailed_sentence_limit: int = Field(default=6, ge=1, le=12, strict=True)

    @model_validator(mode="after")
    def _validate_limits(self) -> PersonalityProfile:
        if self.detailed_sentence_limit < self.concise_sentence_limit:
            raise ValueError("Detailed sentence limit cannot be below the concise limit.")
        return self


class DeliveryPlan(BaseModel):
    """Versioned style contract consumed alongside the original ERE plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    profile_id: _ProfileId
    profile_revision: int = Field(ge=1, strict=True)
    strategy: ResponseStrategy
    mode: Literal["respond", "pause"]
    tone: Literal["neutral", "supportive"]
    reply_style: Literal["concise", "detailed"]
    formality: _Formality
    pace: _Pace
    warmth: _Warmth
    sentence_limit: int = Field(ge=0, le=12)
    acknowledge_reported_need: bool
    offer_check_in: bool

    @model_validator(mode="after")
    def _validate_delivery(self) -> DeliveryPlan:
        paused = self.strategy == ResponseStrategy.GIVE_SPACE
        if paused != (self.mode == "pause"):
            raise ValueError("Delivery mode must respect the response strategy.")
        if paused:
            if self.sentence_limit or self.offer_check_in or self.acknowledge_reported_need:
                raise ValueError("A pause cannot schedule speech or a check-in.")
        elif not self.sentence_limit:
            raise ValueError("Active delivery requires a positive sentence limit.")
        if self.tone == "neutral" and self.warmth != "reserved":
            raise ValueError("Neutral tone requires reserved warmth.")
        return self


_BUILT_INS = (
    PersonalityProfile(profile_id="professional"),
    PersonalityProfile(
        profile_id="friendly",
        formality="conversational",
        supportive_warmth="warm",
    ),
    PersonalityProfile(
        profile_id="formal",
        formality="formal",
        pace="measured",
        supportive_warmth="reserved",
    ),
)


class PersonalityEngine:
    """Apply an approved style profile without changing the interaction strategy."""

    def __init__(
        self,
        *,
        profiles: Iterable[PersonalityProfile] = (),
        default_profile: str = "professional",
    ) -> None:
        self._profiles = {profile.profile_id: profile for profile in _BUILT_INS}
        for profile in profiles:
            if not isinstance(profile, PersonalityProfile):
                raise TypeError("Custom profiles must be validated PersonalityProfile instances.")
            if profile.profile_id in self._profiles:
                raise ValueError(f"Duplicate personality profile ID: {profile.profile_id}")
            self._profiles[profile.profile_id] = profile
        self._get_profile(default_profile)
        self._default_profile = default_profile

    def _get_profile(self, profile_id: str) -> PersonalityProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ValueError(f"Unknown personality profile: {profile_id}") from exc

    def list_profiles(self) -> tuple[PersonalityProfile, ...]:
        """List the validated profiles that the host can select."""
        return tuple(self._profiles.values())

    def style(self, response: ResponsePlan, *, profile_id: str | None = None) -> DeliveryPlan:
        """Translate a trusted ERE response plan into bounded delivery guidance."""
        if not isinstance(response, ResponsePlan):
            raise TypeError("Expected an ERE ResponsePlan.")
        profile = self._get_profile(self._default_profile if profile_id is None else profile_id)
        paused = response.strategy == ResponseStrategy.GIVE_SPACE
        sentence_limit = (
            profile.concise_sentence_limit
            if response.reply_style == "concise"
            else profile.detailed_sentence_limit
        )
        return DeliveryPlan(
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            strategy=response.strategy,
            mode="pause" if paused else "respond",
            tone=response.tone,
            reply_style=response.reply_style,
            formality=profile.formality,
            pace=profile.pace,
            warmth=profile.supportive_warmth if response.tone == "supportive" else "reserved",
            sentence_limit=0 if paused else sentence_limit,
            acknowledge_reported_need=response.acknowledge_reported_need and not paused,
            offer_check_in=response.offer_check_in and not paused,
        )
