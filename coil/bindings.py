import asyncio
import contextlib
from dataclasses import dataclass
from email.generator import Generator
from typing import Any, AsyncGenerator, AsyncIterable, Literal, Tuple, overload

from coil.protocols.bindable import notify_subscribers
from coil.types.events import DataDeletedEvent

from .protocols import (
    Bindable,
    Bound,
    TwoWayBound,
    add_subscription,
    drop_subscription,
    notify_subscribers,
)
from .types import DataEvent, DataUpdatedEvent, is_update_event
from .utils import bound_attr_name


@dataclass
class Binding(TwoWayBound):
    host: Bindable
    prop: str

    def events(self) -> AsyncIterable[DataUpdatedEvent]:
        return BindingEventStream(self)

    async def set(self, value: Any, source: DataEvent | None = None) -> None:
        setattr(self.host, bound_attr_name(self.prop), value)
        event = DataUpdatedEvent(source=source, value=value)
        notify_subscribers(self.host, self.prop, event)

    async def unset(self) -> None:
        delattr(self.host, bound_attr_name(self.prop))
        event = DataDeletedEvent(source=None)
        notify_subscribers(self.host, self.prop, event)

    def __repr__(self) -> str:
        return f"BoundValue({repr(self.host)}.{self.prop})"


class BindingEventStream:
    binding: Binding

    def __init__(self, binding: Binding):
        self.binding = binding
        self.new_data = asyncio.Queue[DataEvent]()
        self.subsciption_handle = add_subscription(
            binding.host, binding.prop, self._handle_event
        )

    def __del__(self) -> None:
        drop_subscription(self.binding.host, self.subsciption_handle)

    def __aiter__(self) -> Any:
        return self

    async def __anext__(self) -> DataUpdatedEvent:
        event = await self.new_data.get()

        if is_update_event(event):
            return event

        else:
            raise StopAsyncIteration

    def _handle_event(self, data_event: DataEvent) -> None:
        self.new_data.put_nowait(data_event)


@overload
def bind(target: Tuple[Bindable, str], *, readonly: Literal[True] = True) -> Bound:
    pass


@overload
def bind(target: Tuple[Bindable, str], *, readonly: Literal[False]) -> TwoWayBound:
    pass


def bind(target: Tuple[Bindable, str], *, readonly: bool = True) -> Any:
    (host, prop) = target
    return Binding(host, prop)
