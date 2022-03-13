# coil

[Docs](https://mr-rodgers.github.io/coil/)

#### Usage

```python
from coil import bindableclass

@bindableclass
class Box:
    value: int


async def track_changes(box: Box) -> None:
    async for event in Box.value.bind(box).events():
        print(event["value"])

async def main() -> None:
    box: Box = ...
    task = create_task(track_changes(box))

    # run the application
    ...

    # cleanup the task
    task.cancel()
    await task
```
