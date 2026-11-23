"""Tests for deterministic queue task accounting, underflow detection, and join unblocking."""

import asyncio

import pytest

from eon.core.queue_manager import SubscriberQueue


@pytest.mark.asyncio
async def test_task_done_underflow_raises_value_error() -> None:
    """Verify task_done() raises ValueError when unfinished_tasks is zero."""
    q = SubscriberQueue(capacity=5, name="underflow_test")
    assert q.unfinished_tasks == 0

    with pytest.raises(ValueError, match="task_done.*too many times"):
        q.task_done()


@pytest.mark.asyncio
async def test_double_task_done_detected() -> None:
    """Verify double task completion on a single item raises ValueError."""
    q = SubscriberQueue(capacity=5, name="double_done_test")
    await q.put("item1")
    assert q.unfinished_tasks == 1

    _prio, item = await q.get()
    assert item == "item1"

    # First completion succeeds
    q.task_done()
    assert q.unfinished_tasks == 0

    # Second completion must fail with underflow detection
    with pytest.raises(ValueError, match="task_done.*too many times"):
        q.task_done()


@pytest.mark.asyncio
async def test_join_unblocks_when_all_tasks_complete() -> None:
    """Verify join() blocks while tasks are unfinished and unblocks when task_done() is called."""
    q = SubscriberQueue(capacity=5, name="join_test")
    await q.put("item1")
    await q.put("item2")
    assert q.unfinished_tasks == 2

    join_completed = False

    async def waiter() -> None:
        nonlocal join_completed
        await q.join()
        join_completed = True

    wait_task = asyncio.create_task(waiter())
    await asyncio.sleep(0.02)
    assert not join_completed

    # Dequeue item1 and complete
    await q.get()
    q.task_done()
    await asyncio.sleep(0.02)
    assert not join_completed
    assert q.unfinished_tasks == 1

    # Dequeue item2 and complete
    await q.get()
    q.task_done()
    assert q.unfinished_tasks == 0

    await asyncio.wait_for(wait_task, timeout=0.5)
    assert join_completed is True


@pytest.mark.asyncio
async def test_join_unblocks_on_closure_and_drain() -> None:
    """Verify join() cannot remain blocked after queue closure and draining."""
    q = SubscriberQueue(capacity=5, name="closure_join_test")
    await q.put("item1")
    assert q.unfinished_tasks == 1

    join_completed = False

    async def waiter() -> None:
        nonlocal join_completed
        await q.join()
        join_completed = True

    wait_task = asyncio.create_task(waiter())
    await asyncio.sleep(0.02)
    assert not join_completed

    # Closing and draining queue balances unfinished tasks and unblocks join()
    q.close()
    q.drain()
    await asyncio.wait_for(wait_task, timeout=0.5)
    assert join_completed is True


@pytest.mark.asyncio
async def test_join_unblocks_after_drain() -> None:
    """Verify drain() balances unfinished tasks and unblocks join()."""
    q = SubscriberQueue(capacity=5, name="drain_join_test")
    await q.put("item1")
    await q.put("item2")
    assert q.unfinished_tasks == 2

    join_completed = False

    async def waiter() -> None:
        nonlocal join_completed
        await q.join()
        join_completed = True

    wait_task = asyncio.create_task(waiter())
    await asyncio.sleep(0.02)
    assert not join_completed

    drained = q.drain()
    assert len(drained) == 2
    assert q.unfinished_tasks == 0

    await asyncio.wait_for(wait_task, timeout=0.5)
    assert join_completed is True


@pytest.mark.asyncio
async def test_concurrent_completion_accounting() -> None:
    """Verify concurrent tasks completing items balance task accounting without underflow."""
    q = SubscriberQueue(capacity=100, name="concurrent_accounting")
    n_items = 50

    for i in range(n_items):
        await q.put(f"item_{i}")

    assert q.unfinished_tasks == n_items

    async def worker() -> None:
        while True:
            try:
                _prio, _item = await asyncio.wait_for(q.get(), timeout=0.05)
                await asyncio.sleep(0.001)
                q.task_done()
            except (asyncio.TimeoutError, Exception):
                break

    workers = [asyncio.create_task(worker()) for _ in range(5)]
    await q.join()
    await asyncio.gather(*workers)

    assert q.unfinished_tasks == 0
    assert q.qsize() == 0
