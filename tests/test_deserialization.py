
import pytest

from marshmallow import fields, utils
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

    def test_tz_datetime_field_deserialization(self):
        assert 0, 'finish me'

    def test_localdatetime_field_deserialization(self):
        dtime = dt.datetime.now()
        localized_dtime = central.localize(dtime)
        field = fields.DateTime(format='iso')
        # Deserializes to a naive datetime
        assert_datetime_equal(field.deserialize(localized_dtime.isoformat()), dtime)

    def test_time_field_deserialization(self):
        assert 0, 'finish me'

    def test_fixed_field_deserialization(self):
        field = fields.Fixed(decimals=3)
        assert field.deserialize(None) == '0.000'
        assert field.deserialize('12.3456') == '12.346'
        assert field.deserialize(12.3456) == '12.346'
        with pytest.raises(DeserializationError):
            field.deserialize('badvalue')

    def test_timedelta_field_deserialization(self):
        assert 0, 'finish me'

    def test_date_field_deserialization(self):
        assert 0, 'finish me'

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

    def test_function_field_deserialization(self):
        assert 0, 'finish me'

    def test_method_field_deserialization(self):
        assert 0, 'finish me'

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
        # UserSerializer has no custom deserialization behavior, so a dict is
        # returned
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result = UserSerializer().deserialize(user_dict)
        assert result['name'] == 'Monty'
        assert result['age'] == 42.3

    def test_make_object(self):
        assert 0, 'finish me'
