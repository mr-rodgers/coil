import asyncio
from logging import getLogger
from pprint import pformat
from typing import Any, Tuple, TypeAlias

from aiostream import stream

from coil.protocols import Bindable, Bound, DataEventHandler, ReverseBound
from coil.types import DataEvent, get_event_type

SubscriptionHandle: TypeAlias = Tuple[str, int]
LOG = getLogger("coil")


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

    if _is_cyclic_trigger(event):
        LOG.warning(
            "Event has a cyclic trigger. "
            f"It will not be propagated:\n{pformat(event)}"
        )
        return

    for receive in bindable.__coil_bindings__.get(prop, []):
        try:
            receive(event)
        except Exception:
            continue


def _is_cyclic_trigger(event: DataEvent) -> bool:
    orig_source_obj = (id(event["source"].host), event["source"].prop)
    orig_event_type = get_event_type(event)

    LOG.debug(f"Starting search for event with source: {orig_source_obj}")

    while event["source_event"] is not None:
        event = event["source_event"]
        if (
            orig_source_obj == (id(event["source"].host), event["source"].prop)
            and get_event_type(event) == orig_event_type
        ):
            LOG.debug(f"Found: \n{pformat(event)}")
            return True
    else:
        LOG.debug("Not found.")
        return False


def tail(bound: Bound, *, into: ReverseBound) -> asyncio.Task[None]:
    """Forward all changes from a bound value into another.

    This function returns a cancellable `asyncio.Task`, which will
    keep running until the bound value is deleted from the host (if ever).

    Args:
        bound: a bound value from which changes are to be streamed.
        into: a bound value into which changes are sent
    """
    events_stream = stream.iterate(bound.events())
    return asyncio.create_task(_tail(events_stream, into))


async def _tail(events_stream: Any, into: ReverseBound) -> None:
    async with events_stream.stream() as streamer:
        async for event in streamer:
            await into.set(event["value"], source_event=event)

        # fixme: if the stream is exhausted, the field was deleted
