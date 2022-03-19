import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterable, Literal, Tuple, overload

from ._core import (
    add_subscription,
    bound_attr_name,
    drop_subscription,
    notify_subscribers,
)
from .protocols import Bindable, Bound, TwoWayBound
from .types import (
    DataDeletedEvent,
    DataEvent,
    DataUpdatedEvent,
    is_update_event,
)


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

    def __repr__(self) -> str:
        return (
            "<BindingEventStream "
            f"bindable={repr(self.binding.host)}, "
            f"prop={repr(self.binding.prop)}>"
        )

    def _handle_event(self, data_event: DataEvent) -> None:
        self.new_data.put_nowait(data_event)


@overload
def bind(
    target: Tuple[Bindable, str], *, readonly: Literal[True] = True
) -> Bound:
    pass


@overload
def bind(
    target: Tuple[Bindable, str], *, readonly: Literal[False]
) -> TwoWayBound:
    pass


def bind(target: Tuple[Bindable, str], *, readonly: bool = True) -> Any:
    """Return a binding for the given target

    :param target: A tuple representing a :class:`protocols.Bindable`
      and attribute combination.
    :param readonly: Controls what you are able to do with the returned
      binding; this is `True` be default, meaning that the returned
      binding can only be used to watch for changes to the bound
      value. When this is set to `False`, the returned binding can also
      be used to set the bound value.
    """
    (host, prop) = target
    return Binding(host, prop)
