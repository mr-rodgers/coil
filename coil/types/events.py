from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict, TypeGuard


class DataEvent(TypedDict):
    """A :class:`typed dict <typing.TypedDict>` representing
    a data-event generated from a bound value.

    :class:`DataUpdatedEvent` and :class:`DataDeletedEvent` are
    both variants of this.

    They are typically yielded from
    :meth:`protocols.Bound.events(...) <coil.protocols.Bound.events>`.

    Data events may provide the following fields:

    :source: this is always present, but may be :code:`None`. When present,
        it will point to another :class:`DataEvent` which this event was
        generated from inside.
    :value: this is only present in :class:`DataUpdatedEvent` dicts.


    It is important to bear in mind that these are dictionaries, and not
    objects. In other words, you can retrieve an event's source using
    :code:`event["source"]`, but not with :code:`event.source`.
    """

    source: Any


class DataUpdatedEvent(DataEvent):
    value: Any


class DataDeletedEvent(DataEvent):
    pass


def is_data_event(obj: Any) -> TypeGuard[DataEvent]:
    """Check whether an object is a data event."""
    return isinstance(obj, Mapping) and {"source", "value"}.issuperset(
        obj.keys()
    )


def is_delete_event(obj: Any) -> TypeGuard[DataDeletedEvent]:
    """Check whether an object is a DataDeletedEvent"""
    return isinstance(obj, Mapping) and {"source"} == set(obj.keys())


def is_update_event(obj: Any) -> TypeGuard[DataUpdatedEvent]:
    """Return whether an object is a DataUpdatedEvent"""
    return isinstance(obj, Mapping) and {"source", "value"} == set(obj.keys())
