from __future__ import annotations

import datetime as dt
from collections import OrderedDict
from copy import copy, deepcopy
from types import MappingProxyType
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


# regression test for https://github.com/marshmallow-code/marshmallow/issues/648
@pytest.mark.parametrize("key", ["items", "keys", "values", "get"])
def test_get_value_from_dict_missing_method_named_key(key):
    # A key missing from a dict must not resolve to a method of the
    # dict type.
    assert utils.get_value({}, key) is utils.missing
    assert utils.get_value({}, key, default=123) == 123
    assert utils.get_value({"a": 1}, key, default=123) == 123


# regression test for https://github.com/marshmallow-code/marshmallow/issues/648
@pytest.mark.parametrize(
    "obj",
    [
        OrderedDict(a=1),
        MappingProxyType({"a": 1}),
    ],
)
def test_get_value_from_mapping_missing_method_named_key(obj):
    assert utils.get_value(obj, "a") == 1
    assert utils.get_value(obj, "items", default=123) == 123
    assert utils.get_value(obj, "get", default=123) == 123


def test_get_value_from_dict_subclass():
    class MyDict(dict):
        pass

    d = MyDict(a=1)
    assert utils.get_value(d, "a") == 1
    assert utils.get_value(d, "items", default=123) == 123


def test_get_value_from_dict_subclass_instance_attribute():
    # Attributes stored on the instance of a dict subclass are still
    # resolved when the key is missing (see PointDict above)...
    p = PointDict(24, 42)
    assert utils.get_value(p, "y") == 42
    # ...but methods of the dict type are not.
    assert utils.get_value(p, "items", default=123) == 123


def test_get_value_for_nested_dict_missing_key():
    d = {"p": {"x": 5}}
    assert utils.get_value(d, "p.x") == 5
    assert utils.get_value(d, "p.items", default=123) == 123


def test_get_value_key_error_from_non_mapping():
    # Objects that are not mappings keep the attribute fallback even
    # when __getitem__ raises KeyError.
    class KeyErrorObject:
        def __init__(self):
            self.x = 24

        def __getitem__(self, key):
            raise KeyError(key)

    assert utils.get_value(KeyErrorObject(), "x") == 24


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
    with pytest.raises(ValueError):
        utils.from_timestamp(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1676386740000, dt.datetime(2023, 2, 14, 14, 59, 00)),
        (1000, dt.datetime(1970, 1, 1, 0, 0, 1)),
    ],
)
def test_from_timestamp_ms(value, expected):
    result = utils.from_timestamp_ms(value)
    assert type(result) is dt.datetime
    assert result == expected


@pytest.mark.parametrize("value", [True, False])
def test_from_timestamp_ms_rejects_booleans(value):
    with pytest.raises(ValueError, match=r"Not a valid POSIX timestamp"):
        utils.from_timestamp_ms(value)


# Regression test for https://github.com/marshmallow-code/marshmallow/issues/540
def test_function_field_using_type_annotation():
    def get_split_words(value: str):
        return value.split(";")

    class MySchema(Schema):
        friends = fields.Function(deserialize=get_split_words)

    data = {"friends": "Clark;Alfred;Robin"}
    result = MySchema().load(data)
    assert result == {"friends": ["Clark", "Alfred", "Robin"]}
