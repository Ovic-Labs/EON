"""Robot and actuator safety isolation enforcement for ERS.

ERS is strictly an observation subsystem and must never authorize or issue physical
robot actuator, wheel, joint, torque, or trajectory commands.
"""

from __future__ import annotations

from typing import Any

from eon_ers.exceptions import ERSSafetyViolationError

FORBIDDEN_MOTION_KEYS: frozenset[str] = frozenset(
    {
        "cmd_vel",
        "motion",
        "actuator",
        "motor",
        "joint",
        "trajectory",
        "velocity",
        "move",
        "wheel",
        "torque",
    }
)


def assert_no_actuator_commands(payload: Any) -> None:
    """Recursively reject any payload key attempting robot motion or actuator control."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            k_str = str(k).lower()
            if any(forbidden in k_str for forbidden in FORBIDDEN_MOTION_KEYS):
                raise ERSSafetyViolationError(
                    f"Safety violation: ERS event payload contains forbidden motion key '{k}'. "
                    "ERS is strictly a perceptual system and must never issue robot actuator commands.",
                    context={"forbidden_key": str(k)},
                )
            assert_no_actuator_commands(v)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_actuator_commands(item)
