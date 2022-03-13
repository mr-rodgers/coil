from typing import Awaitable, Protocol

from ..types.events import DataEvent


class DataEventHandler(Protocol):
    """A data event handler callable"""

    def __call__(self, data_event: DataEvent) -> None:
        """Synchronously receive a notification."""
