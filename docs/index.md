# Getting Started

coil provides data bindings for Python 3.10+ asyncio applications. With
data bindings, you are able to write applications which react to changes
in an application's state, by "binding" properties from one component
onto another.

## Usage

coil allows data bindings through a special type of class that is able
to record changes to its properties. coil's included
[`@bindableclass`][coil.bindableclass]
decorator can be used to declare such a class:

```python
from coil import bindableclass

@bindableclass
class Window:
    width: int
    height: int
```

When a class is decorated like this, you can bind to its declared properties,
receiving notifications about changes to this property through an asyncio
event stream:

```python
from asyncio import create_task

from coil import bind

async def track_window_changes(window: Window) -> None:
    async for event in bind((window, "width")).events():
        print(event["value"])

async def main() -> None:
    window: Window = ...
    task = create_task(track_window_changes(window))

    # run the application
    ...

    # cleanup the task
    task.cancel()
    await task
```

Do be aware that the async iterator returned from
[`Bound.events()`][coil.protocols.Bound.events] will run
indefinitely (or, until the bound value is deleted). For this reason,
this stream should be consumed _in parallel_ to application code.

## Capabilities

- Generate asynchronous [`event streams`][coil.protocols.Bound.events]
  from changes made to a [`bound value`][coil.bind] over time.
- Chain binding properties together, by tailing changes from one property into
  another.
- Bidirectional data binding

## Roadmap

- Composite bindings
- Bindings using a callback function (smart enough to track which props they access, and
  refire when any of those previously accessed props changed)
