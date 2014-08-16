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
        assert "FOO" == field.serialize("key", self.user)

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
            fields.List(UserSerializer)

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
        field.serialize('age', user_data)
    assert "Missing data for required field." in str(excinfo)


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


class TestValidation:

    def test_integer_with_validator(self):
        user = User(name='Joe', age='20')
        field = fields.Integer(validate=lambda x: 18 <= x <= 24)
        out = field.serialize('age', user)
        assert out == 20
        user2 = User(name='Joe', age='25')
        with pytest.raises(MarshallingError):
            field.serialize('age', user2)

    def test_integer_with_validators(self):
        user = User(name='Joe', age='20')

        def validators_gen():
            yield lambda x: x <= 24
            yield lambda x: 18 <= x

        m_collection_types = [
            fields.Integer(validate=[lambda x: x <= 24, lambda x: 18 <= x]),
            fields.Integer(validate=(lambda x: x <= 24, lambda x: 18 <= x)),
            fields.Integer(validate=validators_gen)
        ]

        for field in m_collection_types:
            out = field.serialize('age', user)
            assert out == 20
            user2 = User(name='Joe', age='25')
            with pytest.raises(MarshallingError):
                field.serialize('age', user2)

    def test_float_with_validator(self):
        user = User(name='Joe', age=3.14)
        field = fields.Float(validate=lambda f: f <= 4.1)
        assert field.serialize('age', user) == user.age
        invalid = User('foo', age=5.1)
        with pytest.raises(MarshallingError):
            field.serialize('age', invalid)

    def test_float_with_validators(self):
        user = User(name='Joe', age=3.14)

        def validators_gen():
            yield lambda f: f <= 4.1
            yield lambda f: f >= 1.0

        m_collection_types = [
            fields.Float(validate=[lambda f: f <= 4.1, lambda f: f >= 1.0]),
            fields.Float(validate=(lambda f: f <= 4.1, lambda f: f >= 1.0)),
            fields.Float(validate=validators_gen)
        ]

        for field in m_collection_types:
            assert field.serialize('age', user) == user.age
            invalid = User('foo', age=5.1)
            with pytest.raises(MarshallingError):
                field.serialize('age', invalid)

    def test_string_validator(self):
        user = User(name='Joe')
        field = fields.String(validate=lambda n: len(n) == 3)
        assert field.serialize('name', user) == 'Joe'
        user2 = User(name='Joseph')
        with pytest.raises(MarshallingError):
            field.serialize('name', user2)

    def test_string_validators(self):
        user = User(name='Joe')

        def validators_gen():
            yield lambda n: len(n) == 3
            yield lambda n: n.lower() == 'joe'

        m_collection_types = [
            fields.String(validate=[lambda n: len(n) == 3, lambda n: n.lower() == 'joe']),
            fields.String(validate=(lambda n: len(n) == 3, lambda n: n.lower() == 'joe')),
            fields.String(validate=validators_gen)
        ]

        for field in m_collection_types:
            assert field.serialize('name', user) == 'Joe'
            user2 = User(name='Joseph')
            with pytest.raises(MarshallingError):
                field.serialize('name', user2)

    def test_datetime_validator(self):
        user = User('Joe', birthdate=dt.datetime(2014, 8, 21))
        field = fields.DateTime(format='rfc', validate=lambda d: utils.from_rfc(d).year == 2014)
        assert field.serialize('birthdate', user) == utils.rfcformat(user.birthdate)
        user2 = User('Joe', birthdate=dt.datetime(2013, 8, 21))
        with pytest.raises(MarshallingError):
            field.serialize('birthdate', user2)

    def test_datetime_validators(self):
        user = User('Joe', birthdate=dt.datetime(2014, 8, 21))

        def validators_gen():
            yield lambda d: utils.from_rfc(d).year == 2014
            yield lambda d: utils.from_rfc(d).month == 8

        m_collection_types = [
            fields.DateTime(format='rfc', validate=[lambda d: utils.from_rfc(d).year == 2014,
                                                    lambda d: utils.from_rfc(d).month == 8]),
            fields.DateTime(format='rfc', validate=(lambda d: utils.from_rfc(d).year == 2014,
                                                    lambda d: utils.from_rfc(d).month == 8)),
            fields.DateTime(format='rfc', validate=validators_gen)
        ]

        for field in m_collection_types:
            assert field.serialize('birthdate', user) == utils.rfcformat(user.birthdate)
            user2 = User('Joe', birthdate=dt.datetime(2013, 8, 21))
            with pytest.raises(MarshallingError):
                field.serialize('birthdate', user2)

    def test_function_validator(self):
        user = User('joe')
        field = fields.Function(lambda d: d.name.upper(),
                                validate=lambda n: len(n) == 3)
        assert field.serialize('uppername', user) == 'JOE'
        invalid = User(name='joseph')
        with pytest.raises(MarshallingError):
            field.serialize('uppername', invalid)

    def test_function_validators(self):
        user = User('joe')

        def validators_gen():
            yield lambda n: len(n) == 3
            yield lambda n: n[1].lower() == 'o'

        m_collection_types = [
            fields.Function(lambda d: d.name.upper(), validate=[lambda n: len(n) == 3, lambda n: n[1].lower() == 'o']),
            fields.Function(lambda d: d.name.upper(), validate=(lambda n: len(n) == 3, lambda n: n[1].lower() == 'o')),
            fields.Function(lambda d: d.name.upper(), validate=validators_gen)
        ]

        for field in m_collection_types:
            assert field.serialize('uppername', user) == 'JOE'
            invalid = User(name='joseph')
            with pytest.raises(MarshallingError):
                field.serialize('uppername', invalid)

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

    def test_method_validators(self):

        def validators_gen():
            yield lambda n: len(n) == 3
            yield lambda n: n.upper()[2] == 'E'

        class MethodSerializerList(Serializer):
            uppername = fields.Method('get_uppername',
                                      validate=[lambda n: len(n) == 3, lambda n: n.upper()[2] == 'E'])

            def get_uppername(self, obj):
                return obj.name.upper()

        class MethodSerializerTuple(Serializer):
            uppername = fields.Method('get_uppername',
                                      validate=(lambda n: len(n) == 3, lambda n: n.upper()[2] == 'E'))

            def get_uppername(self, obj):
                return obj.name.upper()

        class MethodSerializerGenerator(Serializer):
            uppername = fields.Method('get_uppername',
                                      validate=validators_gen)

            def get_uppername(self, obj):
                return obj.name.upper()

        collection_serializers = [MethodSerializerList, MethodSerializerTuple, MethodSerializerGenerator]

        user = User('joe')
        for SerializerCls in collection_serializers:
            data, _ = SerializerCls(strict=True).dump(user)
            assert data['uppername'] == 'JOE'
            invalid = User(name='joseph')
            with pytest.raises(MarshallingError) as excinfo:
                SerializerCls(strict=True).dump(invalid)
            assert 'is not True' in str(excinfo)

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

    class PointSerializer(Serializer):
        class Meta:
            fields = ('x', 'y')

    serialized = PointSerializer(p)
    assert serialized.data['x'] == 4
    assert serialized.data['y'] == 2
