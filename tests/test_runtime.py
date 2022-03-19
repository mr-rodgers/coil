import asyncio
import contextlib
from typing import Any, AsyncIterator, Callable

import pytest
import pytest_asyncio

from coil._runtime import Runtime, runtime
from tests.conftest import Box

TaskFactory = Callable[[], asyncio.Task[Any]]

# This fixture doesn't work because the context somehow changes
# by the time the context is unraveled
# @pytest_asyncio.fixture  # type: ignore
# async def active_runtime() -> AsyncIterator[Runtime]:
#     async with Runtime() as rt:
#         yield rt


@pytest.fixture
def rt() -> Runtime:
    return Runtime()


@pytest_asyncio.fixture
async def task_factory() -> AsyncIterator[TaskFactory]:
    tasks = []

    async def _forever() -> None:
        while True:
            await asyncio.sleep(1)

    def _make_task() -> asyncio.Task[Any]:
        task = asyncio.create_task(_forever())
        tasks.append(task)
        return task

    try:
        yield _make_task
    finally:
        meta_task = asyncio.gather(*tasks)
        meta_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await meta_task


def test_runtime_returns_new_runtime_when_no_active_runtime() -> None:
    assert isinstance(runtime(), Runtime)
    assert isinstance(runtime(ensure=True), Runtime)
    with pytest.raises(RuntimeError):
        runtime(ensure=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("ensure", [True, False])
async def test_runtime_returns_active_runtime_when_set(ensure: bool) -> None:
    async with Runtime() as active_rt:
        assert runtime() is active_rt
        assert runtime(ensure=ensure) is active_rt


@pytest.mark.asyncio
async def test_cant_register_on_inactive_runtime(
    task_factory: TaskFactory, box: Box
) -> None:
    task = task_factory()
    rt = Runtime()

    with pytest.raises(AttributeError):
        rt.register(task, "foo")

    with pytest.raises(AttributeError):
        rt.register(task, "foo", source=(box, "value"))

    assert not task.done()


@pytest.mark.asyncio
async def test_registered_tasks_cancelled_on_context_exit(
    box: Box, task_factory: TaskFactory
) -> None:
    task1 = task_factory()
    task2 = task_factory()

    async with runtime() as rt:
        rt.register(task1, "foo")
        rt.register(task2, "bar", source=(box, "value"))

        assert not task1.done()
        assert not task2.done()

    assert task1.done()
    assert task2.done()


@pytest.mark.asyncio
async def test_forgotten_tasks_not_cancelled_on_context_exit(
    box: Box, task_factory: TaskFactory
) -> None:
    task1 = task_factory()
    task2 = task_factory()

    async with runtime() as rt:
        rt.register(task1, "foo")
        rt.register(task2, "bar", source=(box, "value"))

        assert not task1.done()
        assert not task2.done()

        rt.forget(task1)
        rt.forget(task2)

    assert not task1.done()
    assert not task2.done()


@pytest.mark.asyncio
async def test_retrieve_registered_tasks(
    box: Box, task_factory: TaskFactory
) -> None:
    all_tasks = [task_factory() for _ in range(100)]
    box_tasks = [
        asyncio.create_task(asyncio.wait_for(task, timeout=None))
        for task in all_tasks
    ]

    async with runtime() as rt:
        for task, box_task in zip(all_tasks, box_tasks):
            assert task is not box_task

            rt.register(task, f"{id(task)}")
            rt.register(box_task, f"{id(box_task)}", source=(box, "value"))

            assert not task.done()
            assert not box_task.done()

        for task, box_task in zip(all_tasks, box_tasks):
            assert rt.find(f"{id(task)}") is task
            assert rt.find(f"{id(task)}", source=(box, "value")) is None
            assert rt.find(f"{id(box_task)}") is None
            assert (
                rt.find(f"{id(box_task)}", source=(box, "value")) is box_task
            )

            assert not box_task.done()
            assert not task.done()


@pytest.mark.asyncio
async def test_registering_multiple_tasks_with_same_name(
    task_factory: TaskFactory, box: Box
) -> None:
    task1 = task_factory()
    task2 = task_factory()

    async with runtime() as rt:
        rt.register(task1, "foo")
        rt.register(task2, "foo", source=(box, "value"))

        # re-entrant safe
        rt.register(task1, "foo")
        rt.register(task2, "foo", source=(box, "value"))

        with pytest.raises(ValueError):
            rt.register(task_factory(), "foo")
            rt.register(task_factory(), "foo", source=(box, "value"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc",
    [
        ValueError("An error has occurred"),
        TypeError("An error has occured"),
        RuntimeError("Another error has occcured/"),
    ],
)
async def test_exceptions_in_registered_tasks_are_suppressed_and_logged(
    exc: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    async def _raise() -> None:
        raise exc

    task = asyncio.create_task(_raise())

    async with runtime() as rt:
        rt.register(task, "task")

        assert not task.done()
        await asyncio.sleep(0)

    assert task.done()
    assert task.exception() is exc

    last_error_record = next(
        (
            record
            for record in reversed(caplog.records)
            if record.levelname == "ERROR"
        ),
        None,
    )
    assert last_error_record is not None
    assert last_error_record.name == "coil.runtime"
    assert (
        "Unhandled exception in registered task:" == last_error_record.message
    )
    assert type(exc) is last_error_record.exc_info[0]
    assert exc is last_error_record.exc_info[1]
