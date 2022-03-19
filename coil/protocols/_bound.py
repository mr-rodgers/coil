"""
Protocol for bound values.
"""

from typing import Any, AsyncIterable, Awaitable, Protocol

from ..types.events import DataEvent, DataUpdatedEvent


class Bound(Protocol):
    """An abstraction of a readable bound value."""

    def events(self) -> AsyncIterable[DataUpdatedEvent]:
        """Return an asynchronous stream of value change events.

        If the underlying value is destroyed, then the stream will be closed.
        """


class ReverseBound(Protocol):
    """An abstraction of a settable bound value."""

    def set(
        self, value: Any, source: DataEvent | None = None
    ) -> Awaitable[None]:
        """Push a value into the binding."""


class TwoWayBound(Bound, ReverseBound, Protocol):
    """A combination of :class:`Bound` and :class:`ReverseBound`."""

    pass
