# -*- coding: utf-8 -*-
"""Tests for field serialization."""
from collections import namedtuple

import pytest

from marshmallow import Schema, fields, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import total_seconds, text_type

from tests.base import User, UserSchema

class TestFieldSerialization:

    def setup_method(self, method):
        self.user = User("Foo", email="foo@bar.com", age=42)

    def test_repr(self):
        field = fields.String()
        assert repr(field) == "<String Field>"

    def test_function_field(self):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", self.user)

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_method_field_with_method_missing(self):
        class BadSerializer(Schema):
            bad_field = fields.Method('invalid')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Schema):
            foo = 'not callable'
            bad_field = fields.Method('foo')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

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
        field = fields.Select(['male', 'female'])
        assert field.serialize("sex", self.user) == "male"
        invalid = User('foo', sex='alien')
        with pytest.raises(MarshallingError):
            field.serialize('sex', invalid)

    def test_bad_list_field(self):
        with pytest.raises(MarshallingError):
            fields.List("string")
        with pytest.raises(MarshallingError):
            fields.List(UserSchema)

    def test_arbitrary_field(self):
        field = fields.Arbitrary()
        self.user.age = 12.3
        result = field.serialize('age', self.user)
        assert result == text_type(utils.float_to_decimal(self.user.age))
        self.user.age = None
        result = field.serialize('age', self.user)
        assert result == text_type(utils.float_to_decimal(0.0))
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.serialize('age', self.user)

    def test_fixed_field(self):
        field = fields.Fixed(3)
        self.user.age = 42
        result = field.serialize('age', self.user)
        assert result == '42.000'
        self.user.age = None
        assert field.serialize('age', self.user) == '0.000'
        with pytest.raises(MarshallingError):
            self.user.age = 'invalidvalue'
            field.serialize('age', self.user)


@pytest.mark.parametrize(('FieldClass', 'value'), [
    (fields.String, ''),
    (fields.Integer, 0),
    (fields.Float, 0.0)
])
def test_required_field_falsy_is_ok(FieldClass, value):
    user_data = {'name': value}
    field = FieldClass(required=True)
    result = field.serialize('name', user_data)
    assert result is not None
    assert result == value


def test_required_list_field_failure():
    user_data = {"name": "Rosie"}
    field = fields.List(fields.String, required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.serialize('relatives', user_data)
    assert 'Missing data for required field.' in str(excinfo)


class TestMarshaller:

    def test_stores_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller()
        marshal(u, {"email": fields.Email()})
        assert "email" in marshal.errors

    def test_strict_mode_raises_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller()
        with pytest.raises(MarshallingError):
            marshal(u, {"email": fields.Email()}, strict=True)

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

    field = fields.Field()

    p = Point(x=4, y=2)

    assert field.serialize('x', p) == 4


def test_serializing_named_tuple_with_meta():
    Point = namedtuple('Point', ['x', 'y'])
    p = Point(x=4, y=2)

    class PointSerializer(Schema):
        class Meta:
            fields = ('x', 'y')

    serialized = PointSerializer(p)
    assert serialized.data['x'] == 4
    assert serialized.data['y'] == 2
