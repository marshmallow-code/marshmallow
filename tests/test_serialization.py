# -*- coding: utf-8 -*-
"""Tests for field serialization."""
from collections import namedtuple
import datetime as dt
import decimal

import pytest

from marshmallow import Schema, fields, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import total_seconds, text_type, basestring

from tests.base import User, DummyModel

class DateTimeList:
    def __init__(self, dtimes):
        self.dtimes = dtimes

class TestFieldSerialization:

    @pytest.fixture
    def user(self):
        return User("Foo", email="foo@bar.com", age=42)

    def test_default(self, user):
        user.age = None
        field = fields.Field(default='nan')
        assert field.serialize('age', user) == 'nan'

    @pytest.mark.parametrize(('value', 'expected'),
    [
        (42, float(42)),
        (0, float(0)),
        (None, 0.0),
    ])
    def test_number(self, value, expected, user):
        field = fields.Number()
        user.age = value
        assert field.serialize('age', user) == expected

    def test_number_as_string(self, user):
        user.age = 42
        field = fields.Number(as_string=True)
        assert field.serialize('age', user) == str(float(user.age))

    def test_number_as_string_default(self, user):
        user.age = None
        field = fields.Number(as_string=True)
        assert field.serialize('age', user) == str(0.0)

    def test_callable_default(self, user):
        user.age = None
        field = fields.Field(default=lambda: 'nan')
        assert field.serialize('age', user) == 'nan'

    def test_function_field(self, user):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", user)

    def test_integer_field(self, user):
        field = fields.Integer()
        assert field.serialize('age', user) == 42

    def test_integer_field(self, user):
        field = fields.Integer(as_string=True)
        assert field.serialize('age', user) == '42'

    def test_integer_field_default(self, user):
        user.age = None
        field = fields.Integer()
        assert field.serialize('age', user) == 0

    def test_integer_field_default_set_to_none(self, user):
        user.age = None
        field = fields.Integer(default=None)
        assert field.serialize('age', user) is None

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
        assert isinstance(field.serialize('m4', user), decimal.Decimal)
        assert field.serialize('m4', user) == decimal.Decimal()
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
            field.serialize('m6', user)

        field = fields.Decimal(1)
        assert isinstance(field.serialize('m1', user), decimal.Decimal)
        assert field.serialize('m1', user) == decimal.Decimal(12)
        assert isinstance(field.serialize('m2', user), decimal.Decimal)
        assert field.serialize('m2', user) == decimal.Decimal('12.4')
        assert isinstance(field.serialize('m3', user), decimal.Decimal)
        assert field.serialize('m3', user) == decimal.Decimal(1)
        assert isinstance(field.serialize('m4', user), decimal.Decimal)
        assert field.serialize('m4', user) == decimal.Decimal()
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
            field.serialize('m6', user)

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.serialize('m1', user), decimal.Decimal)
        assert field.serialize('m1', user) == decimal.Decimal(12)
        assert isinstance(field.serialize('m2', user), decimal.Decimal)
        assert field.serialize('m2', user) == decimal.Decimal('12.3')
        assert isinstance(field.serialize('m3', user), decimal.Decimal)
        assert field.serialize('m3', user) == decimal.Decimal(1)
        assert isinstance(field.serialize('m4', user), decimal.Decimal)
        assert field.serialize('m4', user) == decimal.Decimal()
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
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
        assert isinstance(field.serialize('m4', user), basestring)
        assert field.serialize('m4', user) == '0'
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
            field.serialize('m6', user)

        field = fields.Decimal(1, as_string=True)
        assert isinstance(field.serialize('m1', user), basestring)
        assert field.serialize('m1', user) == '12.0'
        assert isinstance(field.serialize('m2', user), basestring)
        assert field.serialize('m2', user) == '12.4'
        assert isinstance(field.serialize('m3', user), basestring)
        assert field.serialize('m3', user) == '1.0'
        assert isinstance(field.serialize('m4', user), basestring)
        assert field.serialize('m4', user) == '0'
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
            field.serialize('m6', user)

        field = fields.Decimal(1, decimal.ROUND_DOWN, as_string=True)
        assert isinstance(field.serialize('m1', user), basestring)
        assert field.serialize('m1', user) == '12.0'
        assert isinstance(field.serialize('m2', user), basestring)
        assert field.serialize('m2', user) == '12.3'
        assert isinstance(field.serialize('m3', user), basestring)
        assert field.serialize('m3', user) == '1.0'
        assert isinstance(field.serialize('m4', user), basestring)
        assert field.serialize('m4', user) == '0'
        with pytest.raises(MarshallingError):
            field.serialize('m5', user)
        with pytest.raises(MarshallingError):
            field.serialize('m6', user)

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_email_field_validates(self, user):
        user.email = 'bademail'
        field = fields.Email()
        with pytest.raises(MarshallingError):
            field.serialize('email', user)

    def test_url_field_validates(self, user):
        user.homepage = 'badhomepage'
        field = fields.URL()
        with pytest.raises(MarshallingError):
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

    def test_datetime_deserializes_to_iso_by_default(self, user):
        field = fields.DateTime()  # No format specified
        expected = utils.isoformat(user.created, localtime=False)
        assert field.serialize("created", user) == expected

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
        user.name = None
        assert field.serialize('name', user) == ''

    def test_formattedstring_field(self):
        field = fields.FormattedString('Hello {name}')
        user = User(name='Monty')
        assert field.serialize('name', user) == 'Hello Monty'

    def test_string_field_defaults_to_empty_string(self, user):
        field = fields.String()
        assert field.serialize("notfound", user) == ''

    def test_time_field(self, user):
        field = fields.Time()
        expected = user.time_registered.isoformat()[:12]
        assert field.serialize("time_registered", user) == expected

    def test_date_field(self, user):
        field = fields.Date()
        assert field.serialize('birthdate', user) == user.birthdate.isoformat()

    def test_timedelta_field(self, user):
        field = fields.TimeDelta()
        expected = total_seconds(user.since_created)
        assert field.serialize("since_created", user) == expected

    def test_select_field(self, user):
        field = fields.Select(['male', 'female', 'transexual', 'asexual'])
        assert field.serialize("sex", user) == "male"
        invalid = User('foo', sex='alien')
        with pytest.raises(MarshallingError):
            field.serialize('sex', invalid)

    def test_datetime_list_field(self):
        obj = DateTimeList([dt.datetime.utcnow(), dt.datetime.now()])
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert all([type(each) == str for each in result])

    def test_list_field_with_error(self):
        obj = DateTimeList(['invaliddate'])
        field = fields.List(fields.DateTime)
        with pytest.raises(MarshallingError):
            field.serialize('dtimes', obj)

    def test_datetime_list_serialize_single_value(self):
        obj = DateTimeList(dt.datetime.utcnow())
        field = fields.List(fields.DateTime)
        result = field.serialize('dtimes', obj)
        assert len(result) == 1
        assert type(result[0]) == str

    def test_list_field_serialize_none_returns_empty_list_by_default(self):
        obj = DateTimeList(None)
        field = fields.List(fields.DateTime)
        assert field.serialize('dtimes', obj) == []

    def test_list_field_serialize_allow_none(self):
        obj = DateTimeList(None)
        field = fields.List(fields.DateTime, allow_none=True)
        assert field.serialize('dtimes', obj) is None

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

    def test_arbitrary_field(self, user):
        field = fields.Arbitrary()
        user.age = 12.3
        result = field.serialize('age', user)
        assert result == text_type(utils.float_to_decimal(user.age))

    def test_arbitrary_field_default(self, user):
        field = fields.Arbitrary()
        user.age = None
        result = field.serialize('age', user)
        assert result == '0'

    def test_arbitrary_field_invalid_value(self, user):
        field = fields.Arbitrary()
        with pytest.raises(MarshallingError):
            user.age = 'invalidvalue'
            field.serialize('age', user)

    def test_fixed_field(self, user):
        field = fields.Fixed(3)
        user.age = 42
        result = field.serialize('age', user)
        assert result == '42.000'

    def test_fixed_field_default(self, user):
        field = fields.Fixed()
        user.age = None
        assert field.serialize('age', user) == '0.000'

    def test_fixed_field_invalid_value(self, user):
        field = fields.Fixed()
        with pytest.raises(MarshallingError):
            user.age = 'invalidvalue'
            field.serialize('age', user)

    def test_price_field(self, user):
        field = fields.Price()
        user.balance = 100
        assert field.serialize('balance', user) == '100.00'

    def test_price_field_default(self, user):
        field = fields.Price()
        user.balance = None
        assert field.serialize('price', user) == '0.00'

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
        with pytest.raises(MarshallingError):
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
        with pytest.raises(MarshallingError):
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
        with pytest.raises(MarshallingError):
            field.serialize('du3', user)
        with pytest.raises(MarshallingError):
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
        with pytest.raises(MarshallingError):
            field.serialize('du3', user)
        with pytest.raises(MarshallingError):
            field.serialize('du4', user)


class TestMarshaller:

    def test_prefix(self):
        u = User("Foo", email="foo@bar.com")
        marshal = fields.Marshaller(prefix='usr_')
        result = marshal(u, {"email": fields.Email(), 'name': fields.String()})
        assert result['usr_name'] == u.name
        assert result['usr_email'] == u.email

    def test_marshalling_generator(self):
        gen = (u for u in [User("Foo"), User("Bar")])
        marshal = fields.Marshaller()
        res = marshal(gen, {"name": fields.String()}, many=True)
        assert len(res) == 2

    def test_default_to_missing(self):
        u = User('Foo', email=None)
        marshal = fields.Marshaller()
        res = marshal(u, {'name': fields.String(),
                         'email': fields.Email(default=fields.missing)})
        assert res['name'] == u.name
        assert 'email' not in res


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
