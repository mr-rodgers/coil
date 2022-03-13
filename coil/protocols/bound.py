"""
Protocol for bound values.
"""

from typing import Any, AsyncIterable, Awaitable, Protocol

from ..types.events import DataEvent, DataUpdatedEvent


class Bound(Protocol):
    """An abstraction of bound readable values, able to provide a stream of updates."""

    def events(self) -> AsyncIterable[DataUpdatedEvent]:
        """Return an asynchronous stream representing bound values as they change.

        If the underlying value is destroyed, then the stream will be closed.
        """


class ReverseBound(Protocol):
    def set(self, value: Any, source: DataEvent | None = None) -> Awaitable[None]:
        """Push a value into the binding."""


class TwoWayBound(Bound, ReverseBound, Protocol):
    pass
