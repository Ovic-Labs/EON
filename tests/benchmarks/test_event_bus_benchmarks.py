"""Performance benchmarks for OVIC EON Core Event Bus.

Evaluates throughput (target >= 1,000 events/sec) and dissected routing latencies
(creation, enqueue, queue residence, handler execution, end-to-end) under
controlled, reproducible conditions with sync and async subscribers.
"""

import asyncio
import os
import platform
import time
from typing import Final

import pytest

from eon.core.event_bus import EventBus, EventBusConfig
from eon.core.priority import EventPriority
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import (
    ObservationPayload,
    TextObservationData,
)

TARGET_THROUGHPUT: Final[float] = 1000.0


def _percentile(samples: list[float], p: float) -> float:
    if not samples:
        return 0.0
    s = sorted(samples)
    idx = min(int(len(s) * (p / 100.0)), len(s) - 1)
    return round(s[idx], 3)


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
        assert throughput >= TARGET_THROUGHPUT, (
            f"Throughput {throughput:.2f} ev/s < {TARGET_THROUGHPUT} target"
        )
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

        assert delivery_rate >= TARGET_THROUGHPUT


@pytest.mark.asyncio
async def test_dissected_latency_stages_benchmark() -> None:
    """DEF-1.3-11: Dissect latencies across creation, enqueue, residence, handler duration,
    and end-to-end delivery under queue pressure.
    """
    config = EventBusConfig(
        default_queue_capacity=5000,
        sync_executor_workers=4,
    )
    async with EventBus(config=config) as bus:
        n_events = 500

        creation_latencies_ms: list[float] = []
        enqueue_latencies_ms: list[float] = []
        residence_async_ms: list[float] = []
        residence_sync_ms: list[float] = []
        handler_async_ms: list[float] = []
        handler_sync_ms: list[float] = []
        e2e_async_ms: list[float] = []
        e2e_sync_ms: list[float] = []

        publish_timestamps: dict[str, float] = {}
        all_async_done = asyncio.Event()
        all_sync_done = asyncio.Event()
        async_count = 0
        sync_count = 0

        async def async_subscriber(event: EventEnvelope[ObservationPayload]) -> None:
            nonlocal async_count
            h_start = time.perf_counter_ns()
            ev_id = str(event.event_id)
            pub_ts = publish_timestamps.get(ev_id, h_start)
            residence = (h_start - pub_ts) / 1_000_000.0
            residence_async_ms.append(residence)

            # Minimal processing simulation
            _ = event.payload.confidence * 2.0

            h_duration = (time.perf_counter_ns() - h_start) / 1_000_000.0
            handler_async_ms.append(h_duration)
            e2e_async_ms.append(residence + h_duration)

            async_count += 1
            if async_count >= n_events:
                all_async_done.set()

        def sync_subscriber(event: EventEnvelope[ObservationPayload]) -> None:
            nonlocal sync_count
            h_start = time.perf_counter_ns()
            ev_id = str(event.event_id)
            pub_ts = publish_timestamps.get(ev_id, h_start)
            residence = (h_start - pub_ts) / 1_000_000.0
            residence_sync_ms.append(residence)

            # Sync CPU processing simulation
            _ = sum(ord(c) for c in (event.payload.data.text or ""))

            h_duration = (time.perf_counter_ns() - h_start) / 1_000_000.0
            handler_sync_ms.append(h_duration)
            e2e_sync_ms.append(residence + h_duration)

            sync_count += 1
            if sync_count >= n_events:
                all_sync_done.set()

        await bus.subscribe_async(EventType.OBSERVATION, async_subscriber, name="bench_async_sub")
        await bus.subscribe_async(EventType.OBSERVATION, sync_subscriber, name="bench_sync_sub")

        # Create and measure events
        events: list[EventEnvelope[ObservationPayload]] = []
        for i in range(n_events):
            t0 = time.perf_counter_ns()
            ev = _make_benchmark_event(i)
            t1 = time.perf_counter_ns()
            creation_latencies_ms.append((t1 - t0) / 1_000_000.0)
            events.append(ev)

        # Publish and measure enqueue
        for ev in events:
            t0 = time.perf_counter_ns()
            publish_timestamps[str(ev.event_id)] = t0
            await bus.publish(ev)
            t1 = time.perf_counter_ns()
            enqueue_latencies_ms.append((t1 - t0) / 1_000_000.0)

        # Wait for both subscribers to complete
        await asyncio.wait_for(
            asyncio.gather(all_async_done.wait(), all_sync_done.wait()),
            timeout=10.0,
        )

        print("\n" + "=" * 70)
        print("   OVIC EON Core Event Bus — Dissected Latency Benchmark (DEF-1.3-11)")
        print("=" * 70)
        print(f"Sample Size: {n_events} events × 2 subscribers (1 Async + 1 Sync)")
        print("-" * 70)
        print(f"{'Latency Stage':<28} {'p50 (ms)':<12} {'p95 (ms)':<12} {'p99 (ms)':<12}")
        print("-" * 70)
        print(
            f"{'1. Event Creation':<28} "
            f"{_percentile(creation_latencies_ms, 50):<12.3f} "
            f"{_percentile(creation_latencies_ms, 95):<12.3f} "
            f"{_percentile(creation_latencies_ms, 99):<12.3f}"
        )
        print(
            f"{'2. Publish Enqueue':<28} "
            f"{_percentile(enqueue_latencies_ms, 50):<12.3f} "
            f"{_percentile(enqueue_latencies_ms, 95):<12.3f} "
            f"{_percentile(enqueue_latencies_ms, 99):<12.3f}"
        )
        print(
            f"{'3a. Queue Residence (Async)':<28} "
            f"{_percentile(residence_async_ms, 50):<12.3f} "
            f"{_percentile(residence_async_ms, 95):<12.3f} "
            f"{_percentile(residence_async_ms, 99):<12.3f}"
        )
        print(
            f"{'3b. Queue Residence (Sync)':<28} "
            f"{_percentile(residence_sync_ms, 50):<12.3f} "
            f"{_percentile(residence_sync_ms, 95):<12.3f} "
            f"{_percentile(residence_sync_ms, 99):<12.3f}"
        )
        print(
            f"{'4a. Handler Exec (Async)':<28} "
            f"{_percentile(handler_async_ms, 50):<12.3f} "
            f"{_percentile(handler_async_ms, 95):<12.3f} "
            f"{_percentile(handler_async_ms, 99):<12.3f}"
        )
        print(
            f"{'4b. Handler Exec (Sync)':<28} "
            f"{_percentile(handler_sync_ms, 50):<12.3f} "
            f"{_percentile(handler_sync_ms, 95):<12.3f} "
            f"{_percentile(handler_sync_ms, 99):<12.3f}"
        )
        print(
            f"{'5a. End-to-End (Async)':<28} "
            f"{_percentile(e2e_async_ms, 50):<12.3f} "
            f"{_percentile(e2e_async_ms, 95):<12.3f} "
            f"{_percentile(e2e_async_ms, 99):<12.3f}"
        )
        print(
            f"{'5b. End-to-End (Sync)':<28} "
            f"{_percentile(e2e_sync_ms, 50):<12.3f} "
            f"{_percentile(e2e_sync_ms, 95):<12.3f} "
            f"{_percentile(e2e_sync_ms, 99):<12.3f}"
        )
        print("=" * 70)

        assert _percentile(enqueue_latencies_ms, 95) <= 5.0
        assert _percentile(handler_async_ms, 95) <= 5.0
