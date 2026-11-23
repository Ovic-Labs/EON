"""Tests for EventRouter thread safety and concurrent operations."""

import asyncio
import concurrent.futures

import pytest

from eon.core.backpressure import BackpressurePolicy
from eon.core.event_router import EventRouter
from eon.core.subscription import Subscription


def _make_dummy_sub(sub_id: str, etype: str) -> Subscription:
    async def dummy(_e: object) -> None:
        pass

    return Subscription(
        subscription_id=sub_id,
        event_type=etype,
        handler=dummy,
        name=f"sub_{sub_id}",
        backpressure_policy=BackpressurePolicy.WAIT,
        queue_capacity=10,
        timeout_seconds=5.0,
    )


def test_event_router_multithreaded_concurrency() -> None:
    """Verify EventRouter handles concurrent operations across threads."""
    router = EventRouter()
    n_threads = 6
    n_ops = 100

    def worker(worker_id: int) -> None:
        for i in range(n_ops):
            sub_id = f"sub_{worker_id}_{i}"
            etype = f"eon.event_{i % 5}"
            sub = _make_dummy_sub(sub_id, etype)

            router.register(sub)
            subs = router.get_subscribers(etype)
            assert len(subs) >= 1
            all_subs = router.get_all_subscribers()
            assert len(all_subs) >= 1

            unregistered = router.unregister(sub_id)
            assert unregistered.subscription_id == sub_id

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(n_threads)]
        concurrent.futures.wait(futures)
        for f in futures:
            f.result()

    assert router.subscription_count() == 0


@pytest.mark.asyncio
async def test_event_router_asyncio_concurrent_mutations() -> None:
    """Verify EventRouter snapshot isolation during concurrent asynchronous registration."""
    router = EventRouter()

    async def mutator(idx: int) -> None:
        for i in range(50):
            sub_id = f"async_sub_{idx}_{i}"
            sub = _make_dummy_sub(sub_id, "eon.dynamic")
            router.register(sub)
            await asyncio.sleep(0.001)
            router.unregister(sub_id)

    async def reader() -> None:
        for _ in range(100):
            subs = router.get_subscribers("eon.dynamic")
            # Snapshot should be safe to iterate over without size change errors
            for s in subs:
                _ = s.is_active
            await asyncio.sleep(0.001)

    tasks = [asyncio.create_task(mutator(i)) for i in range(4)]
    tasks.append(asyncio.create_task(reader()))

    await asyncio.gather(*tasks)
    assert router.subscription_count() == 0
