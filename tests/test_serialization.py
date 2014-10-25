# -*- coding: utf-8 -*-
"""Tests for field serialization."""
from collections import namedtuple
import datetime as dt

import pytest

from marshmallow import Schema, fields, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import total_seconds, text_type

from tests.base import User

class DateTimeList:
    def __init__(self, dtimes):
        self.dtimes = dtimes

class TestFieldSerialization:

    def setup_method(self, method):
        self.user = User("Foo", email="foo@bar.com", age=42)

    def test_function_field(self):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", self.user)

    def test_integer_field(self):
        field = fields.Integer()
        assert field.serialize('age', self.user) == 42

    def test_integer_field_default(self):
        self.user.age = None
        field = fields.Integer()
        assert field.serialize('age', self.user) == 0

    def test_integer_field_default_set_to_none(self):
        self.user.age = None
        field = fields.Integer(default=None)
        assert field.serialize('age', self.user) is None

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_email_field_validates(self):
        self.user.email = 'bademail'
        field = fields.Email()
        with pytest.raises(MarshallingError):
            field.serialize('email', self.user)

    def test_url_field_validates(self):
        self.user.homepage = 'badhomepage'
        field = fields.URL()
        with pytest.raises(MarshallingError):
            field.serialize('homepage', self.user)

    def test_method_field_with_method_missing(self):
        class BadSerializer(Schema):
            bad_field = fields.Method('invalid')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(strict=True).dump(u)

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Schema):
            foo = 'not callable'
            bad_field = fields.Method('foo')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(strict=True).dump(u)

    def test_datetime_deserializes_to_iso_by_default(self):
        field = fields.DateTime()  # No format specified
        expected = utils.isoformat(self.user.created, localtime=False)
        assert field.serialize("created", self.user) == expected

    @pytest.mark.parametrize('fmt', ['rfc', 'rfc822'])
    def test_datetime_field_rfc822(self, fmt):
        field = fields.DateTime(format=fmt)
        expected = utils.rfcformat(self.user.created, localtime=False)
        assert field.serialize("created", self.user) == expected

    def test_localdatetime_rfc_field(self):
        field = fields.LocalDateTime(format='rfc')
        expected = utils.rfcformat(self.user.created, localtime=True)
        assert field.serialize("created", self.user) == expected

    @pytest.mark.parametrize('fmt', ['iso', 'iso8601'])
    def test_datetime_iso8601(self, fmt):
        field = fields.DateTime(format=fmt)
        expected = utils.isoformat(self.user.created, localtime=False)
        assert field.serialize("created", self.user) == expected

    def test_localdatetime_iso(self):
        field = fields.LocalDateTime(format="iso")
        expected = utils.isoformat(self.user.created, localtime=True)
        assert field.serialize("created", self.user) == expected

    def test_datetime_format(self):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert field.serialize("created", self.user) == self.user.created.strftime(format)

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

    def test_string_field_defaults_to_empty_string(self):
        field = fields.String()
        assert field.serialize("notfound", self.user) == ''

    def test_time_field(self):
        field = fields.Time()
        expected = self.user.time_registered.isoformat()[:12]
        assert field.serialize("time_registered", self.user) == expected

    def test_date_field(self):
        field = fields.Date()
        assert field.serialize('birthdate', self.user) == self.user.birthdate.isoformat()

    def test_timedelta_field(self):
        field = fields.TimeDelta()
        expected = total_seconds(self.user.since_created)
        assert field.serialize("since_created", self.user) == expected

    def test_select_field(self):
        field = fields.Select(['male', 'female', 'transexual', 'asexual'])
        assert field.serialize("sex", self.user) == "male"
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
        with pytest.raises(MarshallingError):
            fields.List("string")
        with pytest.raises(MarshallingError) as excinfo:
            fields.List(ASchema)
        expected_msg = ('The type of the list elements must be a subclass '
                'of marshmallow.base.FieldABC')
        assert expected_msg in str(excinfo)

    def test_arbitrary_field(self):
        field = fields.Arbitrary()
        self.user.age = 12.3
        result = field.serialize('age', self.user)
        assert result == text_type(utils.float_to_decimal(self.user.age))

    def test_arbitrary_field_default(self):
        field = fields.Arbitrary()
        self.user.age = None
        result = field.serialize('age', self.user)
        assert result == '0'

    def test_arbitrary_field_invalid_value(self):
        field = fields.Arbitrary()
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.serialize('age', self.user)

    def test_fixed_field(self):
        field = fields.Fixed(3)
        self.user.age = 42
        result = field.serialize('age', self.user)
        assert result == '42.000'

    def test_fixed_field_default(self):
        field = fields.Fixed()
        self.user.age = None
        assert field.serialize('age', self.user) == '0.000'

    def test_fixed_field_invalid_value(self):
        field = fields.Fixed()
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.serialize('age', self.user)

    def test_price_field(self):
        field = fields.Price()
        self.user.balance = 100
        assert field.serialize('balance', self.user) == '100.00'

    def test_price_field_default(self):
        field = fields.Price()
        self.user.balance = None
        assert field.serialize('price', self.user) == '0.00'

    def test_serialize_does_not_apply_validators(self):
        field = fields.Field(validate=lambda x: False)
        # No validation error raised
        assert field.serialize('age', self.user) == self.user.age


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
