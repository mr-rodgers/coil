from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Generic, Literal, TypeVar, overload

from coil.protocols.bound import Bound, TwoWayBound

from .bindings import bind
from .protocols import Bindable, notify_subscribers
from .types.events import DataDeletedEvent, DataUpdatedEvent
from .utils import bound_attr_name

T = TypeVar("T", bound=type)
V = TypeVar("V")


def override_init(cls: T) -> None:
    old_init = cls.__init__  # type: ignore

    def __init__(obj: Bindable, *args: Any, **kwargs: Any) -> None:
        obj.__coil_bindings__ = {}  # type: ignore
        old_init(obj, *args, **kwargs)

    cls.__init__ = __init__  # type: ignore


def bindableclass(cls: T) -> T:
    data_cls: Any = dataclass(cls)
    override_init(data_cls)

    for field in fields(data_cls):
        setattr(data_cls, field.name, BindableValue(field.name))

    return data_cls  # type: ignore


class BindableValue(Generic[V]):
    def __init__(self, name: str):
        self.name = name

    def __set_name__(self, obj: Bindable, name: str) -> None:
        # use this to register mutation events on object
        self.name = name

    @overload
    def __get__(self, obj: None, owner: Any) -> BindableValue[V]:
        pass

    @overload
    def __get__(self, obj: object, owner: Any) -> V:
        pass

    def __get__(self, obj: Any, owner: Any) -> Any:
        if obj is None:
            return self

        # simply retrieve the value from the object
        return getattr(obj, self.private_name)

    def __set__(self, obj: Bindable, value: V) -> None:
        setattr(obj, self.private_name, value)
        notify_subscribers(
            obj, self.name, DataUpdatedEvent(source=None, value=value)
        )

    def __delete__(self, obj: Bindable) -> None:
        delattr(obj, self.private_name)
        notify_subscribers(obj, self.name, DataDeletedEvent(source=None))

    @overload
    def bind(self, obj: Bindable, *, readonly: Literal[True] = True) -> Bound:
        pass

    @overload
    def bind(self, obj: Bindable, *, readonly: Literal[False]) -> TwoWayBound:
        pass

    def bind(self, obj: Bindable, *, readonly: bool = True) -> Any:
        return bind((obj, self.name), readonly=readonly)  # type: ignore

    @property
    def private_name(self) -> str:
        return bound_attr_name(self.name)
