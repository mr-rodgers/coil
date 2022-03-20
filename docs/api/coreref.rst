:mod:`coil` -- Core functions
=============================

The :mod:`coil` module contains most of what your need to use
coil.


.. py:module:: coil

.. autofunction:: bindableclass(cls: typing.Type[T]) -> typing.Type[T]

.. autofunction:: bind

.. autoclass:: BindableValue(...)

    .. automethod:: bind

.. autofunction:: runtime

.. autoclass:: Runtime
    :members: register, forget, find, evict
    :member-order: bysource
