# OVIC EON — Event Bus Developer Guide

**Document ID:** EON-DEV-CORE-001  
**Document Title:** Developer Integration Guide for Core Event Bus  
**Product:** OVIC EON  
**Tagline:** Emotional Intelligence Infrastructure for Robotics  
**Organization:** OVIC Labs  
**Repository:** `https://github.com/Ovic-Labs/EON.git`  
**Milestone:** Phase 1.3 — Core Event Bus  
**Status:** `QUALIFIED AND VERIFIED`  
**Classification:** `PUBLIC DEVELOPER DOCUMENTATION`  

---

## 1. Introduction

The OVIC EON Core Event Bus is an in-memory, asynchronous, CPU-first message routing system. It is designed to connect perception engines, affective models, memory stores, and safety monitors with minimal latency and guaranteed failure isolation.

This guide provides practical examples for:
- Initializing the event bus with custom configurations.
- Subscribing to specific event types and wildcards.
- Publishing typed `EventEnvelope` instances.
- Configuring backpressure policies and priority levels.
- Inspecting runtime metrics.
- Handling graceful shutdown.

---

## 2. Quickstart Example

The recommended pattern is using the async context manager (`async with EventBus()`), which guarantees that workers are started and gracefully stopped upon exiting:

```python
import asyncio
from eon.core import EventBus, EventPriority
from eon.schemas.common import ModalityType, Provenance
from eon.schemas.events import EventEnvelope, EventType
from eon.schemas.observations import ObservationPayload, TextObservationData


async def main() -> None:
    # 1. Initialize Event Bus using async context manager
    async with EventBus() as bus:
        # 2. Define a typed event handler
        async def on_observation(event: EventEnvelope[ObservationPayload]) -> None:
            print(f"Received observation from {event.source}: {event.payload.data.text}")

        # 3. Register subscriber
        sub_id = await bus.subscribe_async(
            event_type=EventType.OBSERVATION,
            handler=on_observation,
            name="text_observer",
        )
        print(f"Registered subscriber: {sub_id}")

        # 4. Construct a validated Phase 1.2 event envelope
        prov = Provenance(
            source_id="sensor.mic.01",
            engine_version="0.1.0",
            capture_device="synthetic_mic",
        )
        payload = ObservationPayload(
            source_id="sensor.mic.01",
            modality=ModalityType.TEXT,
            confidence=0.95,
            provenance=prov,
            data=TextObservationData(text="Hello robot!"),
        )
        event = EventEnvelope(
            event_type=EventType.OBSERVATION,
            source="sensor.mic.01",
            payload=payload,
        )

        # 5. Publish event and await completion
        outcomes = await bus.publish_and_wait(event, priority=EventPriority.NORMAL)
        print(f"Delivery outcome: {outcomes[0].state.value}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. Priority and Scheduling

Events can be scheduled with four explicit priority levels:

```python
from eon.core import EventPriority

# Publishing a critical alarm (scheduling precedence only; not safety authority)
await bus.publish(critical_event, priority=EventPriority.CRITICAL)

# Publishing a standard observation
await bus.publish(obs_event, priority=EventPriority.NORMAL)

# Publishing a background log/housekeeping event
await bus.publish(diag_event, priority=EventPriority.LOW)
```

> [!NOTE]
> Higher priority items are always dequeued before lower priority items. Items with identical priority maintain strict FIFO order. Priority does NOT confer robot movement or emergency-stop authority.

---

## 4. Backpressure Policies

When a subscriber queue reaches capacity, one of four policies is applied:

```python
from eon.core import BackpressurePolicy

# 1. WAIT: Asynchronously pause publisher until space is available (or timeout)
bus.subscribe(
    EventType.OBSERVATION,
    handler,
    backpressure_policy=BackpressurePolicy.WAIT,
    queue_capacity=500,
)

# 2. REJECT: Immediately reject incoming event and raise QueueFullError
bus.subscribe(
    EventType.SAFETY_ADVISORY,
    handler,
    backpressure_policy=BackpressurePolicy.REJECT,
    queue_capacity=100,
)

# 3. DROP_NEWEST: Discard incoming event without raising an error (e.g. video frames)
bus.subscribe(
    EventType.OBSERVATION,
    handler,
    backpressure_policy=BackpressurePolicy.DROP_NEWEST,
    queue_capacity=50,
)

# 4. DROP_OLDEST: Evict oldest queued item to accept incoming event
bus.subscribe(
    EventType.OBSERVATION,
    handler,
    backpressure_policy=BackpressurePolicy.DROP_OLDEST,
    queue_capacity=100,
)
```

---

## 5. Failure Isolation and Timeouts

Subscribers execute in isolated worker loops. If a subscriber handler raises an unhandled exception or hangs, the event bus captures the failure, logs a bounded error, updates metrics, and continues servicing other subscribers:

```python
async def buggy_handler(event: EventEnvelope[ObservationPayload]) -> None:
    raise RuntimeError("Unexpected engine crash")


# Configured with a 0.5-second timeout boundary
await bus.subscribe_async(
    EventType.OBSERVATION,
    buggy_handler,
    timeout_seconds=0.5,
)

# The exception is caught internally; publish() succeeds without crashing the host process
await bus.publish(event)
```

---

## 6. Inspecting Metrics

The event bus collects in-process operational metrics with zero external dependencies:

```python
snapshot = bus.get_metrics()

print(f"Total Published:     {snapshot.total_published}")
print(f"Delivered Events:    {snapshot.delivered_events}")
print(f"Rejected Events:     {snapshot.rejected_events}")
print(f"Dropped Events:      {snapshot.dropped_events}")
print(f"Failed Deliveries:   {snapshot.failed_deliveries}")
print(f"Publish Latency p95: {snapshot.publish_latency_p95_ms} ms")
print(f"Handler Timeouts:    {snapshot.handler_timeout_count}")
```

---

## 7. Synchronous Handlers and Thread Pool Isolation

The Event Bus accommodates both `async def` coroutines and standard synchronous `def` callables:

```python
import time


# Synchronous handler: automatically executed in the thread pool executor
def on_perception_sync(event: EventEnvelope[ObservationPayload]) -> None:
    # Heavy synchronous calculations run in thread worker without blocking asyncio loop
    time.sleep(0.01)
    print(f"Sync handler received event: {event.event_id}")


bus.subscribe(
    EventType.OBSERVATION,
    on_perception_sync,
    name="sync_processor",
)
```

> [!WARNING]
> While synchronous handlers prevent event loop starvation by running in worker threads, standard Python threads cannot be preempted or forcibly killed if they hang. Implement bounded timeouts or cooperative flags inside long-running synchronous code.

---

## 8. Configuration Reference

```python
from eon.core import EventBusConfig, BackpressurePolicy

config = EventBusConfig(
    default_queue_capacity=1000,  # Positive integer > 0
    default_backpressure_policy=BackpressurePolicy.WAIT,  # WAIT | REJECT | DROP_NEWEST | DROP_OLDEST
    publish_timeout_seconds=2.0,  # Positive float > 0.0
    handler_timeout_seconds=5.0,  # Positive float > 0.0
    shutdown_timeout_seconds=5.0,  # Positive float > 0.0
    max_workers_per_subscription=1,  # Positive integer > 0
    sync_executor_workers=4,  # Bounded ThreadPoolExecutor workers > 0
    starvation_threshold=10,  # High dispatches before lower-priority relief > 0
)

bus = EventBus(config=config)
```
