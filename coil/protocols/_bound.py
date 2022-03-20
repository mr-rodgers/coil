"""
Protocol for bound values.
"""

from typing import Any, AsyncIterable, Awaitable, Protocol, runtime_checkable

from ..types import DataEvent, DataUpdatedEvent
from ._bindable import BindingTarget


@runtime_checkable
class Bound(BindingTarget, Protocol):
    """An abstraction of a readable bound value."""

    def events(self) -> AsyncIterable[DataUpdatedEvent]:
        """Return an asynchronous stream of value change events.

        If the underlying value is destroyed, then the stream will be closed.
        """


@runtime_checkable
class ReverseBound(Protocol):
    """An abstraction of a settable bound value."""

    def set(
        self, value: Any, source_event: DataEvent | None = None
    ) -> Awaitable[None]:
        """Push a value into the binding."""


@runtime_checkable
class TwoWayBound(Bound, ReverseBound, Protocol):
    """A combination of :class:`Bound` and :class:`ReverseBound`."""
