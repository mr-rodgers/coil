import asyncio
import contextlib

from dataclasses import dataclass
from typing import Any, AsyncIterator

import pytest
import pytest_asyncio

from coil import bindableclass, BindableValue


@dataclass
class Size:
    width: float
    height: float


@bindableclass
class Window:
    size: BindableValue[Size] = Size(1024, 768)


@pytest.fixture
def window() -> Window:
    return Window()


@pytest_asyncio.fixture(autouse=True)
async def cancel_running_tasks() -> AsyncIterator[Any]:
    yield

    all_tasks = {task for task in asyncio.all_tasks() if task != asyncio.current_task()}

    for task in all_tasks:
        if not task.done():
            task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.gather(*all_tasks)
