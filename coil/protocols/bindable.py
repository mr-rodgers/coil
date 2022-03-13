from typing import Dict, List, Protocol, Tuple, TypeAlias, runtime_checkable


from .data_event_handler import DataEventHandler, DataEvent  # type: ignore

# why is type: ignore needed ???


SubscriptionHandle: TypeAlias = Tuple[str, int]


@runtime_checkable
class Bindable(Protocol):
    """An object which can notify subscribers about changes to its
    properties.
    """

    @property
    def __coil_bindings__(self) -> Dict[str, List[DataEventHandler]]:
        """Return a mapping of subscribers"""


def add_subscription(
    bindable: Bindable, prop: str, handler: DataEventHandler
) -> SubscriptionHandle:
    """
    Add a subscription for the given property name.

    The subscription should track both updates and deletions
    for the given property. In addition, it should return a handle
    which can be used to drop the subscription later.
    """
    bindable.__coil_bindings__.setdefault(prop, []).append(handler)
    return (prop, id(handler))


def drop_subscription(bindable: Bindable, handle: SubscriptionHandle) -> None:
    """Remove a subscription from a bindable."""
    (prop_name, handler_id) = handle

    handlers = bindable.__coil_bindings__.get(prop_name, [])
    handler = next((h for h in handlers if id(h) == handler_id), None)

    if handler is not None:
        handlers.remove(handler)
    else:
        raise LookupError(f"Invalid subscription: {handle}")


def notify_subscribers(bindable: Bindable, prop: str, event: DataEvent) -> None:
    for receive in bindable.__coil_bindings__.get(prop, []):
        try:
            receive(event)
        except Exception:
            continue
