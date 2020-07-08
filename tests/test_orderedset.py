import pytest

from marshmallow import orderedset


@pytest.mark.parametrize(
    ("method_name", "result"),
    [("intersection", {2, 3}), ("union", {1, 2, 3}), ("difference", {1})],
)
def test_methods(method_name, result):
    s = orderedset.OrderedSet([2, 1, 3])
    t = orderedset.OrderedSet([3, 2])

    assert getattr(s, method_name)(t) == result
