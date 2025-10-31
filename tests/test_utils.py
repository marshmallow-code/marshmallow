from __future__ import annotations

import datetime as dt
from copy import copy, deepcopy
from typing import NamedTuple

import pytest

from marshmallow import Schema, fields, utils


def test_missing_singleton_copy():
    assert copy(utils.missing) is utils.missing
    assert deepcopy(utils.missing) is utils.missing


class PointNT(NamedTuple):
    x: int | None
    y: int | None


class PointClass:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class PointDict(dict):
    def __init__(self, x, y):
        super().__init__({"x": x})
        self.y = y


@pytest.mark.parametrize(
    "obj", [PointNT(24, 42), PointClass(24, 42), PointDict(24, 42), {"x": 24, "y": 42}]
)
def test_get_value_from_object(obj):
    assert utils.get_value(obj, "x") == 24
    assert utils.get_value(obj, "y") == 42


def test_get_value_from_namedtuple_with_default():
    p = PointNT(x=42, y=None)
    # Default is only returned if key is not found
    assert utils.get_value(p, "z", default=123) == 123
    # since 'y' is an attribute, None is returned instead of the default
    assert utils.get_value(p, "y", default=123) is None


class Triangle:
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.points = [p1, p2, p3]


def test_get_value_for_nested_object():
    tri = Triangle(p1=PointClass(1, 2), p2=PointNT(3, 4), p3={"x": 5, "y": 6})
    assert utils.get_value(tri, "p1.x") == 1
    assert utils.get_value(tri, "p2.x") == 3
    assert utils.get_value(tri, "p3.x") == 5


# regression test for https://github.com/marshmallow-code/marshmallow/issues/62
def test_get_value_from_dict():
    d = dict(items=["foo", "bar"], keys=["baz", "quux"])
    assert utils.get_value(d, "items") == ["foo", "bar"]
    assert utils.get_value(d, "keys") == ["baz", "quux"]


def test_get_value():
    lst = [1, 2, 3]
    assert utils.get_value(lst, 1) == 2

    class MyInt(int):
        pass

    assert utils.get_value(lst, MyInt(1)) == 2


def test_set_value():
    d: dict[str, int | dict] = {}
    utils.set_value(d, "foo", 42)
    assert d == {"foo": 42}

    d = {}
    utils.set_value(d, "foo.bar", 42)
    assert d == {"foo": {"bar": 42}}

    d = {"foo": {}}
    utils.set_value(d, "foo.bar", 42)
    assert d == {"foo": {"bar": 42}}

    d = {"foo": 42}
    with pytest.raises(ValueError):
        utils.set_value(d, "foo.bar", 42)


def test_is_collection():
    assert utils.is_collection([1, "foo", {}]) is True
    assert utils.is_collection(("foo", 2.3)) is True
    assert utils.is_collection({"foo": "bar"}) is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1676386740, dt.datetime(2023, 2, 14, 14, 59, 00)),
        (1676386740.58, dt.datetime(2023, 2, 14, 14, 59, 00, 580000)),
    ],
)
def test_from_timestamp(value, expected):
    result = utils.from_timestamp(value)
    assert type(result) is dt.datetime
    assert result == expected


def test_from_timestamp_with_negative_value():
    value = -10
    with pytest.raises(ValueError, match=r"Not a valid POSIX timestamp"):
        utils.from_timestamp(value)


def test_from_timestamp_with_overflow_value():
    value = 9223372036854775
    with pytest.raises(ValueError, match=r"out of range|year must be in 1\.\.9999"):
        utils.from_timestamp(value)


# Regression test for https://github.com/marshmallow-code/marshmallow/issues/540
def test_function_field_using_type_annotation():
    def get_split_words(value: str):
        return value.split(";")

    class MySchema(Schema):
        friends = fields.Function(deserialize=get_split_words)

    data = {"friends": "Clark;Alfred;Robin"}
    result = MySchema().load(data)
    assert result == {"friends": ["Clark", "Alfred", "Robin"]}
