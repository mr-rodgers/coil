import pytest

from coil import BindableValue, bindableclass
from coil.protocols import Bindable


@bindableclass
class Values:
    value: BindableValue[str]
    unannotated_value: int


def test_bindable_class_sets_descriptors() -> None:
    assert isinstance(Values.value, BindableValue)
    assert isinstance(Values.unannotated_value, BindableValue)


@pytest.fixture
def values() -> Values:
    return Values(value="foo", unannotated_value=100)


def test_bindable_obj_instance_values(values: Values) -> None:
    assert values.value == "foo"
    assert values.unannotated_value == 100


def test_bindable_obj_instance_is_bindable(values: Values) -> None:
    assert isinstance(values, Bindable)
