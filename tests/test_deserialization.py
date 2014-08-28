# -*- coding: utf-8 -*-
import pytest
import json
import uuid

from marshmallow import fields, utils, Schema
from marshmallow.exceptions import UnmarshallingError
from marshmallow.compat import text_type, total_seconds

from tests.base import *  # noqa

class TestFieldDeserialization:

    def test_float_field_deserialization(self):
        field = fields.Float()
        assert_almost_equal(field.deserialize('12.3'), 12.3)
        assert_almost_equal(field.deserialize(12.3), 12.3)
        assert field.deserialize(None) == 0.0
        with pytest.raises(UnmarshallingError):
            field.deserialize('bad')

    def test_float_field_deserialization_with_default(self):
        field = fields.Float(default=1.0)
        assert field.deserialize(None) == 1.0

    def test_integer_field_deserialization(self):
        field = fields.Integer()
        assert field.deserialize('42') == 42
        assert field.deserialize(None) == 0
        with pytest.raises(UnmarshallingError):
            field.deserialize('42.0')
        with pytest.raises(UnmarshallingError):
            field.deserialize('bad')

    def test_string_field_deserialization(self):
        field = fields.String()
        assert field.deserialize(None) == ''
        assert field.deserialize(42) == '42'
        assert field.deserialize(b'foo') == 'foo'

    def test_boolean_field_deserialization(self):
        field = fields.Boolean()
        assert field.deserialize(True) is True
        assert field.deserialize(False) is False
        assert field.deserialize(None) is False
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
        with pytest.raises(UnmarshallingError):
            field.deserialize('notvalid')

    def test_arbitrary_field_deserialization(self):
        field = fields.Arbitrary()
        expected = text_type(utils.float_to_decimal(float(42)))
        assert field.deserialize('42') == expected

    def test_invalid_datetime_deserialization(self):
        field = fields.DateTime()
        with pytest.raises(UnmarshallingError):
            field.deserialize('not-a-datetime')

    @pytest.mark.parametrize('fmt', ['rfc', 'rfc822'])
    def test_rfc_datetime_field_deserialization(self, fmt):
        dtime = dt.datetime.now()
        datestring = utils.rfcformat(dtime)
        field = fields.DateTime(format=fmt)
        assert_datetime_equal(field.deserialize(datestring), dtime)

    @pytest.mark.parametrize('fmt', ['iso', 'iso8601'])
    def test_iso_datetime_field_deserialization(self, fmt):
        dtime = dt.datetime.now()
        datestring = dtime.isoformat()
        field = fields.DateTime(format=fmt)
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
        with pytest.raises(UnmarshallingError):
            field.deserialize('badvalue')

    def test_fixed_field_deserialization(self):
        field = fields.Fixed(decimals=3)
        assert field.deserialize(None) == '0.000'
        assert field.deserialize('12.3456') == '12.346'
        assert field.deserialize(12.3456) == '12.346'
        with pytest.raises(UnmarshallingError):
            field.deserialize('badvalue')

    def test_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        result = field.deserialize('42')
        assert isinstance(result, dt.timedelta)
        assert total_seconds(result) == 42.0
        result = field.deserialize('-42')
        assert total_seconds(result) == -42.0
        result = field.deserialize(12.3)
        assert_almost_equal(total_seconds(result), 12.3)

    def test_invalid_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        with pytest.raises(UnmarshallingError):
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
        with pytest.raises(UnmarshallingError):
            field.deserialize('badvalue')

    def test_price_field_deserialization(self):
        field = fields.Price()
        assert field.deserialize(None) == '0.00'
        assert field.deserialize('12.345') == '12.35'

    def test_url_field_deserialization(self):
        field = fields.Url()
        assert field.deserialize('https://duckduckgo.com') == 'https://duckduckgo.com'
        assert field.deserialize(None) is None
        with pytest.raises(UnmarshallingError):
            field.deserialize('badurl')
        # Relative URLS not allowed by default
        with pytest.raises(UnmarshallingError):
            field.deserialize('/foo/bar')

    def test_relative_url_field_deserialization(self):
        field = fields.Url(relative=True)
        assert field.deserialize('/foo/bar') == '/foo/bar'

    def test_email_field_deserialization(self):
        field = fields.Email()
        assert field.deserialize('foo@bar.com') == 'foo@bar.com'
        with pytest.raises(UnmarshallingError):
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

    def test_uuid_field_deserialization(self):
        field = fields.UUID()
        uuid_str = str(uuid.uuid4())
        assert field.deserialize(uuid_str) == uuid_str

    def test_deserialization_function_must_be_callable(self):
        with pytest.raises(ValueError):
            fields.Function(lambda x: None,
                            deserialize='notvalid')

    def test_method_field_deserialization_is_noop_by_default(self):
        class MiniUserSerializer(Schema):
            uppername = fields.Method('uppercase_name')

            def uppercase_name(self, obj):
                return obj.upper()
        user = User(name='steve')
        s = MiniUserSerializer(user)
        assert s.fields['uppername'].deserialize('steve') == 'steve'

    def test_deserialization_method(self):
        class MiniUserSerializer(Schema):
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
        with pytest.raises(UnmarshallingError):
            field.deserialize('notvalid')

    def test_list_field_deserialization(self):
        field = fields.List(fields.Fixed(3))
        nums = (1, 2, 3)
        assert field.deserialize(nums) == ['1.000', '2.000', '3.000']
        with pytest.raises(UnmarshallingError):
            field.deserialize((1, 2, 'invalid'))

    def test_field_deserialization_with_user_validator(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid')
        assert field.deserialize('Valid') == 'Valid'
        with pytest.raises(UnmarshallingError) as excinfo:
            field.deserialize('invalid')
        assert 'Validator <lambda>(invalid) is not True' in str(excinfo)

    def test_field_deserialization_with_user_validators(self):

        def validators_gen():
            yield lambda s: s.lower() == 'valid'
            yield lambda s: s.lower()[::-1] == 'dilav'

        m_colletion_type = [
            fields.String(validate=[lambda s: s.lower() == 'valid', lambda s: s.lower()[::-1] == 'dilav']),
            fields.String(validate=(lambda s: s.lower() == 'valid', lambda s: s.lower()[::-1] == 'dilav')),
            fields.String(validate=validators_gen)
        ]

        for field in m_colletion_type:
            assert field.deserialize('Valid') == 'Valid'
            with pytest.raises(UnmarshallingError) as excinfo:
                field.deserialize('invalid')
            assert 'Validator <lambda>(invalid) is not True' in str(excinfo)

    def test_field_deserialization_with_custom_error_message(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid', error='Bad value.')
        with pytest.raises(UnmarshallingError) as excinfo:
            field.deserialize('invalid')
        assert 'Bad value.' in str(excinfo)

# No custom deserialization behavior, so a dict is returned
class SimpleUserSerializer(Schema):
    name = fields.String()
    age = fields.Float()

class Validator(Schema):
    email = fields.Email()
    colors = fields.Enum(['red', 'blue'])
    age = fields.Integer(validate=lambda n: n > 0)

class Validators(Schema):
    email = fields.Email()
    colors = fields.Enum(['red', 'blue'])
    age = fields.Integer(validate=[lambda n: n > 0, lambda n: n < 100])

class TestSchemaDeserialization:

    def test_deserialize_to_dict(self):
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result, errors = SimpleUserSerializer().load(user_dict)
        assert result['name'] == 'Monty'
        assert_almost_equal(result['age'], 42.3)

    def test_deserialize_many(self):
        users_data = [
            {'name': 'Mick', 'age': '914'},
            {'name': 'Keith', 'age': '8442'}
        ]
        result, errors = SimpleUserSerializer(many=True).load(users_data)
        assert isinstance(result, list)
        user = result[0]
        assert user['age'] == int(users_data[0]['age'])

    def test_make_object(self):
        class SimpleUserSerializer2(Schema):
            name = fields.String()
            age = fields.Float()

            def make_object(self, data):
                return User(**data)
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result, errors = SimpleUserSerializer2().load(user_dict)
        assert isinstance(result, User)
        assert result.name == 'Monty'
        assert_almost_equal(result.age, 42.3)

    def test_loads_deserializes_from_json(self):
        user_dict = {'name': 'Monty', 'age': '42.3'}
        user_json = json.dumps(user_dict)
        result, errors = UserSchema().loads(user_json)
        assert isinstance(result, User)
        assert result.name == 'Monty'
        assert_almost_equal(result.age, 42.3)

    def test_nested_single_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            author = fields.Nested(SimpleUserSerializer)

        blog_dict = {
            'title': 'Gimme Shelter',
            'author': {'name': 'Mick', 'age': '914'}
        }
        result, errors = SimpleBlogSerializer().load(blog_dict)
        author = result['author']
        assert author['name'] == 'Mick'
        assert author['age'] == 914

    def test_nested_list_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            authors = fields.Nested(SimpleUserSerializer, many=True)

        blog_dict = {
            'title': 'Gimme Shelter',
            'authors': [
                {'name': 'Mick', 'age': '914'},
                {'name': 'Keith', 'age': '8442'}
            ]
        }
        result, errors = SimpleBlogSerializer().load(blog_dict)
        assert isinstance(result['authors'], list)
        author = result['authors'][0]
        assert author['name'] == 'Mick'
        assert author['age'] == 914

    def test_deserialize_with_attribute_param(self):
        class AliasingUserSerializer(Schema):
            username = fields.Email(attribute='email')
            years = fields.Integer(attribute='age')
        data = {
            'username': 'foo@bar.com',
            'years': '42'
        }
        result, errors = AliasingUserSerializer().load(data)
        assert result['email'] == 'foo@bar.com'
        assert result['age'] == 42

    def test_deserialization_returns_errors(self):
        bad_data = {
            'email': 'invalid-email',
            'colors': 'burger',
            'age': -1,
        }
        v = Validator(strict=False)
        result, errors = v.load(bad_data)
        assert 'email' in errors
        assert 'colors' in errors
        assert 'age' in errors

    def test_deserialization_returns_errors_with_multiple_validators(self):
        bad_data = {
            'email': 'invalid-email',
            'colors': 'burger',
            'age': -1,
        }
        v = Validators(strict=False)
        result, errors = v.load(bad_data)
        assert 'email' in errors
        assert 'colors' in errors
        assert 'age' in errors

    def test_strict_mode_deserialization(self):
        bad_data = {
            'email': 'invalid-email',
            'colors': 'burger',
            'age': -1,
        }
        v = Validator(strict=True)
        with pytest.raises(UnmarshallingError):
            v.load(bad_data)

    def test_strict_mode_deserialization_with_multiple_validators(self):
        bad_data = {
            'email': 'invalid-email',
            'colors': 'burger',
            'age': -1,
        }
        v = Validators(strict=True)
        with pytest.raises(UnmarshallingError):
            v.load(bad_data)


class TestUnMarshaller:

    @pytest.fixture
    def unmarshal(self):
        return fields.Unmarshaller()

    def test_deserialize(self, unmarshal):
        user_data = {
            'age': '12'
        }
        result = unmarshal.deserialize(user_data, {'age': fields.Integer()})
        assert result['age'] == 12

    def test_extra_fields(self, unmarshal):
        data = {'name': 'Mick'}
        fields_dict = {'name': fields.String(), 'age': fields.Integer()}
        # data doesn't have to have all the fields in the schema
        result = unmarshal(data, fields_dict)
        assert result['name'] == data['name']
        assert 'age' not in result

    def test_deserialize_many(self, unmarshal):
        users_data = [
            {'name': 'Mick', 'age': '71'},
            {'name': 'Keith', 'age': '70'}
        ]
        fields_dict = {
            'name': fields.String(),
            'age': fields.Integer(),
        }
        result = unmarshal.deserialize(users_data, fields_dict, many=True)
        assert isinstance(result, list)
        user = result[0]
        assert user['age'] == 71

    def test_deserialize_strict_raises_error(self):
        strict_unmarshal = fields.Unmarshaller()
        with pytest.raises(UnmarshallingError):
            strict_unmarshal(
                {'email': 'invalid', 'name': 'Mick'},
                {'email': fields.Email(), 'name': fields.String()},
                strict=True
            )

    def test_deserialize_stores_errors(self, unmarshal):
        user_data = {
            'email': 'invalid',
            'age': 'nan',
            'name': 'Valid Name',
        }
        fields_dict = {
            'email': fields.Email(),
            'age': fields.Integer(),
            'name': fields.String(),
        }
        unmarshal(user_data, fields_dict)
        errors = unmarshal.errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'name' not in errors

    def test_deserialize_fields_with_attribute_param(self, unmarshal):
        data = {
            'username': 'mick@stones.com',
            'name': 'Mick'
        }
        fields_dict = {
            'username': fields.Email(attribute='email'),
            'name': fields.String(attribute='firstname'),
        }
        result = unmarshal.deserialize(data, fields_dict)
        assert result['email'] == 'mick@stones.com'
        assert result['firstname'] == 'Mick'
