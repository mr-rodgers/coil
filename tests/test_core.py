import asyncio

import pytest

from coil import bind
from coil._core import tail

from .conftest import Size, Window


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
