from typing import Protocol

from ..types import DataEvent


class DataEventHandler(Protocol):
    """A data event handler callable"""

    def __call__(self, data_event: DataEvent) -> None:
        """Synchronously receive a notification."""
