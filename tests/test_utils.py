import datetime as dt
from collections import namedtuple
from functools import partial
from copy import copy, deepcopy

import pytest

from marshmallow import utils, fields, Schema
from tests.base import (
    assert_datetime_equal,
    central,
    assert_time_equal,
    assert_date_equal,
)


def test_missing_singleton_copy():
    assert copy(utils.missing) is utils.missing
    assert deepcopy(utils.missing) is utils.missing


PointNT = namedtuple("Point", ["x", "y"])


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
    d = {}
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


def test_is_keyed_tuple():
    Point = namedtuple("Point", ["x", "y"])
    p = Point(24, 42)
    assert utils.is_keyed_tuple(p) is True
    t = (24, 42)
    assert utils.is_keyed_tuple(t) is False
    d = {"x": 42, "y": 24}
    assert utils.is_keyed_tuple(d) is False
    s = "xy"
    assert utils.is_keyed_tuple(s) is False
    lst = [24, 42]
    assert utils.is_keyed_tuple(lst) is False


def test_is_collection():
    assert utils.is_collection([1, "foo", {}]) is True
    assert utils.is_collection(("foo", 2.3)) is True
    assert utils.is_collection({"foo": "bar"}) is False


def test_rfcformat_gmt_naive():
    d = dt.datetime(2013, 11, 10, 1, 23, 45)
    assert utils.rfcformat(d) == "Sun, 10 Nov 2013 01:23:45 -0000"


def test_rfcformat_central():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.rfcformat(d) == "Sun, 10 Nov 2013 07:23:45 -0000"


def test_rfcformat_naive_localized():
    d = dt.datetime(2013, 11, 10, 1, 23, 45)
    assert utils.rfcformat(d, localtime=True) == "Sun, 10 Nov 2013 01:23:45 +0000"


def test_rfcformat_central_localized():
    d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
    assert utils.rfcformat(d, localtime=True) == "Sun, 10 Nov 2013 08:23:45 -0600"


def test_isoformat():
    d = dt.datetime(2013, 11, 10, 1, 23, 45)
    assert utils.isoformat(d) == "2013-11-10T01:23:45+00:00"


def test_isoformat_tzaware():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.isoformat(d) == "2013-11-10T07:23:45+00:00"


def test_isoformat_localtime():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.isoformat(d, localtime=True) == "2013-11-10T01:23:45-06:00"


def test_from_rfc():
    d = dt.datetime.now().replace(microsecond=0)
    rfc = utils.rfcformat(d)
    result = utils.from_rfc(rfc)
    assert type(result) == dt.datetime
    assert_datetime_equal(result, d)


@pytest.mark.parametrize("timezone", [None, central])
def test_from_iso_datetime(timezone):
    d = dt.datetime.now(tz=timezone)
    formatted = d.isoformat()
    result = utils.from_iso_datetime(formatted)
    assert type(result) == dt.datetime
    assert_datetime_equal(result, d)

    # Test with 3-digit only microseconds
    #  Regression test for https://github.com/marshmallow-code/marshmallow/issues/1251
    d = dt.datetime.now(tz=timezone).replace(microsecond=123000)
    formatted = d.isoformat()
    formatted = formatted[:23] + formatted[26:]
    result = utils.from_iso_datetime(formatted)
    assert type(result) == dt.datetime
    assert_datetime_equal(result, d)


def test_from_iso_with_tz():
    d = central.localize(dt.datetime.now())
    formatted = d.isoformat()
    result = utils.from_iso_datetime(formatted)
    assert_datetime_equal(result, d)
    assert result.tzinfo is not None


def test_from_iso_time_with_microseconds():
    t = dt.time(1, 23, 45, 6789)
    formatted = t.isoformat()
    result = utils.from_iso_time(formatted)
    assert type(result) == dt.time
    assert_time_equal(result, t)


def test_from_iso_time_without_microseconds():
    t = dt.time(1, 23, 45)
    formatted = t.isoformat()
    result = utils.from_iso_time(formatted)
    assert type(result) == dt.time
    assert_time_equal(result, t)


def test_from_iso_date():
    d = dt.date(2014, 8, 21)
    iso_date = d.isoformat()
    result = utils.from_iso_date(iso_date)
    assert type(result) == dt.date
    assert_date_equal(result, d)


def test_get_func_args():
    def f1(foo, bar):
        pass

    f2 = partial(f1, "baz")

    class F3:
        def __call__(self, foo, bar):
            pass

    f3 = F3()

    for func in [f1, f2, f3]:
        assert utils.get_func_args(func) == ["foo", "bar"]


# Regression test for https://github.com/marshmallow-code/marshmallow/issues/540
def test_function_field_using_type_annotation():
    def get_split_words(value: str):  # noqa
        return value.split(";")

    class MySchema(Schema):
        friends = fields.Function(deserialize=get_split_words)

    data = {"friends": "Clark;Alfred;Robin"}
    result = MySchema().load(data)
    assert result == {"friends": ["Clark", "Alfred", "Robin"]}
