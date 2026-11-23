"""Unit tests for component health, status, and diagnostic schemas."""

from eon.schemas.health import (
    ComponentHealthPayload,
    ComponentStatus,
    HealthState,
)


def test_valid_component_health_report() -> None:
    """AC-1.2-10: Verify valid component health heartbeat construction."""
    health = ComponentHealthPayload(
        component_id="eon.ers",
        health_state=HealthState.HEALTHY,
        status=ComponentStatus.RUNNING,
        diagnostic_code="HEALTH_OK",
        message="Emotion recognition pipeline operating normally at 30 FPS.",
        metrics={"latency_p95_ms": 12.4, "fps": 29.8, "memory_mb": 115.0},
    )
    assert health.component_id == "eon.ers"
    assert health.health_state == HealthState.HEALTHY
    assert health.status == ComponentStatus.RUNNING
    assert health.metrics is not None
    assert health.metrics["latency_p95_ms"] == 12.4


def test_degraded_component_health_report() -> None:
    """Verify degraded health status reporting with diagnostic code."""
    health = ComponentHealthPayload(
        component_id="eon.core.event_bus",
        health_state=HealthState.DEGRADED,
        status=ComponentStatus.RUNNING,
        diagnostic_code="WARN_QUEUE_BACKPRESSURE",
        message="EventQueue depth exceeded 80% watermark.",
        metrics={"queue_depth": 850.0, "dropped_events": 0.0},
    )
    assert health.health_state == HealthState.DEGRADED
    assert health.diagnostic_code == "WARN_QUEUE_BACKPRESSURE"
