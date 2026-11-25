"""Liveness and validated-inference readiness probes for OVIC EON ERS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from eon_ers.engine import ERSEngine


def get_liveness_status(engine: ERSEngine) -> dict[str, Any]:
    """Return process/engine liveness distinct from validated-model readiness."""
    core_health = engine.event_bus.check_health()
    return {
        "component": "eon.ers",
        "status": "HEALTHY" if engine.is_running else "DEGRADED",
        "state": engine.state.value,
        "is_running": engine.is_running,
        "core_integration_status": core_health["status"],
        "missing_dependencies": core_health["missing_dependencies"],
        "failure_reason": engine.lifecycle.failure_reason,
    }


def get_readiness_status(engine: ERSEngine) -> dict[str, Any]:
    """Report server readiness while separating infrastructure liveness from model qualification."""
    model_checks: dict[str, dict[str, Any]] = {}
    validated_count = 0

    for name, pipeline in (
        ("facial", getattr(engine, "_facial_pipeline", None)),
        ("speech", getattr(engine, "_speech_pipeline", None)),
        ("text", getattr(engine, "_text_pipeline", None)),
    ):
        adapter = getattr(pipeline, "model_adapter", None) if pipeline else None
        if adapter is None:
            continue
        is_val = bool(getattr(adapter, "is_validated", False))
        if is_val:
            validated_count += 1
        state = getattr(adapter, "model_state", None)
        model_checks[name] = {
            "model_id": getattr(adapter, "model_id", "unknown"),
            "available": bool(getattr(adapter, "is_available", False)),
            "is_validated": is_val,
            "state": state.value if state is not None else "UNKNOWN",
        }

    # Infrastructure can serve requests once running, but qualified_inference_ready requires >= 1 validated model
    return {
        "ready": engine.is_running,
        "qualified_inference_ready": engine.is_running and validated_count > 0,
        "validated_model_count": validated_count,
        "engine_state": engine.state.value,
        "models": model_checks,
        "note": (
            "Ready for empirically validated classification."
            if engine.is_running and validated_count > 0
            else "Service operational on unvalidated baseline/diagnostic models only; empirical benchmark qualification pending."
        ),
    }
