from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Generic, Literal, NamedTuple, TypeVar, overload

from coil.protocols._bound import Bound, TwoWayBound

from ._bindings import bind
from ._core import bound_attr_name, notify_subscribers, tail
from ._runtime import runtime
from .protocols import Bindable
from .types import DataDeletedEvent, DataUpdatedEvent

T = TypeVar("T", bound=type)
V = TypeVar("V")


TAIL_BINDING_TASK_ID = "_coil.tail"
REVERSE_TAIL_BINDING_TASK_ID = "_coil.reverse-tail"


def override_init(cls: T) -> None:
    old_init = cls.__init__  # type: ignore

    def __init__(obj: Bindable, *args: Any, **kwargs: Any) -> None:
        obj.__coil_bindings__ = {}  # type: ignore
        old_init(obj, *args, **kwargs)

    cls.__init__ = __init__  # type: ignore


def bindableclass(cls: T) -> T:
    """Decorate a class as :class:`coil.protocols.Bindable`.

    This enables to bind to the classes' declared properties
    using instances of this class (either using :func:`bind` or
    :meth:`BindableValue.bind`)::

        @bindableclass
        class Box:
            value: Any

    Classes generated by this decorator are also dataclasses.
    """
    data_cls: Any = dataclass(cls)
    override_init(data_cls)

    for field in fields(data_cls):
        setattr(data_cls, field.name, BindableValue(field.name))

    return data_cls  # type: ignore


class BindableValue(Generic[V]):
    """
    A descriptor which allows to track changes on a
    :class:`coil.protocols.Bindable`.

    You typically do not need to instantiate one of these
    yourself; classes decorated with :func:`bindableclass`
    will have all of their declared properties turned into
    one of these.

    These also provide an alternative syntax for creating
    data bindings::

        >>> @bindableclass
        ... class Box:
        ...     value: Any
        ...
        >>> box = Box(value=1)
        >>> bound_value = Box.value.bind(box)
        >>> bound_value.events()
        <BindingEventStream bindable=Box(value=1), prop='value'>
    """

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

    def __set__(self, obj: Bindable, value: V | Bound | TwoWayBound) -> None:
        if isinstance(value, (Bound, TwoWayBound)):
            self._assign_bound_value(obj, value)
        else:
            setattr(obj, self.private_name, value)
            notify_subscribers(
                obj,
                self.name,
                DataUpdatedEvent(
                    source_event=None,
                    value=value,
                    source=self._assignment_source(obj),
                ),
            )

    def __delete__(self, obj: Bindable) -> None:
        delattr(obj, self.private_name)
        notify_subscribers(
            obj,
            self.name,
            DataDeletedEvent(
                source_event=None, source=self._assignment_source(obj)
            ),
        )

    def _assign_bound_value(
        self, obj: Bindable, assigned_bound_value: Bound | TwoWayBound
    ) -> None:
        rt = runtime(ensure=False)
        self_bound_value = self.bind(obj, readonly=False)
        rt_source = (obj, self.name)

        # evict any previously existing tail tasks
        rt.evict(TAIL_BINDING_TASK_ID, source=rt_source)
        rt.evict(REVERSE_TAIL_BINDING_TASK_ID, source=rt_source)

        # if this is binding from and into the same property
        # important to do this after above evictions, because assigning a
        # self-bind is one way of clearing an ongoing binding task
        if (id(obj), self.name) == (
            id(assigned_bound_value.host),
            assigned_bound_value.prop,
        ):
            return

        # setup a tail task to copy changes from the assigned bound
        # value into the attribute controlled by the descriptor.
        tail_task = tail(assigned_bound_value, into=self_bound_value)
        rt.register(tail_task, TAIL_BINDING_TASK_ID, source=rt_source)

        if isinstance(assigned_bound_value, TwoWayBound):
            # tail task in opposite direction
            reverse_tail_task = tail(
                self_bound_value, into=assigned_bound_value
            )
            rt.register(
                reverse_tail_task,
                REVERSE_TAIL_BINDING_TASK_ID,
                source=rt_source,
            )

        # finally set the value to match the initial
        # bound value
        setattr(obj, self.name, assigned_bound_value.current)

    @overload
    def bind(self, obj: Bindable, *, readonly: Literal[True] = True) -> Bound:
        pass

    @overload
    def bind(self, obj: Bindable, *, readonly: Literal[False]) -> TwoWayBound:
        pass

    def bind(self, obj: Bindable, *, readonly: bool = True) -> Any:
        """Get a binding for this value on a given object.

        Short hand for
        :func:`bind((obj, attr), readonly=readonly) <coil.bind>`::

            from coil import bind, bindableclass

            @bindableclass
            class Box:
                value: Any

            box = Box(value="foo")

            # these are equivalent:
            bind((box, "value"))
            Box.value.bind(box) # this is more type safe

        """
        return bind((obj, self.name), readonly=readonly)  # type: ignore

    def clear_last_binding(self, *, assigned_to: Bindable) -> None:
        """Clear an an ongoing binding that was assigned to a bindable.

        If you've assigned a bound value to a binding
        target. That means changes to the bound value will be
        propagated to the binding target automatically in the background.
        This method provides a way to stop this process::

            @coil.bindableclass
            class Box:
                value: int

            async with coil.runtime():
                source = Box(10)
                target = Box(10)

                # changes to source.value will be reflected
                # into target.value
                target.value = Box.value.bind(source)

                # changes to source.value will no longer be
                # reflected into target.value
                Box.value.clear_last_binding(assigned_to=target)

        This function is a more readable shorthand for assigning
        a "self-bind" to the target::

            async with coil.runtime():
               source = Box(10)
                target = Box(10)

                # changes to source.value will be reflected
                # into target.value
                target.value = Box.value.bind(source)

                # changes to source.value will no longer be
                # reflected into target.value
                target.value = Box.value.bind(target)

        """
        self._assign_bound_value(assigned_to, self.bind(assigned_to))

    def _assignment_source(self, obj: Bindable) -> "Assignment":
        return Assignment(obj, self.name)

    @property
    def private_name(self) -> str:
        return bound_attr_name(self.name)


class Assignment(NamedTuple):
    host: Bindable
    prop: str

    @property
    def current(self) -> Any:
        return getattr(self.host, self.prop)
