import asyncio
from typing import Any

from aiostream import stream

from coil.protocols import Bound, ReverseBound


def bound_attr_name(name: str) -> str:
    return f"_bound__value__{name}"


def tail(bound: Bound, *, into: ReverseBound) -> asyncio.Task[None]:
    """Forward all changes from a bound value into another.

    :param bound: a bound value from which changes can be streamed.
    :param into: a bound value into which changes can be sent.

    This function returns a cancellable asyncio.Task, which will
    keep running until the bound value is deleted from the host (if ever).
    """
    events_stream = stream.iterate(bound.events())
    return asyncio.create_task(_tail(events_stream, into))


async def _tail(events_stream: Any, into: ReverseBound) -> None:
    async with events_stream.stream() as streamer:
        async for event in streamer:
            await into.set(event["value"], source=event)

        # fixme: if the stream is exhausted, the field was deleted
