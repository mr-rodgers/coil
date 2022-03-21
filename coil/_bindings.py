import asyncio
from logging import getLogger
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

LOG = getLogger("coil")


class Binding(Bound):
    def __init__(self, host: Bindable, prop: str) -> None:
        self.__host = host
        self.__prop = prop

    def events(self) -> AsyncIterable[DataUpdatedEvent]:
        return BindingEventStream(self)

    def __repr__(self) -> str:
        return f"Binding({repr(self.host)}, {repr(self.prop)})"

    @property
    def host(self) -> Bindable:
        return self.__host

    @property
    def prop(self) -> str:
        return self.__prop


class TwoWayBinding(Binding, TwoWayBound):
    async def set(
        self, value: Any, source_event: DataEvent | None = None
    ) -> None:
        setattr(self.host, bound_attr_name(self.prop), value)
        event = DataUpdatedEvent(
            source_event=source_event, value=value, source=self
        )
        notify_subscribers(self.host, self.prop, event)

    async def unset(self, source_event: DataEvent | None = None) -> None:
        delattr(self.host, bound_attr_name(self.prop))
        event = DataDeletedEvent(source_event=source_event, source=self)
        notify_subscribers(self.host, self.prop, event)


class BindingEventStream:
    binding: Binding

    def __init__(self, binding: Binding):
        self.binding = binding
        self.new_data = asyncio.Queue[DataEvent]()
        self.subsciption_handle = add_subscription(
            binding.host, binding.prop, self._handle_event
        )
        LOG.debug(f"initialized binding event stream: {self}")

    def __del__(self) -> None:
        LOG.debug(f"finalizing binding event stream: {self}")
        drop_subscription(self.binding.host, self.subsciption_handle)

    def __aiter__(self) -> Any:
        return self

    async def __anext__(self) -> DataUpdatedEvent:
        LOG.debug("getting next event from queue")
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
        LOG.debug("pushing next event into queue")
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

    Args:
        target (coil.protocols.Bindable): A tuple representing a
            [`protocols.Bindable`][coil.protocols.Bindable]
            and attribute combination.
        readonly: Controls what you are able to do with the returned
                  binding; this is `True` be default, meaning that the returned
                  binding can only be used to watch for changes to the bound
                  value. When this is set to `False`, the returned binding can
                  also be used to set the bound value.
    """
    (host, prop) = target
    return Binding(host, prop) if readonly else TwoWayBinding(host, prop)
