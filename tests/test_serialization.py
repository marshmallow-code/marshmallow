# -*- coding: utf-8 -*-
"""Tests for field serialization."""
from collections import namedtuple
import datetime as dt
import decimal

import pytest

from marshmallow import Schema, fields, utils
from marshmallow.exceptions import ValidationError
from marshmallow.compat import basestring, OrderedDict

from tests.base import User, DummyModel, ALL_FIELDS

class DateTimeList:
    def __init__(self, dtimes):
        self.dtimes = dtimes

class IntegerList:
    def __init__(self, ints):
        self.ints = ints

class TestFieldSerialization:

    @pytest.fixture
    def user(self):
        return User("Foo", email="foo@bar.com", age=42)

    def test_default(self, user):
        field = fields.Field(default='nan')
        assert field.serialize('age', {}) == 'nan'

    @pytest.mark.parametrize(('value', 'expected'),
    [
        (42, float(42)),
        (0, float(0)),
        (None, None),
    ])
    def test_number(self, value, expected, user):
        field = fields.Number()
        user.age = value
        assert field.serialize('age', user) == expected

    def test_number_as_string(self, user):
        user.age = 42
        field = fields.Number(as_string=True)
        assert field.serialize('age', user) == str(float(user.age))

    def test_number_as_string_passed_none(self, user):
        user.age = None
        field = fields.Number(as_string=True, allow_none=True)
        assert field.serialize('age', user) is None

    def test_callable_default(self, user):
        field = fields.Field(default=lambda: 'nan')
        assert field.serialize('age', {}) == 'nan'

    def test_function_field(self, user):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", user)

    def test_function_field_passed_uncallable_object(self):
        with pytest.raises(ValueError):
            fields.Function('uncallable')

    def test_integer_field(self, user):
        field = fields.Integer()
        assert field.serialize('age', user) == 42

    def test_integer_as_string_field(self, user):
        field = fields.Integer(as_string=True)
        assert field.serialize('age', user) == '42'

    def test_integer_field_default(self, user):
        user.age = None
        field = fields.Integer(default=0)
        assert field.serialize('age', user) is None
        # missing
        assert field.serialize('age', {}) == 0

    def test_integer_field_default_set_to_none(self, user):
        user.age = None
        field = fields.Integer(default=None)
        assert field.serialize('age', user) is None

    def test_callable_field(self, user):
       field = fields.String()
       assert field.serialize('call_me', user) == 'This was called.'

    def test_decimal_field(self, user):
        user.m1 = 12
        user.m2 = '12.355'
        user.m3 = decimal.Decimal(1)
        user.m4 = None
        user.m5 = 'abc'
        user.m6 = [1, 2]

        field = fields.Decimal()
        assert isinstance(field.serialize('m1', user), decimal.Decimal)
        assert field.serialize('m1', user) == decimal.Decimal(12)
        assert isinstance(field.serialize('m2', user), decimal.Decimal)
        assert field.serialize('m2', user) == decimal.Decimal('12.355')
        assert isinstance(field.serialize('m3', user), decimal.Decimal)
        assert field.serialize('m3', user) == decimal.Decimal(1)
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

        field = fields.Decimal(1)
        assert isinstance(field.serialize('m1', user), decimal.Decimal)
        assert field.serialize('m1', user) == decimal.Decimal(12)
        assert isinstance(field.serialize('m2', user), decimal.Decimal)
        assert field.serialize('m2', user) == decimal.Decimal('12.4')
        assert isinstance(field.serialize('m3', user), decimal.Decimal)
        assert field.serialize('m3', user) == decimal.Decimal(1)
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.serialize('m1', user), decimal.Decimal)
        assert field.serialize('m1', user) == decimal.Decimal(12)
        assert isinstance(field.serialize('m2', user), decimal.Decimal)
        assert field.serialize('m2', user) == decimal.Decimal('12.3')
        assert isinstance(field.serialize('m3', user), decimal.Decimal)
        assert field.serialize('m3', user) == decimal.Decimal(1)
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

    def test_decimal_field_string(self, user):
        user.m1 = 12
        user.m2 = '12.355'
        user.m3 = decimal.Decimal(1)
        user.m4 = None
        user.m5 = 'abc'
        user.m6 = [1, 2]

        field = fields.Decimal(as_string=True)
        assert isinstance(field.serialize('m1', user), basestring)
        assert field.serialize('m1', user) == '12'
        assert isinstance(field.serialize('m2', user), basestring)
        assert field.serialize('m2', user) == '12.355'
        assert isinstance(field.serialize('m3', user), basestring)
        assert field.serialize('m3', user) == '1'
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

        field = fields.Decimal(1, as_string=True)
        assert isinstance(field.serialize('m1', user), basestring)
        assert field.serialize('m1', user) == '12.0'
        assert isinstance(field.serialize('m2', user), basestring)
        assert field.serialize('m2', user) == '12.4'
        assert isinstance(field.serialize('m3', user), basestring)
        assert field.serialize('m3', user) == '1.0'
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

        field = fields.Decimal(1, decimal.ROUND_DOWN, as_string=True)
        assert isinstance(field.serialize('m1', user), basestring)
        assert field.serialize('m1', user) == '12.0'
        assert isinstance(field.serialize('m2', user), basestring)
        assert field.serialize('m2', user) == '12.3'
        assert isinstance(field.serialize('m3', user), basestring)
        assert field.serialize('m3', user) == '1.0'
        assert field.serialize('m4', user) is None
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

    def test_decimal_field_special_values(self, user):
        user.m1 = '-NaN'
        user.m2 = 'NaN'
        user.m3 = '-sNaN'
        user.m4 = 'sNaN'
        user.m5 = '-Infinity'
        user.m6 = 'Infinity'
        user.m7 = '-0'

        field = fields.Decimal(places=2, allow_nan=True)

        m1s = field.serialize('m1', user)
        assert isinstance(m1s, decimal.Decimal)
        assert m1s.is_qnan() and not m1s.is_signed()

        m2s = field.serialize('m2', user)
        assert isinstance(m2s, decimal.Decimal)
        assert m2s.is_qnan() and not m2s.is_signed()

        m3s = field.serialize('m3', user)
        assert isinstance(m3s, decimal.Decimal)
        assert m3s.is_qnan() and not m3s.is_signed()

        m4s = field.serialize('m4', user)
        assert isinstance(m4s, decimal.Decimal)
        assert m4s.is_qnan() and not m4s.is_signed()

        m5s = field.serialize('m5', user)
        assert isinstance(m5s, decimal.Decimal)
        assert m5s.is_infinite() and m5s.is_signed()

        m6s = field.serialize('m6', user)
        assert isinstance(m6s, decimal.Decimal)
        assert m6s.is_infinite() and not m6s.is_signed()

        m7s = field.serialize('m7', user)
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero() and m7s.is_signed()

    def test_decimal_field_special_values_not_permitted(self, user):
        user.m1 = '-NaN'
        user.m2 = 'NaN'
        user.m3 = '-sNaN'
        user.m4 = 'sNaN'
        user.m5 = '-Infinity'
        user.m6 = 'Infinity'
        user.m7 = '-0'

        field = fields.Decimal(places=2)

        with pytest.raises(ValidationError):
            field.serialize('m1', user)
        with pytest.raises(ValidationError):
            field.serialize('m2', user)
        with pytest.raises(ValidationError):
            field.serialize('m3', user)
        with pytest.raises(ValidationError):
            field.serialize('m4', user)
        with pytest.raises(ValidationError):
            field.serialize('m5', user)
        with pytest.raises(ValidationError):
            field.serialize('m6', user)

        m7s = field.serialize('m7', user)
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero() and m7s.is_signed()

    def test_boolean_field_serialization(self, user):
        field = fields.Boolean()

        user.truthy = 'non-falsy-ish'
        user.falsy = 'false'
        user.none = None

        assert field.serialize('truthy', user) == True
        assert field.serialize('falsy', user) == False
        assert field.serialize('none', user) == None

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_email_field_validates(self, user):
        user.email = 'bademail'
        field = fields.Email()
        with pytest.raises(ValidationError):
            field.serialize('email', user)

    def test_email_field_serialize_none(self, user):
        user.email = None
        field = fields.Email()
        assert field.serialize('email', user) is None

    def test_dict_field_serialize_none(self, user):
        user.various_data = None
        field = fields.Dict()
        assert field.serialize('various_data', user) is None

    def test_dict_field_invalid_dict_but_okay(self, user):
        user.various_data = 'okaydict'
        field = fields.Dict()
        field.serialize('various_data', user)
        assert field.serialize('various_data', user) == 'okaydict'

    def test_dict_field_serialize(self, user):
        user.various_data = {"foo": "bar"}
        field = fields.Dict()
        assert field.serialize('various_data', user) == {"foo": "bar"}

    def test_dict_field_serialize_ordereddict(self, user):
        user.various_data = OrderedDict([("foo", "bar"), ("bar", "baz")])
        field = fields.Dict()
        assert field.serialize('various_data', user) == \
            OrderedDict([("foo", "bar"), ("bar", "baz")])

    def test_url_field_serialize_none(self, user):
        user.homepage = None
        field = fields.Url()
        assert field.serialize('homepage', user) is None

    def test_url_field_validates(self, user):
        user.homepage = 'badhomepage'
        field = fields.URL()
        with pytest.raises(ValidationError):
            field.serialize('homepage', user)

    def test_method_field_with_method_missing(self):
        class BadSerializer(Schema):
            bad_field = fields.Method('invalid')
        u = User('Foo')
        with pytest.raises(ValueError):
            BadSerializer().dump(u)

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Schema):
            foo = 'not callable'
            bad_field = fields.Method('foo')
        u = User('Foo')
        with pytest.raises(ValueError):
            BadSerializer().dump(u)

    def test_datetime_serializes_to_iso_by_default(self, user):
        field = fields.DateTime()  # No format specified
        expected = utils.isoformat(user.created, localtime=False)
        assert field.serialize('created', user) == expected

    @pytest.mark.parametrize('value',
    [
        'invalid',
        [],
        24,
    ])
    def test_datetime_invalid_serialization(self, value, user):
        field = fields.DateTime()
        user.created = value

        with pytest.raises(ValidationError) as excinfo:
            field.serialize('created', user)
        assert excinfo.value.args[0] == '"{0}" cannot be formatted as a datetime.'.format(value)

    @pytest.mark.parametrize('fmt', ['rfc', 'rfc822'])
    def test_datetime_field_rfc822(self, fmt, user):
        field = fields.DateTime(format=fmt)
        expected = utils.rfcformat(user.created, localtime=False)
        assert field.serialize("created", user) == expected

    def test_localdatetime_rfc_field(self, user):
        field = fields.LocalDateTime(format='rfc')
        expected = utils.rfcformat(user.created, localtime=True)
        assert field.serialize("created", user) == expected

    @pytest.mark.parametrize('fmt', ['iso', 'iso8601'])
    def test_datetime_iso8601(self, fmt, user):
        field = fields.DateTime(format=fmt)
        expected = utils.isoformat(user.created, localtime=False)
        assert field.serialize("created", user) == expected

    def test_localdatetime_iso(self, user):
        field = fields.LocalDateTime(format="iso")
        expected = utils.isoformat(user.created, localtime=True)
        assert field.serialize("created", user) == expected

    def test_datetime_format(self, user):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert field.serialize("created", user) == user.created.strftime(format)

    def test_string_field(self):
        field = fields.String()
        user = User(name=b'foo')
        assert field.serialize('name', user) == 'foo'
        field = fields.String(allow_none=True)
        user.name = None
        assert field.serialize('name', user) is None

    def test_formattedstring_field(self):
        field = fields.FormattedString('Hello {name}')
        user = User(name='Monty')
        assert field.serialize('name', user) == 'Hello Monty'

    def test_string_field_default_to_empty_string(self, user):
        field = fields.String(default='')
        assert field.serialize("notfound", {}) == ''

    def test_time_field(self, user):
        field = fields.Time()
        expected = user.time_registered.isoformat()[:12]
        assert field.serialize('time_registered', user) == expected

        user.time_registered = None
        assert field.serialize('time_registered', user) is None

    @pytest.mark.parametrize('in_data',
    [
        'badvalue',
        '',
        [],
        42,
    ])
    def test_invalid_time_field_serialization(self, in_data, user):
        field = fields.Time()
        user.time_registered = in_data
        with pytest.raises(ValidationError) as excinfo:
            field.serialize('time_registered', user)
        msg = '"{0}" cannot be formatted as a time.'.format(in_data)
        assert excinfo.value.args[0] == msg

    def test_date_field(self, user):
        field = fields.Date()
        assert field.serialize('birthdate', user) == user.birthdate.isoformat()

        user.birthdate = None
        assert field.serialize('birthdate', user) is None

    @pytest.mark.parametrize('in_data',
    [
        'badvalue',
        '',
        [],
        42,
    ])
    def test_invalid_date_field_serialization(self, in_data, user):
        field = fields.Date()
        user.birthdate = in_data
        with pytest.raises(ValidationError) as excinfo:
            field.serialize('birthdate', user)
        msg = '"{0}" cannot be formatted as a date.'.format(in_data)
        assert excinfo.value.args[0] == msg

    def test_timedelta_field(self, user):
        user.d1 = dt.timedelta(days=1, seconds=1, microseconds=1)
        user.d2 = dt.timedelta(days=0, seconds=86401, microseconds=1)
        user.d3 = dt.timedelta(days=0, seconds=0, microseconds=86401000001)
        user.d4 = dt.timedelta(days=0, seconds=0, microseconds=0)
        user.d5 = dt.timedelta(days=-1, seconds=0, microseconds=0)

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize('d1', user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize('d1', user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize('d1', user) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize('d2', user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize('d2', user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize('d2', user) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize('d3', user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize('d3', user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize('d3', user) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize('d4', user) == 0
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize('d4', user) == 0
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize('d4', user) == 0

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize('d5', user) == -1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize('d5', user) == -86400
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize('d5', user) == -86400000000

        user.d6 = None
        assert field.serialize('d6', user) is None

    def test_datetime_list_field(self):
        obj = DateTimeList([dt.datetime.utcnow(), dt.datetime.now()])
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert all([type(each) == str for each in result])

    def test_list_field_with_error(self):
        obj = DateTimeList(['invaliddate'])
        field = fields.List(fields.DateTime)
        with pytest.raises(ValidationError):
            field.serialize('dtimes', obj)

    def test_datetime_list_serialize_single_value(self):
        obj = DateTimeList(dt.datetime.utcnow())
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert len(result) == 1
        assert type(result[0]) == str

    def test_list_field_serialize_none_returns_none(self):
        obj = DateTimeList(None)
        field = fields.List(fields.DateTime)
        assert field.serialize('dtimes', obj) is None

    def test_list_field_respect_inner_attribute(self):
        now = dt.datetime.now()
        obj = DateTimeList([now])
        field = fields.List(fields.Int(attribute='day'))
        assert field.serialize('dtimes', obj) == [now.day]

    def test_list_field_respect_inner_attribute_single_value(self):
        now = dt.datetime.now()
        obj = DateTimeList(now)
        field = fields.List(fields.Int(attribute='day'))
        assert field.serialize('dtimes', obj) == [now.day]

    def test_list_field_work_with_generator_single_value(self):
        def custom_generator():
            yield dt.datetime.utcnow()
        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert len(result) == 1

    def test_list_field_work_with_generators_multiple_values(self):
        def custom_generator():
            for dtime in [dt.datetime.utcnow(), dt.datetime.now()]:
                yield dtime
        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert len(result) == 2

    def test_list_field_work_with_generators_error(self):
        def custom_generator():
            for dtime in [dt.datetime.utcnow(), "m", dt.datetime.now()]:
                yield dtime
        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        with pytest.raises(ValidationError):
            field.serialize('dtimes', obj)

    def test_list_field_work_with_generators_empty_generator_returns_none_for_every_non_returning_yield_statement(self):
        def custom_generator():
            a = yield
            yield
        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime, allow_none=True)
        result = field.serialize('dtimes', obj)
        assert len(result) == 2
        assert result[0] is None
        assert result[1] is None

    def test_list_field_work_with_set(self):
        custom_set = set([1, 2, 3])
        obj = IntegerList(custom_set)
        field = fields.List(fields.Int)
        result = field.serialize("ints", obj)
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_list_field_work_with_custom_class_with_iterator_protocol(self):
        class IteratorSupportingClass:
            def __init__(self, iterable):
                self.iterable = iterable

            def __iter__(self):
                return iter(self.iterable)

        ints = IteratorSupportingClass([1, 2, 3])
        obj = IntegerList(ints)
        field = fields.List(fields.Int)
        result = field.serialize("ints", obj)
        assert len(result) == 3
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3

    def test_bad_list_field(self):
        class ASchema(Schema):
            id = fields.Int()
        with pytest.raises(ValueError):
            fields.List("string")
        with pytest.raises(ValueError) as excinfo:
            fields.List(ASchema)
        expected_msg = ('The type of the list elements must be a subclass '
                'of marshmallow.base.FieldABC')
        assert expected_msg in str(excinfo)

    def test_serialize_does_not_apply_validators(self, user):
        field = fields.Field(validate=lambda x: False)
        # No validation error raised
        assert field.serialize('age', user) == user.age

    def test_query_select_field_func_key(self, user):
        user.du1 = DummyModel('a')
        user.du2 = DummyModel('b')
        user.du3 = DummyModel('c')
        user.du4 = DummyModel('d')
        query = lambda: [DummyModel(ch) for ch in 'abc']

        field = fields.QuerySelect(query, str)
        assert field.serialize('du1', user) == 'bar a'
        assert field.serialize('du2', user) == 'bar b'
        assert field.serialize('du3', user) == 'bar c'
        with pytest.raises(ValidationError):
            field.serialize('du4', user)

    def test_query_select_field_string_key(self, user):
        user.du1 = DummyModel('a')
        user.du2 = DummyModel('b')
        user.du3 = DummyModel('c')
        user.du4 = DummyModel('d')
        query = lambda: [DummyModel(ch) for ch in 'abc']

        field = fields.QuerySelect(query, 'foo')
        assert field.serialize('du1', user) == 'a'
        assert field.serialize('du2', user) == 'b'
        assert field.serialize('du3', user) == 'c'
        with pytest.raises(ValidationError):
            field.serialize('du4', user)

    def test_query_select_list_field_func_key(self, user):
        user.du1 = [DummyModel('a'), DummyModel('c'), DummyModel('b')]
        user.du2 = [DummyModel('d'), DummyModel('e'), DummyModel('e')]
        user.du3 = [DummyModel('a'), DummyModel('b'), DummyModel('f')]
        user.du4 = [DummyModel('a'), DummyModel('b'), DummyModel('b')]
        user.du5 = []
        query = lambda: [DummyModel(ch) for ch in 'abecde']

        field = fields.QuerySelectList(query, str)
        assert field.serialize('du1', user) == ['bar a', 'bar c', 'bar b']
        assert field.serialize('du2', user) == ['bar d', 'bar e', 'bar e']
        assert field.serialize('du5', user) == []
        with pytest.raises(ValidationError):
            field.serialize('du3', user)
        with pytest.raises(ValidationError):
            field.serialize('du4', user)

    def test_query_select_list_field_string_key(self, user):
        user.du1 = [DummyModel('a'), DummyModel('c'), DummyModel('b')]
        user.du2 = [DummyModel('d'), DummyModel('e'), DummyModel('e')]
        user.du3 = [DummyModel('a'), DummyModel('b'), DummyModel('f')]
        user.du4 = [DummyModel('a'), DummyModel('b'), DummyModel('b')]
        user.du5 = []
        query = lambda: [DummyModel(ch) for ch in 'abecde']

        field = fields.QuerySelectList(query, 'foo')
        assert field.serialize('du1', user) == ['a', 'c', 'b']
        assert field.serialize('du2', user) == ['d', 'e', 'e']
        assert field.serialize('du5', user) == []
        with pytest.raises(ValidationError):
            field.serialize('du3', user)
        with pytest.raises(ValidationError):
            field.serialize('du4', user)

    def test_constant_field_serialization(self, user):
        field = fields.Constant('something')
        assert field.serialize('whatever', user) == 'something'

    def test_constant_field_serialize_when_omitted(self):
        class MiniUserSchema(Schema):
            name = fields.Constant('bill')

        s = MiniUserSchema()
        assert s.dump({}).data['name'] == 'bill'

    @pytest.mark.parametrize('FieldClass', ALL_FIELDS)
    def test_all_fields_serialize_none_to_none(self, FieldClass):
        if FieldClass == fields.FormattedString:
            field = FieldClass('{foo}', allow_none=True)
        else:
            field = FieldClass(allow_none=True)

        res = field.serialize('foo', {'foo': None})
        if FieldClass == fields.FormattedString:
            assert res == 'None'
        else:
            assert res is None


def test_serializing_named_tuple():
    Point = namedtuple('Point', ['x', 'y'])

    field = fields.Field()

    p = Point(x=4, y=2)

    assert field.serialize('x', p) == 4


def test_serializing_named_tuple_with_meta():
    Point = namedtuple('Point', ['x', 'y'])
    p = Point(x=4, y=2)

    class PointSerializer(Schema):
        class Meta:
            fields = ('x', 'y')

    serialized = PointSerializer().dump(p)
    assert serialized.data['x'] == 4
    assert serialized.data['y'] == 2
