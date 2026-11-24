"""Unit and contract tests for the EON Core integration boundary adapter."""

import pytest
from eon_ers.core.adapter import (
    CoreEventBusAdapter,
    CoreIntegrationStatus,
    EONCoreEventBusProtocol,
)


class MockEONCoreBus:
    """Mock implementation adhering to EONCoreEventBusProtocol for contract testing."""

    def __init__(self, should_fail: bool = False) -> None:
        self.published_events: list[tuple[str, dict]] = []
        self.should_fail = should_fail

    def publish(self, topic: str, payload: dict, **kwargs) -> None:
        if self.should_fail:
            raise ConnectionError("Mock Core bus connection lost")
        self.published_events.append((topic, payload))

    def subscribe(self, topic: str, handler) -> None:
        pass


def test_core_protocol_conformance() -> None:
    bus = MockEONCoreBus()
    assert isinstance(bus, EONCoreEventBusProtocol)


def test_standalone_adapter_reports_not_connected() -> None:
    adapter = CoreEventBusAdapter(external_bus=None)
    health = adapter.check_health()

    assert health["status"] == CoreIntegrationStatus.NOT_CONNECTED.value
    assert health["external_bus_detected"] is False
    assert health["is_connected_to_core"] is False
    assert health["missing_dependencies"] == ["eon.core.event_bus"]
    assert health["verified_against_production_core"] is False
    assert health["safety_interlocks_active"] is True


def test_connected_adapter_reports_connected() -> None:
    bus = MockEONCoreBus()
    adapter = CoreEventBusAdapter(external_bus=bus)
    health = adapter.check_health()

    assert health["status"] == CoreIntegrationStatus.CONNECTED.value
    assert health["external_bus_detected"] is True
    assert health["is_connected_to_core"] is True
    assert health["missing_dependencies"] == []


@pytest.mark.asyncio
async def test_motion_command_safety_rejection() -> None:
    adapter = CoreEventBusAdapter()
    for forbidden_key in ["cmd_vel", "actuator_pos", "motor_rpm", "joint_angles", "wheel_speed"]:
        payload = {"observation_id": "obs-1", forbidden_key: 1.0}
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.publish("ers.observation.created", payload)
        assert "Safety violation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_external_bus_failure_not_silently_swallowed() -> None:
    failing_bus = MockEONCoreBus(should_fail=True)
    adapter = CoreEventBusAdapter(external_bus=failing_bus)

    with pytest.raises(RuntimeError) as exc_info:
        await adapter.publish("ers.observation.created", {"observation_id": "obs-1"})
    assert "EON Core event bus publication failed" in str(exc_info.value)
    assert adapter.integration_status == CoreIntegrationStatus.ERROR


@pytest.mark.asyncio
async def test_local_subscriber_dispatch() -> None:
    adapter = CoreEventBusAdapter(external_bus=None)
    received: list[dict] = []

    def on_event(topic: str, payload: dict) -> None:
        received.append(payload)

    adapter.subscribe("ers.observation.created", on_event)
    await adapter.publish("ers.observation.created", {"data": 42})

    assert len(received) == 1
    assert received[0]["data"] == 42
