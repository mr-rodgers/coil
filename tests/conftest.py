import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any, AsyncIterator

import pytest
import pytest_asyncio

from coil import BindableValue, bindableclass


@dataclass
class Size:
    width: float
    height: float


@bindableclass
class Window:
    size: BindableValue[Size] = Size(1024, 768)


@bindableclass
class Box:
    value: BindableValue[int]

    def __repr__(self) -> str:
        return f"<Box object: {id(self)}>"


@pytest.fixture
def window() -> Window:
    return Window()


@pytest.fixture
def box() -> Box:
    return Box(10)


@pytest_asyncio.fixture(autouse=True)
async def cancel_running_tasks() -> AsyncIterator[Any]:
    yield

    all_tasks = {
        task for task in asyncio.all_tasks() if task != asyncio.current_task()
    }

    for task in all_tasks:
        if not task.done():
            task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.gather(*all_tasks)
