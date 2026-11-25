"""Deterministic Unicode-safe tokenization and feature encoding for CPU text affect models."""

from __future__ import annotations

import hashlib
import re

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class TextTokenizationResult(BaseModel):
    """Tokenized representation and fixed-size numerical feature vector."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    tokens: list[str] = Field(default_factory=list)
    token_count: int = Field(default=0, ge=0)
    lexical_cues: dict[str, float] = Field(default_factory=dict)
    feature_dim: int = Field(default=64, ge=8)


class TextTokenizer:
    """Unicode-aware word & punctuation tokenizer computing deterministic hashed feature vectors."""

    _TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)

    _POSITIVE_CUES: frozenset[str] = frozenset(
        {"happy", "joy", "glad", "love", "great", "wonderful", "excited", "smile", "thank", "good"}
    )
    _SAD_CUES: frozenset[str] = frozenset(
        {"sad", "unhappy", "cry", "grief", "lonely", "sorry", "hurt", "loss", "down", "miss"}
    )
    _ANGER_CUES: frozenset[str] = frozenset(
        {"angry", "mad", "furious", "annoyed", "hate", "rage", "frustrated", "unfair"}
    )
    _FEAR_CUES: frozenset[str] = frozenset(
        {"afraid", "scared", "fear", "anxious", "worried", "nervous", "terrified", "panic"}
    )
    _SURPRISE_CUES: frozenset[str] = frozenset(
        {"surprised", "amazed", "shocked", "wow", "unexpected", "unbelievable"}
    )
    _DISGUST_CUES: frozenset[str] = frozenset(
        {"disgusted", "gross", "nasty", "revolting", "awful", "horrible", "sickening"}
    )

    def __init__(self, feature_dim: int = 64) -> None:
        self.feature_dim = feature_dim

    def tokenize(self, text: str) -> tuple[TextTokenizationResult, np.ndarray]:
        """Tokenize normalized text and return (metadata, L2-normalized float32 feature vector)."""
        raw_tokens = self._TOKEN_RE.findall(text.lower())
        vec = np.zeros((1, self.feature_dim), dtype=np.float32)

        for tok in raw_tokens:
            digest = hashlib.blake2b(tok.encode("utf-8"), digest_size=4).digest()
            idx = int.from_bytes(digest, "little") % self.feature_dim
            vec[0, idx] += 1.0

        norm = float(np.linalg.norm(vec))
        if norm > 1e-8:
            vec /= norm

        tok_set = set(raw_tokens)
        n_tok = max(1, len(raw_tokens))
        cues = {
            "cue_happiness_density": round(len(tok_set & self._POSITIVE_CUES) / n_tok, 4),
            "cue_sadness_density": round(len(tok_set & self._SAD_CUES) / n_tok, 4),
            "cue_anger_density": round(len(tok_set & self._ANGER_CUES) / n_tok, 4),
            "cue_fear_density": round(len(tok_set & self._FEAR_CUES) / n_tok, 4),
            "cue_surprise_density": round(len(tok_set & self._SURPRISE_CUES) / n_tok, 4),
            "cue_disgust_density": round(len(tok_set & self._DISGUST_CUES) / n_tok, 4),
            "token_count": float(len(raw_tokens)),
        }
        return (
            TextTokenizationResult(
                tokens=raw_tokens[:128],
                token_count=len(raw_tokens),
                lexical_cues=cues,
                feature_dim=self.feature_dim,
            ),
            vec,
        )
