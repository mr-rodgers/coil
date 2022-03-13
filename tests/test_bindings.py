import asyncio
from typing import Any, AsyncIterable, List, cast

import pytest
from aiostream import pipe, stream

from coil import bind
from coil.protocols import Bindable

from .conftest import Size, Window


@pytest.mark.asyncio
@pytest.mark.parametrize("num_values", [100])
async def test_bind_produces_result_stream(
    window: Window, num_values: int
) -> None:
    bound_value = bind((window, "size"))
    event_stream = stream.iterate(bound_value.events()) | pipe.take(num_values)

    sent_sizes = []

    async def drain(s: AsyncIterable[Any]) -> List[Any]:
        return await stream.list(s)

    task = asyncio.create_task(drain(event_stream))

    for i in range(num_values):
        perc = (i + 1) / num_values
        size = Size(perc * 1024, perc * 768)
        window.size = size
        sent_sizes.append(size)

    assert sent_sizes == [val["value"] for val in await task]


@pytest.mark.asyncio
@pytest.mark.parametrize("new_size", [Size(1920, 1080), Size(1280, 720)])
async def test_setting_value_from_two_way_bind(
    window: Window, new_size: Size
) -> None:
    assert window.size != new_size

    bound_value = bind((cast(Bindable, window), "size"), readonly=False)
    await bound_value.set(new_size)

    assert window.size == new_size
