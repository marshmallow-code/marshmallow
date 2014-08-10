# -*- coding: utf-8 -*-
import pytest

from marshmallow import fields, utils, Serializer
from marshmallow.exceptions import DeserializationError
from marshmallow.compat import text_type

from tests.base import *  # noqa

class TestFieldDeserialization:

    def test_float_field_deserialization(self):
        field = fields.Float()
        assert_almost_equal(field.deserialize('12.3'), 12.3)
        assert_almost_equal(field.deserialize(12.3), 12.3)
        assert field.deserialize(None) == 0.0
        with pytest.raises(DeserializationError) as excinfo:
            field.deserialize('bad')
        assert 'could not convert string to float' in str(excinfo)

    def test_float_field_deserialization_with_default(self):
        field = fields.Float(default=1.0)
        assert field.deserialize(None) == 1.0

    def test_integer_field_deserialization(self):
        field = fields.Integer()
        assert field.deserialize('42') == 42
        assert field.deserialize(None) == 0
        with pytest.raises(DeserializationError):
            field.deserialize('42.0')
        with pytest.raises(DeserializationError):
            field.deserialize('bad')

    def test_string_field_deserialization(self):
        field = fields.String()
        assert field.deserialize(42) == '42'

    def test_boolean_field_deserialization(self):
        field = fields.Boolean()
        assert field.deserialize('True') is True
        assert field.deserialize('False') is False
        assert field.deserialize('true') is True
        assert field.deserialize('false') is False
        assert field.deserialize('1') is True
        assert field.deserialize('0') is False

    def test_boolean_field_deserialization_with_custom_truthy_values(self):
        class MyBoolean(fields.Boolean):
            truthy = set(['yep'])
        field = MyBoolean()
        assert field.deserialize('yep') is True
        with pytest.raises(DeserializationError):
            field.deserialize('notvalid')

    def test_arbitrary_field_deserialization(self):
        field = fields.Arbitrary()
        expected = text_type(utils.float_to_decimal(float(42)))
        assert field.deserialize('42') == expected

    def test_invalid_datetime_deserialization(self):
        field = fields.DateTime()
        with pytest.raises(DeserializationError):
            field.deserialize('not-a-datetime')

    def test_rfc_datetime_field_deserialization(self):
        dtime = dt.datetime.now()
        datestring = utils.rfcformat(dtime)
        field = fields.DateTime(format='rfc')
        assert_datetime_equal(field.deserialize(datestring), dtime)

    def test_iso_datetime_field_deserialization(self):
        dtime = dt.datetime.now()
        datestring = dtime.isoformat()
        field = fields.DateTime(format='iso')
        assert_datetime_equal(field.deserialize(datestring), dtime)

    def test_localdatetime_field_deserialization(self):
        dtime = dt.datetime.now()
        localized_dtime = central.localize(dtime)
        field = fields.DateTime(format='iso')
        result = field.deserialize(localized_dtime.isoformat())
        assert_datetime_equal(result, dtime)
        # If dateutil is used, the datetime will not be naive
        if utils.dateutil_available:
            assert result.tzinfo is not None

    def test_time_field_deserialization(self):
        field = fields.Time()
        t = dt.time(1, 23, 45)
        t_formatted = t.isoformat()
        result = field.deserialize(t_formatted)
        assert isinstance(result, dt.time)
        assert_time_equal(result, t)
        # With microseconds
        t2 = dt.time(1, 23, 45, 6789)
        t2_formatted = t2.isoformat()
        result2 = field.deserialize(t2_formatted)
        assert_time_equal(result2, t2)

    def test_invalid_time_field_deserialization(self):
        field = fields.Time()
        with pytest.raises(DeserializationError):
            field.deserialize('badvalue')

    def test_fixed_field_deserialization(self):
        field = fields.Fixed(decimals=3)
        assert field.deserialize(None) == '0.000'
        assert field.deserialize('12.3456') == '12.346'
        assert field.deserialize(12.3456) == '12.346'
        with pytest.raises(DeserializationError):
            field.deserialize('badvalue')

    def test_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        result = field.deserialize('42')
        assert isinstance(result, dt.timedelta)
        assert result.total_seconds() == 42.0
        result = field.deserialize('-42')
        assert result.total_seconds() == -42.0
        result = field.deserialize(12.3)
        assert_almost_equal(result.total_seconds(), 12.3)

    def test_invalid_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        with pytest.raises(DeserializationError):
            field.deserialize('badvalue')

    def test_date_field_deserialization(self):
        field = fields.Date()
        d = dt.date(2014, 8, 21)
        iso_date = d.isoformat()
        result = field.deserialize(iso_date)
        assert isinstance(result, dt.date)
        assert_date_equal(result, d)

    def test_invalid_date_field_deserialization(self):
        field = fields.Date()
        with pytest.raises(DeserializationError):
            field.deserialize('badvalue')

    def test_price_field_deserialization(self):
        field = fields.Price()
        assert field.deserialize(None) == '0.00'
        assert field.deserialize('12.345') == '12.35'

    def test_url_field_deserialization(self):
        field = fields.Url()
        assert field.deserialize('https://duckduckgo.com') == 'https://duckduckgo.com'
        assert field.deserialize(None) is None
        with pytest.raises(DeserializationError):
            field.deserialize('badurl')
        # Relative URLS not allowed by default
        with pytest.raises(DeserializationError):
            field.deserialize('/foo/bar')

    def test_relative_url_field_deserialization(self):
        field = fields.Url(relative=True)
        assert field.deserialize('/foo/bar') == '/foo/bar'

    def test_email_field_deserialization(self):
        field = fields.Email()
        assert field.deserialize('foo@bar.com') == 'foo@bar.com'
        with pytest.raises(DeserializationError):
            field.deserialize('invalidemail')

    def test_function_field_deserialization_is_noop_by_default(self):
        field = fields.Function(lambda x: None)
        # Default is noop
        assert field.deserialize('foo') == 'foo'
        assert field.deserialize(42) == 42

    def test_function_field_deserialization_with_callable(self):
        field = fields.Function(lambda x: None,
                                deserialize=lambda val: val.upper())
        assert field.deserialize('foo') == 'FOO'

    def test_deserialization_function_must_be_callable(self):
        with pytest.raises(ValueError):
            fields.Function(lambda x: None,
                            deserialize='notvalid')

    def test_method_field_deserialization_is_noop_by_default(self):
        class MiniUserSerializer(Serializer):
            uppername = fields.Method('uppercase_name')

            def uppercase_name(self, obj):
                return obj.upper()
        user = User(name='steve')
        s = MiniUserSerializer(user)
        assert s.fields['uppername'].deserialize('steve') == 'steve'

    def test_deserialization_method(self):
        class MiniUserSerializer(Serializer):
            uppername = fields.Method('uppercase_name', deserialize='lowercase_name')

            def uppercase_name(self, obj):
                return obj.name.upper()

            def lowercase_name(self, value):
                return value.lower()

        user = User(name='steve')
        s = MiniUserSerializer(user)
        assert s.fields['uppername'].deserialize('STEVE') == 'steve'

    def test_enum_field_deserialization(self):
        field = fields.Enum(['red', 'blue'])
        assert field.deserialize('red') == 'red'
        with pytest.raises(DeserializationError):
            field.deserialize('notvalid')

    def test_list_field_deserialization(self):
        field = fields.List(fields.Fixed(3))
        nums = (1, 2, 3)
        assert field.deserialize(nums) == ['1.000', '2.000', '3.000']
        with pytest.raises(DeserializationError):
            field.deserialize((1, 2, 'invalid'))

    def test_field_deserialization_with_user_validator(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid')
        assert field.deserialize('Valid') == 'Valid'
        with pytest.raises(DeserializationError) as excinfo:
            field.deserialize('invalid')
        assert 'Validator <lambda>(invalid) is not True' in str(excinfo)

    def test_field_deserialization_with_custom_error_message(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid', error='Bad value.')
        with pytest.raises(DeserializationError) as excinfo:
            field.deserialize('invalid')
        assert 'Bad value.' in str(excinfo)


class TestSchemaDeserialization:

    def test_deserialize_to_dict(self):
        # No custom deserialization behavior, so a dict is returned
        class SimpleUserSerializer(Serializer):
            name = fields.String()
            age = fields.Float()
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result = SimpleUserSerializer().deserialize(user_dict)
        assert result['name'] == 'Monty'
        assert_almost_equal(result['age'], 42.3)

    def test_make_object(self):
        class SimpleUserSerializer(Serializer):
            name = fields.String()
            age = fields.Float()

            def make_object(self, data):
                return User(**data)
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result = SimpleUserSerializer().deserialize(user_dict)
        assert isinstance(result, User)
        assert result.name == 'Monty'
        assert_almost_equal(result.age, 42.3)
