import asyncio
from typing import Any, Tuple, TypeAlias

from aiostream import stream

from coil.protocols import Bindable, Bound, DataEventHandler, ReverseBound
from coil.types import DataEvent

SubscriptionHandle: TypeAlias = Tuple[str, int]


def bound_attr_name(name: str) -> str:
    return f"_bound__value__{name}"


def add_subscription(
    bindable: Bindable, prop: str, handler: DataEventHandler
) -> SubscriptionHandle:
    """
    Add a subscription for the given property name.

    The subscription should track both updates and deletions
    for the given property. In addition, it should return a handle
    which can be used to drop the subscription later.
    """
    bindable.__coil_bindings__.setdefault(prop, []).append(handler)
    return (prop, id(handler))


def drop_subscription(bindable: Bindable, handle: SubscriptionHandle) -> None:
    """Remove a subscription from a bindable."""
    (prop_name, handler_id) = handle

    handlers = bindable.__coil_bindings__.get(prop_name, [])
    handler = next((h for h in handlers if id(h) == handler_id), None)

    if handler is not None:
        handlers.remove(handler)
    else:
        raise LookupError(f"Invalid subscription: {handle}")


def notify_subscribers(
    bindable: Bindable, prop: str, event: DataEvent
) -> None:
    for receive in bindable.__coil_bindings__.get(prop, []):
        try:
            receive(event)
        except Exception:
            continue


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
