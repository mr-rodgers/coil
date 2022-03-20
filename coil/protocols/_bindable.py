from typing import Any, Dict, List, Protocol, runtime_checkable

from ._data_event_handler import DataEventHandler


@runtime_checkable
class Bindable(Protocol):
    """An object which can notify subscribers about changes to its
    properties.

    This protocol is implemented by any class that is decorated
    with :func:`bindableclass <coil.bindableclass>` (even though
    this currently fails mypy typecheck).
    """

    @property
    def __coil_bindings__(self) -> Dict[str, List[DataEventHandler]]:
        """Return a mapping of subscribers"""


class BindingTarget(Protocol):
    """A property that can be bound to."""

    @property
    def host(self) -> Bindable:
        """Return a host mapping to the bindable."""

    @property
    def prop(self) -> str:
        """The name of the property"""

    @property
    def current(self) -> Any:
        """Retrieve the current value of the binding target."""
        return getattr(self.host, self.prop)
