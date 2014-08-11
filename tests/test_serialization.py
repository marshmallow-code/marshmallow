# -*- coding: utf-8 -*-
"""Tests for field serialization."""
import datetime as dt
from collections import namedtuple

import pytest

from marshmallow import Serializer, fields, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import total_seconds, text_type

from tests.base import User, UserSerializer

class TestFieldSerialization:

    def setup_method(self, method):
        self.user = User("Foo", email="foo@bar.com", age=42)

    def test_repr(self):
        field = fields.String()
        assert repr(field) == "<String Field>"

    def test_function_field(self):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.output("key", self.user)

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_method_field_with_method_missing(self):
        class BadSerializer(Serializer):
            bad_field = fields.Method('invalid')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Serializer):
            foo = 'not callable'
            bad_field = fields.Method('foo')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

    def test_datetime_field(self):
        field = fields.DateTime()
        expected = utils.rfcformat(self.user.created, localtime=False)
        assert field.output("created", self.user) == expected

    def test_localdatetime_field(self):
        field = fields.LocalDateTime()
        expected = utils.rfcformat(self.user.created, localtime=True)
        assert field.output("created", self.user) == expected

    def test_datetime_iso8601(self):
        field = fields.DateTime(format="iso")
        expected = utils.isoformat(self.user.created, localtime=False)
        assert field.output("created", self.user) == expected

    def test_localdatetime_iso(self):
        field = fields.LocalDateTime(format="iso")
        expected = utils.isoformat(self.user.created, localtime=True)
        assert field.output("created", self.user) == expected

    def test_datetime_format(self):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert field.output("created", self.user) == self.user.created.strftime(format)

    def test_string_field(self):
        field = fields.String()
        user = User(name=b'foo')
        assert field.output('name', user) == 'foo'
        user.name = None
        assert field.output('name', user) == ''

    def test_string_field_defaults_to_empty_string(self):
        field = fields.String()
        assert field.output("notfound", self.user) == ''

    def test_time_field(self):
        field = fields.Time()
        expected = self.user.time_registered.isoformat()[:12]
        assert field.output("time_registered", self.user) == expected

    def test_date_field(self):
        field = fields.Date()
        assert field.output('birthdate', self.user) == self.user.birthdate.isoformat()

    def test_timedelta_field(self):
        field = fields.TimeDelta()
        expected = total_seconds(self.user.since_created)
        assert field.output("since_created", self.user) == expected

    def test_select_field(self):
        field = fields.Select(['male', 'female'])
        assert field.output("sex", self.user) == "male"
        invalid = User('foo', sex='alien')
        with pytest.raises(MarshallingError):
            field.output('sex', invalid)

    def test_bad_list_field(self):
        with pytest.raises(MarshallingError):
            fields.List("string")
        with pytest.raises(MarshallingError):
            fields.List(UserSerializer)

    def test_arbitrary_field(self):
        field = fields.Arbitrary()
        self.user.age = 12.3
        result = field.output('age', self.user)
        assert result == text_type(utils.float_to_decimal(self.user.age))
        self.user.age = None
        result = field.output('age', self.user)
        assert result == text_type(utils.float_to_decimal(0.0))
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.output('age', self.user)

    def test_fixed_field(self):
        field = fields.Fixed(3)
        self.user.age = 42
        result = field.output('age', self.user)
        assert result == '42.000'
        self.user.age = None
        assert field.output('age', self.user) == '0.000'
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.output('age', self.user)


@pytest.mark.parametrize('FieldClass', [
    fields.String,
    fields.Integer,
    fields.Boolean,
    fields.Float,
    fields.Number,
    fields.DateTime,
    fields.LocalDateTime,
    fields.Time,
    fields.Date,
    fields.TimeDelta,
    fields.Fixed,
    fields.Url,
    fields.Email,
])
def test_required_field_failure(FieldClass):
    user_data = {"name": "Phil"}
    field = FieldClass(required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('age', user_data)
    assert "Missing data for required field." in str(excinfo)


@pytest.mark.parametrize(('FieldClass', 'value'), [
    (fields.String, ''),
    (fields.Integer, 0),
    (fields.Float, 0.0)
])
def test_required_field_falsy_is_ok(FieldClass, value):
    user_data = {'name': value}
    field = FieldClass(required=True)
    result = field.output('name', user_data)
    assert result is not None
    assert result == value


def test_required_list_field_failure():
    user_data = {"name": "Rosie"}
    field = fields.List(fields.String, required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('relatives', user_data)
    assert 'Missing data for required field.' in str(excinfo)


class TestValidation:

    def test_integer_with_validator(self):
        user = User(name='Joe', age='20')
        field = fields.Integer(validate=lambda x: 18 <= x <= 24)
        out = field.output('age', user)
        assert out == 20
        user2 = User(name='Joe', age='25')
        with pytest.raises(MarshallingError):
            field.output('age', user2)

    def test_float_with_validator(self):
        user = User(name='Joe', age=3.14)
        field = fields.Float(validate=lambda f: f <= 4.1)
        assert field.output('age', user) == user.age
        invalid = User('foo', age=5.1)
        with pytest.raises(MarshallingError):
            field.output('age', invalid)

    def test_string_validator(self):
        user = User(name='Joe')
        field = fields.String(validate=lambda n: len(n) == 3)
        assert field.output('name', user) == 'Joe'
        user2 = User(name='Joseph')
        with pytest.raises(MarshallingError):
            field.output('name', user2)

    def test_datetime_validator(self):
        user = User('Joe', birthdate=dt.datetime(2014, 8, 21))
        field = fields.DateTime(validate=lambda d: utils.from_rfc(d).year == 2014)
        assert field.output('birthdate', user) == utils.rfcformat(user.birthdate)
        user2 = User('Joe', birthdate=dt.datetime(2013, 8, 21))
        with pytest.raises(MarshallingError):
            field.output('birthdate', user2)

    def test_function_validator(self):
        user = User('joe')
        field = fields.Function(lambda d: d.name.upper(),
                                validate=lambda n: len(n) == 3)
        assert field.output('uppername', user) == 'JOE'
        invalid = User(name='joseph')
        with pytest.raises(MarshallingError):
            field.output('uppername', invalid)

    def test_method_validator(self):
        class MethodSerializer(Serializer):
            uppername = fields.Method('get_uppername',
                                      validate=lambda n: len(n) == 3)

            def get_uppername(self, obj):
                return obj.name.upper()
        user = User('joe')
        s = MethodSerializer(user, strict=True)
        assert s.data['uppername'] == 'JOE'
        invalid = User(name='joseph')
        with pytest.raises(MarshallingError) as excinfo:
            MethodSerializer(strict=True).dump(invalid)
        assert 'is not True' in str(excinfo)

class TestMarshaller:

    def test_stores_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller()
        marshal(u, {"email": fields.Email()})
        assert "email" in marshal.errors

    def test_strict_mode_raises_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller(strict=True)
        with pytest.raises(MarshallingError):
            marshal(u, {"email": fields.Email()})

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


def test_enum_is_select():
    assert fields.Select is fields.Enum


def test_serializing_named_tuple():
    Point = namedtuple('Point', ['x', 'y'])

    field = fields.Raw()

    p = Point(x=4, y=2)

    assert field.output('x', p) == 4


def test_serializing_named_tuple_with_meta():
    Point = namedtuple('Point', ['x', 'y'])
    p = Point(x=4, y=2)

    class PointSerializer(Serializer):
        class Meta:
            fields = ('x', 'y')

    serialized = PointSerializer(p)
    assert serialized.data['x'] == 4
    assert serialized.data['y'] == 2
