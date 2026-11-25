"""Responsible-AI and model-qualification safety policies for ERS."""

from __future__ import annotations

from eon_ers.exceptions import ERSSafetyViolationError
from eon_ers.types import ModelQualificationState, ModelState

ACTIVATABLE_MODEL_STATES: frozenset[ModelState] = frozenset(
    {
        ModelState.MODEL_LOADED_VALIDATED,
    }
)


def assert_epistemic_modesty(is_definitive_claim: bool) -> None:
    """Enforce that emotion estimates never assert ground-truth subjective claims."""
    if is_definitive_claim:
        raise ERSSafetyViolationError(
            "Epistemic modesty invariant violated: is_definitive_claim must remain False."
        )


def ensure_model_activation_allowed(
    model_id: str,
    model_state: ModelState | ModelQualificationState,
    is_validated: bool,
) -> None:
    """Prevent promoting unvalidated, rejected, or revoked models into production classification."""
    allowed = model_state in ACTIVATABLE_MODEL_STATES or (
        model_state == ModelQualificationState.MODEL_VALIDATED
    )
    if not is_validated or not allowed:
        raise ERSSafetyViolationError(
            f"Model '{model_id}' cannot be activated for qualified inference "
            f"(state={model_state.value}, is_validated={is_validated}).",
            context={"model_id": model_id, "state": model_state.value},
        )
