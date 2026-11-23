"""Component health, status, and diagnostic data contracts."""

from enum import Enum

from pydantic import Field

from eon.schemas.base import EonBaseModel
from eon.schemas.identifiers import SourceId
from eon.schemas.timestamps import UtcTimestamp, utc_now


class HealthState(str, Enum):
    """Categorical operational health states of an EON engine or service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ComponentStatus(str, Enum):
    """Runtime lifecycle execution states."""

    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


class ComponentHealthPayload(EonBaseModel):
    """Diagnostic health heartbeat published by EON core and engine components."""

    component_id: SourceId = Field(
        ...,
        description="Identifier of the component reporting health status (e.g. 'eon.ers').",
    )
    health_state: HealthState = Field(
        ...,
        description="Current operational health category.",
    )
    status: ComponentStatus = Field(
        ...,
        description="Current runtime lifecycle status.",
    )
    timestamp: UtcTimestamp = Field(
        default_factory=utc_now,
        description="Timezone-aware UTC timestamp of this diagnostic report.",
    )
    diagnostic_code: str | None = Field(
        default=None,
        max_length=64,
        description="Optional diagnostic or error code.",
    )
    message: str | None = Field(
        default=None,
        max_length=512,
        description="Human-readable status summary or diagnostic note.",
    )
    metrics: dict[str, float] | None = Field(
        default=None,
        description="Key performance indicators (e.g. latency_ms, queue_depth, memory_mb).",
    )
