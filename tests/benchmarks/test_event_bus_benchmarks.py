"""Performance benchmarks for OVIC EON Core Event Bus.

Evaluates throughput (target >= 1,000 events/sec) and routing latency
(target p95 <= 5.0 ms) under controlled, reproducible conditions.
"""

import asyncio
import os
import platform
import time

import pytest

from eon.core.event_bus import EventBus, EventBusConfig
from eon.core.priority import EventPriority
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)


def _make_benchmark_event(index: int) -> EventEnvelope[ObservationPayload]:
    prov = Provenance(
        source_id="benchmark.producer",
        engine_version="0.1.0",
        capture_device="synthetic_bench",
    )
    payload = ObservationPayload(
        source_id="benchmark.producer",
        modality=ModalityType.TEXT,
        confidence=0.99,
        provenance=prov,
        data=TextObservationData(text=f"Benchmark payload sample index {index}"),
    )
    return EventEnvelope(
        event_type=EventType.OBSERVATION,
        source="benchmark.producer",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_baseline_throughput_and_latency_benchmark() -> None:
    """AC-1.3-19: Benchmark throughput and p95 latency under high-volume publishing."""
    config = EventBusConfig(
        default_queue_capacity=10000,
        publish_timeout_seconds=5.0,
        handler_timeout_seconds=5.0,
    )

    async with EventBus(config=config) as bus:
        received_count = 0
        all_received_event = asyncio.Event()
        target_events = 2000

        async def sink_handler(_event: EventEnvelope[ObservationPayload]) -> None:
            nonlocal received_count
            received_count += 1
            if received_count >= target_events:
                all_received_event.set()

        await bus.subscribe_async(
            EventType.OBSERVATION,
            sink_handler,
            name="bench_sink",
            queue_capacity=10000,
        )

        # Warm-up phase: 100 events
        for i in range(100):
            warmup_ev = _make_benchmark_event(i)
            await bus.publish(warmup_ev)
        await asyncio.sleep(0.05)

        # Reset counter for measurement
        received_count = 0
        all_received_event.clear()

        # Measurement phase: 2000 events
        events = [_make_benchmark_event(i) for i in range(target_events)]

        start_time = time.monotonic()
        for ev in events:
            await bus.publish(ev, priority=EventPriority.NORMAL)

        # Wait for all events to be dispatched and processed by subscriber worker
        await asyncio.wait_for(all_received_event.wait(), timeout=10.0)
        total_duration = time.monotonic() - start_time

        throughput = target_events / total_duration
        metrics = bus.get_metrics()

        print("\n" + "=" * 60)
        print("   OVIC EON Core Event Bus — Performance Benchmark Results")
        print("=" * 60)
        plat_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        print(f"Platform:            {plat_info}")
        print(f"Python Version:      {platform.python_version()}")
        print(f"CPU Count:           {os.cpu_count()}")
        print(f"Total Events:        {target_events}")
        print(f"Elapsed Time:        {total_duration:.4f} seconds")
        print(f"Throughput:          {throughput:.2f} events/sec")
        print(f"Publish Latency p50: {metrics.publish_latency_p50_ms:.3f} ms")
        print(f"Publish Latency p95: {metrics.publish_latency_p95_ms:.3f} ms")
        print(f"Publish Latency p99: {metrics.publish_latency_p99_ms:.3f} ms")
        print(f"Handler Exec p50:    {metrics.handler_execution_p50_ms:.3f} ms")
        print(f"Handler Exec p95:    {metrics.handler_execution_p95_ms:.3f} ms")
        print(f"Max Queue Depth:     {metrics.max_queue_depth}")
        print("=" * 60)

        # Assert qualification targets
        assert throughput >= 1000.0, f"Throughput {throughput:.2f} ev/s < 1,000 ev/s target"
        assert metrics.publish_latency_p95_ms <= 5.0, (
            f"p95 latency {metrics.publish_latency_p95_ms} ms > 5.0 ms target"
        )


@pytest.mark.asyncio
async def test_multi_subscriber_fanout_benchmark() -> None:
    """Benchmark fan-out throughput with 5 concurrent subscribers receiving 1,000 events."""
    config = EventBusConfig(default_queue_capacity=5000)
    async with EventBus(config=config) as bus:
        sub_count = 5
        event_count = 1000
        total_expected_deliveries = sub_count * event_count
        received_total = 0
        all_done = asyncio.Event()

        async def multi_sink(_event: EventEnvelope[ObservationPayload]) -> None:
            nonlocal received_total
            received_total += 1
            if received_total >= total_expected_deliveries:
                all_done.set()

        for s in range(sub_count):
            await bus.subscribe_async(
                EventType.OBSERVATION,
                multi_sink,
                name=f"sink_{s}",
                queue_capacity=5000,
            )

        events = [_make_benchmark_event(i) for i in range(event_count)]
        start_ts = time.monotonic()
        for ev in events:
            await bus.publish(ev)

        await asyncio.wait_for(all_done.wait(), timeout=10.0)
        duration = time.monotonic() - start_ts
        delivery_rate = total_expected_deliveries / duration

        print("\n" + "=" * 60)
        print("   OVIC EON Core Event Bus — Multi-Subscriber Fan-out Benchmark")
        print("=" * 60)
        print(f"Subscribers:         {sub_count}")
        print(f"Published Events:    {event_count}")
        print(f"Total Deliveries:    {total_expected_deliveries}")
        print(f"Elapsed Time:        {duration:.4f} seconds")
        print(f"Delivery Rate:       {delivery_rate:.2f} deliveries/sec")
        print("=" * 60)

        assert delivery_rate >= 1000.0
