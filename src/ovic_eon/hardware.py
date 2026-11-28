"""Host-side sensor contract and in-memory simulator for bench acceptance tests."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from time import monotonic
from typing import Callable, Protocol


class LinkState(StrEnum):
    OFFLINE = "offline"
    READY = "ready"
    STALE = "stale"
    STOPPED = "stopped"


@dataclass(frozen=True)
class SensorFrame:
    """Optional JPEG and mono signed 16-bit PCM from one simulated capture."""

    jpeg: bytes | None = None
    pcm: bytes | None = None
    sample_rate: int = 16000


class SensorPort(Protocol):
    def read(self) -> SensorFrame: ...


class SimulatedRobot:
    """Single-owner simulator. A latched stop needs an explicit reset and reconnect."""

    def __init__(self, timeout: float = 1.0, *, clock: Callable[[], float] = monotonic):
        if not isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self._clock = clock
        self._timeout = timeout
        self._heartbeat: float | None = None
        self._stopped = False
        self._frame = SensorFrame()

    @property
    def state(self) -> LinkState:
        if self._stopped:
            return LinkState.STOPPED
        if self._heartbeat is None:
            return LinkState.OFFLINE
        if self._clock() - self._heartbeat >= self._timeout:
            return LinkState.STALE
        return LinkState.READY

    def connect(self) -> None:
        if self._stopped:
            raise RuntimeError("Emergency stop is latched")
        self._frame = SensorFrame()
        self._heartbeat = self._clock()

    def update(self, frame: SensorFrame) -> None:
        if self.state != LinkState.READY:
            raise RuntimeError("Sensor link unavailable")
        self._frame = frame
        self._heartbeat = self._clock()

    def read(self) -> SensorFrame:
        if self.state != LinkState.READY:
            raise RuntimeError("Sensor link unavailable")
        return self._frame

    def disconnect(self) -> None:
        self._heartbeat = None
        self._frame = SensorFrame()

    def emergency_stop(self) -> None:
        self._stopped = True
        self.disconnect()

    def reset(self) -> None:
        self.disconnect()
        self._stopped = False
