import asyncio
from typing import Iterator, Protocol
from unittest.mock import MagicMock

import pytest

from coil import bind
from coil._core import (
    add_subscription,
    drop_subscription,
    notify_subscribers,
    tail,
)
from coil.protocols import BindingTarget
from coil.types import DataUpdatedEvent

from .conftest import Box, Size, Window


class Subscriber(Protocol):
    def __call__(self, target: BindingTarget) -> MagicMock:
        pass


@pytest.fixture
def subscribe() -> Iterator[Subscriber]:
    sub_handles = []

    def _subscribe(target: BindingTarget) -> MagicMock:
        mock = MagicMock()
        sub_handles.append(
            (target.host, add_subscription(target.host, target.prop, mock))
        )
        return mock

    yield _subscribe

    for bindable, sub_handle in sub_handles:
        drop_subscription(bindable, sub_handle)


@pytest.mark.asyncio
async def test_tail_binding(window: Window) -> None:
    tailed_window = Window(size=Size(window.size.width, window.size.height))

    bound_size = bind((window, "size"))
    # this returned task will be cancelled automatically by a test
    # fixture; normal usage requires this to be done before exiting
    tail(bound_size, into=bind((tailed_window, "size"), readonly=False))

    async def wait_for_update():
        while window.size != tailed_window.size:
            await asyncio.sleep(0)

    window.size = Size(400, 600)
    await asyncio.wait_for(wait_for_update(), 0.5)

    window.size = Size(600, 400)
    await asyncio.wait_for(wait_for_update(), 0.5)

    assert window.size == tailed_window.size


@pytest.mark.asyncio
async def test_cyclic_events_are_not_notified(
    subscribe: Subscriber, caplog: pytest.LogCaptureFixture
) -> None:
    box = Box(10)
    window = Window()

    evt1 = DataUpdatedEvent(
        source_event=None, source=Box.value.bind(box), value=11
    )
    evt2 = DataUpdatedEvent(
        source_event=evt1, source=Window.size.bind(window), value=100
    )
    evt3 = DataUpdatedEvent(
        source_event=evt2, source=Box.value.bind(box), value=11
    )
    mock = subscribe(Box.value.bind(box))

    notify_subscribers(box, "value", evt3)
    assert mock.call_count == 0

    last_coil_record = next(
        (record for record in caplog.records if record.name == "coil"), None
    )
    assert last_coil_record is not None
    assert last_coil_record.levelname == "WARNING"
    assert last_coil_record.message.startswith(
        "Event has a cyclic trigger. It will not be propagated:"
    )
