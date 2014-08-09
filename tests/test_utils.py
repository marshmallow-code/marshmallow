# -*- coding: utf-8 -*-
import datetime as dt
from collections import namedtuple

from marshmallow import utils
from tests.base import assert_datetime_equal, central


def test_to_marshallable_type():
    class Foo(object):
        CLASS_VAR = 'bar'

        def __init__(self):
            self.attribute = 'baz'

        @property
        def prop(self):
            return 42

    obj = Foo()
    u_dict = utils.to_marshallable_type(obj)
    assert u_dict['CLASS_VAR'] == Foo.CLASS_VAR
    assert u_dict['attribute'] == obj.attribute
    assert u_dict['prop'] == obj.prop

def test_to_marshallable_type_none():
    assert utils.to_marshallable_type(None) is None

def test_to_marshallable_type_with_namedtuple():
    Point = namedtuple('Point', ['x', 'y'])
    p = Point(24, 42)
    result = utils.to_marshallable_type(p)
    assert result['x'] == p.x
    assert result['y'] == p.y

def test_is_keyed_tuple():
    Point = namedtuple('Point', ['x', 'y'])
    p = Point(24, 42)
    assert utils.is_keyed_tuple(p) is True
    t = (24, 42)
    assert utils.is_keyed_tuple(t) is False
    d = {'x': 42, 'y': 24}
    assert utils.is_keyed_tuple(d) is False
    s = 'xy'
    assert utils.is_keyed_tuple(s) is False
    l = [24, 42]
    assert utils.is_keyed_tuple(l) is False

def test_to_marshallable_type_list():
    assert utils.to_marshallable_type(['foo', 'bar']) == ['foo', 'bar']

def test_to_marshallable_type_generator():
    gen = (e for e in ['foo', 'bar'])
    assert utils.to_marshallable_type(gen) == ['foo', 'bar']

def test_marshallable():
    class ObjContainer(object):
        contained = {"foo": 1}

        def __marshallable__(self):
            return self.contained

    obj = ObjContainer()
    assert utils.to_marshallable_type(obj) == {"foo": 1}

def test_is_collection():
    assert utils.is_collection([1, 'foo', {}]) is True
    assert utils.is_collection(('foo', 2.3)) is True
    assert utils.is_collection({'foo': 'bar'}) is False

def test_rfcformat_gmt_naive():
    d = dt.datetime(2013, 11, 10, 1, 23, 45)
    assert utils.rfcformat(d) == "Sun, 10 Nov 2013 01:23:45 -0000"

def test_rfcformat_central():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.rfcformat(d) == 'Sun, 10 Nov 2013 07:23:45 -0000'

def test_rfcformat_central_localized():
    d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
    assert utils.rfcformat(d, localtime=True) == "Sun, 10 Nov 2013 08:23:45 -0600"

def test_isoformat():
    d = dt.datetime(2013, 11, 10, 1, 23, 45)
    assert utils.isoformat(d) == '2013-11-10T01:23:45+00:00'

def test_isoformat_tzaware():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.isoformat(d) == "2013-11-10T07:23:45+00:00"

def test_isoformat_localtime():
    d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
    assert utils.isoformat(d, localtime=True) == "2013-11-10T01:23:45-06:00"

def test_from_rfc():
    d = dt.datetime.now()
    rfc = utils.rfcformat(d)
    output = utils.from_rfc(rfc)
    assert_datetime_equal(output, d)

def test_from_iso():
    d = dt.datetime.now()
    formatted = d.isoformat()
    assert_datetime_equal(utils.from_iso(formatted), d)

def test_from_iso_with_tz():
    d = central.localize(dt.datetime.now())
    formatted = d.isoformat()
    result = utils.from_iso(formatted)
    assert_datetime_equal(result, d)
    if utils.dateutil_available:
        # Note a naive datetime
        assert result.tzinfo is not None
