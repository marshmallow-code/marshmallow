# -*- coding: utf-8 -*-
import datetime as dt
from collections import namedtuple
from functools import partial

import pytest

from marshmallow.exceptions import ValidationError
from marshmallow import utils
from tests.base import (
    assert_datetime_equal,
    central,
    assert_time_equal,
    assert_date_equal,
)


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

PointNT = namedtuple('Point', ['x', 'y'])

def test_to_marshallable_type_with_namedtuple():
    p = PointNT(24, 42)
    result = utils.to_marshallable_type(p)
    assert result['x'] == p.x
    assert result['y'] == p.y

class PointClass(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

@pytest.mark.parametrize('obj', [
    PointNT(24, 42),
    PointClass(24, 42),
    {'x': 24, 'y': 42}
])
def test_get_value(obj):
    result = utils.get_value('x', obj)
    assert result == 24
    result2 = utils.get_value('y', obj)
    assert result2 == 42

def test_get_value_from_namedtuple_with_default():
    p = PointNT(x=42, y=None)
    # Default is only returned if key is not found
    assert utils.get_value('z', p, default=123) == 123
    # since 'y' is an attribute, None is returned instead of the default
    assert utils.get_value('y', p, default=123) is None

class Triangle(object):
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.points = [p1, p2, p3]

def test_get_value_for_nested_object():
    tri = Triangle(p1=PointClass(1, 2), p2=PointNT(3, 4), p3={'x': 5, 'y': 6})
    assert utils.get_value('p1.x', tri) == 1
    assert utils.get_value('p2.x', tri) == 3
    assert utils.get_value('p3.x', tri) == 5

# regression test for https://github.com/marshmallow-code/marshmallow/issues/62
def test_get_value_from_dict():
    d = dict(items=['foo', 'bar'], keys=['baz', 'quux'])
    assert utils.get_value('items', d) == ['foo', 'bar']
    assert utils.get_value('keys', d) == ['baz', 'quux']

def test_get_value():
    l = [1,2,3]
    assert utils.get_value(1, l) == 2

    class MyInt(int):
        pass

    assert utils.get_value(MyInt(1), l) == 2

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

def test_from_datestring():
    d = dt.datetime.now()
    rfc = utils.rfcformat(d)
    iso = d.isoformat()
    assert_date_equal(utils.from_datestring(rfc), d)
    assert_date_equal(utils.from_datestring(iso), d)

@pytest.mark.parametrize('use_dateutil', [True, False])
def test_from_rfc(use_dateutil):
    d = dt.datetime.now()
    rfc = utils.rfcformat(d)
    result = utils.from_rfc(rfc, use_dateutil=use_dateutil)
    assert type(result) == dt.datetime
    assert_datetime_equal(result, d)

@pytest.mark.parametrize('use_dateutil', [True, False])
def test_from_iso(use_dateutil):
    d = dt.datetime.now()
    formatted = d.isoformat()
    result = utils.from_iso(formatted, use_dateutil=use_dateutil)
    assert type(result) == dt.datetime
    assert_datetime_equal(result, d)

def test_from_iso_with_tz():
    d = central.localize(dt.datetime.now())
    formatted = d.isoformat()
    result = utils.from_iso(formatted)
    assert_datetime_equal(result, d)
    if utils.dateutil_available:
        # Note a naive datetime
        assert result.tzinfo is not None

# Test with and without dateutil
@pytest.mark.parametrize('use_dateutil', [True, False])
def test_from_iso_time_with_microseconds(use_dateutil):
    t = dt.time(1, 23, 45, 6789)
    formatted = t.isoformat()
    result = utils.from_iso_time(formatted, use_dateutil=use_dateutil)
    assert type(result) == dt.time
    assert_time_equal(result, t, microseconds=True)

@pytest.mark.parametrize('use_dateutil', [True, False])
def test_from_iso_time_without_microseconds(use_dateutil):
    t = dt.time(1, 23, 45)
    formatted = t.isoformat()
    result = utils.from_iso_time(formatted, use_dateutil=use_dateutil)
    assert type(result) == dt.time
    assert_time_equal(result, t, microseconds=True)

@pytest.mark.parametrize('use_dateutil', [True, False])
def test_from_iso_date(use_dateutil):
    d = dt.date(2014, 8, 21)
    iso_date = d.isoformat()
    result = utils.from_iso_date(iso_date, use_dateutil=use_dateutil)
    assert type(result) == dt.date
    assert_date_equal(result, d)

def test_get_func_args():
    def f1(self, foo, bar):
        pass

    f2 = partial(f1, 'baz')

    class F3(object):
        def __call__(self, foo, bar):
            pass
    f3 = F3()

    for func in [f1, f2, f3]:
        assert utils.get_func_args(func) == ['self', 'foo', 'bar']


CustomError = namedtuple('CustomError', ['code', 'message'])

class TestMergeErrors:

    def test_merging_none_and_string(self):
        assert 'error1' == utils.merge_errors(None, 'error1')

    def test_merging_none_and_custom_error(self):
        assert CustomError(123, 'error1') == \
            utils.merge_errors(None, CustomError(123, 'error1'))

    def test_merging_none_and_list(self):
        assert ['error1', 'error2'] == \
            utils.merge_errors(None, ['error1', 'error2'])

    def test_merging_none_and_dict(self):
        assert {'field1': 'error1'} == \
            utils.merge_errors(None, {'field1': 'error1'})

    def test_merging_string_and_none(self):
        assert 'error1' == utils.merge_errors('error1', None)

    def test_merging_custom_error_and_none(self):
        assert CustomError(123, 'error1') == \
            utils.merge_errors(CustomError(123, 'error1'), None)

    def test_merging_list_and_none(self):
        assert ['error1', 'error2'] == \
            utils.merge_errors(['error1', 'error2'], None)

    def test_merging_dict_and_none(self):
        assert {'field1': 'error1'} == \
            utils.merge_errors({'field1': 'error1'}, None)

    def test_merging_string_and_string(self):
        assert ['error1', 'error2'] == utils.merge_errors('error1', 'error2')

    def test_merging_custom_error_and_string(self):
        assert [CustomError(123, 'error1'), 'error2'] == \
            utils.merge_errors(CustomError(123, 'error1'), 'error2')

    def test_merging_string_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == \
            utils.merge_errors('error1', CustomError(123, 'error2'))

    def test_merging_custom_error_and_custom_error(self):
        assert [CustomError(123, 'error1'), CustomError(456, 'error2')] == \
            utils.merge_errors(CustomError(123, 'error1'),
                               CustomError(456, 'error2'))

    def test_merging_string_and_list(self):
        assert ['error1', 'error2'] == utils.merge_errors('error1', ['error2'])

    def test_merging_string_and_dict(self):
        assert {'_schema': 'error1', 'field1': 'error2'} == \
            utils.merge_errors('error1', {'field1': 'error2'})

    def test_merging_string_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == \
            utils.merge_errors('error1', {'_schema': 'error2', 'field1': 'error3'})

    def test_merging_custom_error_and_list(self):
        assert [CustomError(123, 'error1'), 'error2'] == \
            utils.merge_errors(CustomError(123, 'error1'), ['error2'])

    def test_merging_custom_error_and_dict(self):
        assert {'_schema': CustomError(123, 'error1'), 'field1': 'error2'} == \
            utils.merge_errors(CustomError(123, 'error1'), {'field1': 'error2'})

    def test_merging_custom_error_and_dict_with_schema_error(self):
        assert {'_schema': [CustomError(123, 'error1'), 'error2'],
                'field1': 'error3'} == \
            utils.merge_errors(CustomError(123, 'error1'),
                               {'_schema': 'error2', 'field1': 'error3'})

    def test_merging_list_and_string(self):
        assert ['error1', 'error2'] == utils.merge_errors(['error1'], 'error2')

    def test_merging_list_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == \
            utils.merge_errors(['error1'], CustomError(123, 'error2'))

    def test_merging_list_and_list(self):
        assert ['error1', 'error2'] == utils.merge_errors(['error1'], ['error2'])

    def test_merging_list_and_dict(self):
        assert {'_schema': ['error1'], 'field1': 'error2'} == \
            utils.merge_errors(['error1'], {'field1': 'error2'})

    def test_merging_list_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == \
            utils.merge_errors(['error1'], {'_schema': 'error2',
                                            'field1': 'error3'})

    def test_merging_dict_and_string(self):
        assert {'_schema': 'error2', 'field1': 'error1'} == \
            utils.merge_errors({'field1': 'error1'}, 'error2')

    def test_merging_dict_and_custom_error(self):
        assert {'_schema': CustomError(123, 'error2'), 'field1': 'error1'} == \
            utils.merge_errors({'field1': 'error1'}, CustomError(123, 'error2'))

    def test_merging_dict_and_list(self):
        assert {'_schema': ['error2'], 'field1': 'error1'} == \
            utils.merge_errors({'field1': 'error1'}, ['error2'])

    def test_merging_dict_and_dict(self):
        assert {'field1': 'error1',
                'field2': ['error2', 'error3'],
                'field3': 'error4'} == \
            utils.merge_errors({'field1': 'error1', 'field2': 'error2'},
                               {'field2': 'error3', 'field3': 'error4'})

    def test_deep_merging_dicts(self):
        assert {'field1': {'field2': ['error1', 'error2']}} == \
            utils.merge_errors({'field1': {'field2': 'error1'}},
                               {'field1': {'field2': 'error2'}})


class TestValidationErrorBuilder:

    def test_empty_errors(self):
        builder = utils.ValidationErrorBuilder()
        assert {} == builder.errors

    def test_adding_field_error(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        assert {'foo': 'error 1'} == builder.errors

    def test_adding_multiple_errors(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        builder.add_error('bar', 'error 2')
        builder.add_error('bam', 'error 3')
        assert {'foo': 'error 1', 'bar': 'error 2', 'bam': 'error 3'} == \
            builder.errors

    def test_adding_nested_errors(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error('foo.bar', 'error 1')
        assert {'foo': {'bar': 'error 1'}} == builder.errors

    def test_adding_multiple_nested_errors_described_with_string_path(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error('foo.bar', 'error 1')
        builder.add_error('foo.baz.bam', 'error 2')
        builder.add_error('quux', 'error 3')
        assert {'foo': {'bar': 'error 1', 'baz': {'bam': 'error 2'}},
                'quux': 'error 3'} == builder.errors

    def test_adding_multiple_nested_errors_described_with_list(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error(['foo', 'bar'], 'error 1')
        builder.add_error(['foo', 'baz', 'bam'], 'error 2')
        builder.add_error('quux', 'error 3')
        assert {'foo': {'bar': 'error 1', 'baz': {'bam': 'error 2'}},
                'quux': 'error 3'} == builder.errors

    def test_adding_merging_errors(self):
        builder = utils.ValidationErrorBuilder()
        builder.merge_errors({'foo': {'bar': 'error 1'}})
        builder.merge_errors({'foo': {'baz': 'error 2'}})
        assert {'foo': {'bar': 'error 1', 'baz': 'error 2'}} == builder.errors

    def test_raise_errors_on_empty_builder_does_nothing(self):
        builder = utils.ValidationErrorBuilder()
        builder.raise_errors()

    def test_raise_errors_on_non_empty_builder_raises_ValidationError(self):
        builder = utils.ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        with pytest.raises(ValidationError) as excinfo:
            builder.raise_errors()

        assert excinfo.value.messages == builder.errors
