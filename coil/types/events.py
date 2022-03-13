from __future__ import annotations

from typing import Any, TypeAlias, TypedDict, Union, TypeGuard
from collections.abc import Mapping


class DataEvent(TypedDict):
    source: Any


class DataUpdatedEvent(DataEvent):
    value: Any


class DataDeletedEvent(DataEvent):
    pass


def is_data_event(obj: Any) -> TypeGuard[DataEvent]:
    """Check whether an object is a data event."""
    return isinstance(obj, Mapping) and {"source", "value"}.issuperset(obj.keys())


def is_delete_event(obj: Any) -> TypeGuard[DataDeletedEvent]:
    """Check whether an object is a DataDeletedEvent"""
    return isinstance(obj, Mapping) and {"source"} == set(obj.keys())


def is_update_event(obj: Any) -> TypeGuard[DataUpdatedEvent]:
    """Return whether an object is a DataUpdatedEvent"""
    return isinstance(obj, Mapping) and {"source", "value"} == set(obj.keys())
