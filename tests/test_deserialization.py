# -*- coding: utf-8 -*-
import datetime as dt
import uuid
import decimal

import pytest

from marshmallow import fields, utils, Schema, validate
from marshmallow.exceptions import ValidationError
from marshmallow.compat import basestring

from tests.base import (
    assert_almost_equal,
    assert_date_equal,
    assert_datetime_equal,
    assert_time_equal,
    central,
    ALL_FIELDS,
    User,
    DummyModel,
)

class TestDeserializingNone:

    @pytest.mark.parametrize('FieldClass', ALL_FIELDS)
    def test_fields_allow_none_deserialize_to_none(self, FieldClass):
        if FieldClass == fields.FormattedString:
            field = FieldClass(src_str='foo', allow_none=True)
        else:
            field = FieldClass(allow_none=True)
        field.deserialize(None) is None

    # https://github.com/marshmallow-code/marshmallow/issues/111
    @pytest.mark.parametrize('FieldClass', ALL_FIELDS)
    def test_fields_dont_allow_none_by_default(self, FieldClass):
        # by default, allow_none=False
        if FieldClass == fields.FormattedString:
            field = FieldClass(src_str='foo')
        else:
            field = FieldClass()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(None)
        assert 'Field may not be null.' in str(excinfo)

    def test_allow_none_is_true_if_missing_is_true(self):
        field = fields.Field(missing=None)
        assert field.allow_none is True
        field.deserialize(None) is None

    def test_list_field_deserialize_none_to_empty_list(self):
        field = fields.List(fields.String(allow_none=True), allow_none=True)
        assert field.deserialize(None) is None


class TestFieldDeserialization:

    def test_float_field_deserialization(self):
        field = fields.Float()
        assert_almost_equal(field.deserialize('12.3'), 12.3)
        assert_almost_equal(field.deserialize(12.3), 12.3)

    @pytest.mark.parametrize('in_val',
    [
        'bad',
        '',
        {},
    ])
    def test_invalid_float_field_deserialization(self, in_val):
        field = fields.Float()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_val)
        assert excinfo.value.args[0] == 'Not a valid number.'

    def test_integer_field_deserialization(self):
        field = fields.Integer()
        assert field.deserialize('42') == 42
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('42.0')
        assert excinfo.value.args[0] == 'Not a valid integer.'
        with pytest.raises(ValidationError):
            field.deserialize('bad')
        assert excinfo.value.args[0] == 'Not a valid integer.'
        with pytest.raises(ValidationError):
            field.deserialize({})
        assert excinfo.value.args[0] == 'Not a valid integer.'

    def test_decimal_field_deserialization(self):
        m1 = 12
        m2 = '12.355'
        m3 = decimal.Decimal(1)
        m4 = 'abc'
        m5 = [1, 2]

        field = fields.Decimal()
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal('12.355')
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m4)
        assert excinfo.value.args[0] == 'Not a valid number.'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m5)
        assert excinfo.value.args[0] == 'Not a valid number.'

    def test_decimal_field_with_places(self):
        m1 = 12
        m2 = '12.355'
        m3 = decimal.Decimal(1)
        m4 = 'abc'
        m5 = [1, 2]

        field = fields.Decimal(1)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal('12.4')
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m4)
        assert excinfo.value.args[0] == 'Not a valid number.'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m5)
        assert excinfo.value.args[0] == 'Not a valid number.'

    def test_decimal_field_with_places_and_rounding(self):
        m1 = 12
        m2 = '12.355'
        m3 = decimal.Decimal(1)
        m4 = 'abc'
        m5 = [1, 2]

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal('12.3')
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError):
            field.deserialize(m4)
        with pytest.raises(ValidationError):
            field.deserialize(m5)

    def test_decimal_field_deserialization_string(self):
        m1 = 12
        m2 = '12.355'
        m3 = decimal.Decimal(1)
        m4 = 'abc'
        m5 = [1, 2]

        field = fields.Decimal(as_string=True)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal('12.355')
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError):
            field.deserialize(m4)
        with pytest.raises(ValidationError):
            field.deserialize(m5)

    def test_decimal_field_special_values(self):
        m1 = '-NaN'
        m2 = 'NaN'
        m3 = '-sNaN'
        m4 = 'sNaN'
        m5 = '-Infinity'
        m6 = 'Infinity'
        m7 = '-0'

        field = fields.Decimal(places=2, allow_nan=True)

        m1d = field.deserialize(m1)
        assert isinstance(m1d, decimal.Decimal)
        assert m1d.is_qnan() and not m1d.is_signed()

        m2d = field.deserialize(m2)
        assert isinstance(m2d, decimal.Decimal)
        assert m2d.is_qnan() and not m2d.is_signed()

        m3d = field.deserialize(m3)
        assert isinstance(m3d, decimal.Decimal)
        assert m3d.is_qnan() and not m3d.is_signed()

        m4d = field.deserialize(m4)
        assert isinstance(m4d, decimal.Decimal)
        assert m4d.is_qnan() and not m4d.is_signed()

        m5d = field.deserialize(m5)
        assert isinstance(m5d, decimal.Decimal)
        assert m5d.is_infinite() and m5d.is_signed()

        m6d = field.deserialize(m6)
        assert isinstance(m6d, decimal.Decimal)
        assert m6d.is_infinite() and not m6d.is_signed()

        m7d = field.deserialize(m7)
        assert isinstance(m7d, decimal.Decimal)
        assert m7d.is_zero() and m7d.is_signed()

    def test_decimal_field_special_values_not_permitted(self):
        m1 = '-NaN'
        m2 = 'NaN'
        m3 = '-sNaN'
        m4 = 'sNaN'
        m5 = '-Infinity'
        m6 = 'Infinity'
        m7 = '-0'

        field = fields.Decimal(places=2)

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m1)
        assert str(excinfo.value.args[0]) == 'Special numeric values are not permitted.'
        with pytest.raises(ValidationError):
            field.deserialize(m2)
        with pytest.raises(ValidationError):
            field.deserialize(m3)
        with pytest.raises(ValidationError):
            field.deserialize(m4)
        with pytest.raises(ValidationError):
            field.deserialize(m5)
        with pytest.raises(ValidationError):
            field.deserialize(m6)

        m7d = field.deserialize(m7)
        assert isinstance(m7d, decimal.Decimal)
        assert m7d.is_zero() and m7d.is_signed()

    def test_string_field_deserialization(self):
        field = fields.String()
        assert field.deserialize('foo') == 'foo'
        assert field.deserialize(b'foo') == 'foo'

        # https://github.com/marshmallow-code/marshmallow/issues/231
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(42)
        assert excinfo.value.args[0] == 'Not a valid string.'

        with pytest.raises(ValidationError):
            field.deserialize({})

    def test_boolean_field_deserialization(self):
        field = fields.Boolean()
        assert field.deserialize(True) is True
        assert field.deserialize(False) is False
        assert field.deserialize('True') is True
        assert field.deserialize('False') is False
        assert field.deserialize('true') is True
        assert field.deserialize('false') is False
        assert field.deserialize('1') is True
        assert field.deserialize('0') is False
        assert field.deserialize(1) is True
        assert field.deserialize(0) is False

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({})
        assert excinfo.value.args[0] == 'Not a valid boolean.'

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(42)

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('invalid-string')

    def test_boolean_field_deserialization_with_custom_truthy_values(self):
        class MyBoolean(fields.Boolean):
            truthy = set(['yep'])
        field = MyBoolean()
        assert field.deserialize('yep') is True

    @pytest.mark.parametrize('in_val',
    [
        'notvalid',
        123
    ])
    def test_boolean_field_deserialization_with_custom_truthy_values_invalid(
            self, in_val):
        class MyBoolean(fields.Boolean):
            truthy = set(['yep'])
        field = MyBoolean()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_val)
        expected_msg = 'Not a valid boolean.'
        assert str(excinfo.value.args[0]) == expected_msg
        field2 = MyBoolean(error_messages={'invalid': 'bad input'})
        with pytest.raises(ValidationError) as excinfo:
            field2.deserialize(in_val)
        assert str(excinfo.value.args[0]) == 'bad input'

    @pytest.mark.parametrize('in_value',
    [
        'not-a-datetime',
        42,
        '',
        [],
    ])
    def test_invalid_datetime_deserialization(self, in_value):
        field = fields.DateTime()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)
        msg = 'Not a valid datetime.'.format(in_value)
        assert msg in str(excinfo)

    def test_custom_date_format_datetime_field_deserialization(self):

        dtime = dt.datetime.now()
        datestring = dtime.strftime('%H:%M:%S %Y-%m-%d')

        field = fields.DateTime(format='%d-%m-%Y %H:%M:%S')
        #deserialization should fail when datestring is not of same format
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(datestring)
        msg = 'Not a valid datetime.'.format(datestring)
        assert msg in str(excinfo)
        field = fields.DateTime(format='%H:%M:%S %Y-%m-%d')
        assert_datetime_equal(field.deserialize(datestring), dtime)

        field = fields.DateTime()
        if utils.dateutil_available:
            assert_datetime_equal(field.deserialize(datestring), dtime)
        else:
            assert msg in str(excinfo)

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

    @pytest.mark.parametrize('in_data',
    [
        'badvalue',
        '',
        [],
        42,
    ])
    def test_invalid_time_field_deserialization(self, in_data):
        field = fields.Time()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_data)
        assert excinfo.value.args[0] == 'Not a valid time.'

    def test_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        result = field.deserialize('42')
        assert isinstance(result, dt.timedelta)
        assert result.days == 0
        assert result.seconds == 42
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        result = field.deserialize(100000)
        assert result.days == 1
        assert result.seconds == 13600
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        result = field.deserialize('-42')
        assert isinstance(result, dt.timedelta)
        assert result.days == -42
        assert result.seconds == 0
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        result = field.deserialize(10 ** 6 + 1)
        assert isinstance(result, dt.timedelta)
        assert result.days == 0
        assert result.seconds == 1
        assert result.microseconds == 1

        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        result = field.deserialize(86400 * 10 ** 6 + 1)
        assert isinstance(result, dt.timedelta)
        assert result.days == 1
        assert result.seconds == 0
        assert result.microseconds == 1

        field = fields.TimeDelta()
        result = field.deserialize(12.9)
        assert isinstance(result, dt.timedelta)
        assert result.days == 0
        assert result.seconds == 12
        assert result.microseconds == 0

    @pytest.mark.parametrize('in_value',
    [
        '',
        'badvalue',
        [],
        9999999999,
    ])
    def test_invalid_timedelta_field_deserialization(self, in_value):
        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)
        assert excinfo.value.args[0] == 'Not a valid period of time.'

    def test_date_field_deserialization(self):
        field = fields.Date()
        d = dt.date(2014, 8, 21)
        iso_date = d.isoformat()
        result = field.deserialize(iso_date)
        assert isinstance(result, dt.date)
        assert_date_equal(result, d)

    @pytest.mark.parametrize('in_value',
    [
        '',
        123,
        [],
    ])
    def test_invalid_date_field_deserialization(self, in_value):
        field = fields.Date()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)
        msg = 'Not a valid date.'
        assert excinfo.value.args[0] == msg

    def test_dict_field_deserialization(self):
        field = fields.Dict()
        assert field.deserialize({"foo": "bar"}) == {"foo": "bar"}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('baddict')
        assert excinfo.value.args[0] == 'Not a valid mapping type.'

    def test_url_field_deserialization(self):
        field = fields.Url()
        assert field.deserialize('https://duckduckgo.com') == 'https://duckduckgo.com'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('badurl')
        assert excinfo.value.args[0][0] == 'Not a valid URL.'
        # Relative URLS not allowed by default
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('/foo/bar')
        assert excinfo.value.args[0][0] == 'Not a valid URL.'

    def test_relative_url_field_deserialization(self):
        field = fields.Url(relative=True)
        assert field.deserialize('/foo/bar') == '/foo/bar'

    def test_email_field_deserialization(self):
        field = fields.Email()
        assert field.deserialize('foo@bar.com') == 'foo@bar.com'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('invalidemail')
        assert excinfo.value.args[0][0] == 'Not a valid email address.'

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
        result = field.deserialize(uuid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uuid_str

    @pytest.mark.parametrize('in_value',
    [
        'malformed',
        123,
        [],
    ])
    def test_invalid_uuid_deserialization(self, in_value):
        field = fields.UUID()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)

        assert excinfo.value.args[0] == 'Not a valid UUID.'

    def test_deserialization_function_must_be_callable(self):
        with pytest.raises(ValueError):
            fields.Function(lambda x: None,
                            deserialize='notvalid')

    def test_method_field_deserialization_is_noop_by_default(self):
        class MiniUserSchema(Schema):
            uppername = fields.Method('uppercase_name')

            def uppercase_name(self, obj):
                return obj.upper()
        user = User(name='steve')
        s = MiniUserSchema(user)
        assert s.fields['uppername'].deserialize('steve') == 'steve'

    def test_deserialization_method(self):
        class MiniUserSchema(Schema):
            uppername = fields.Method('uppercase_name', deserialize='lowercase_name')

            def uppercase_name(self, obj):
                return obj.name.upper()

            def lowercase_name(self, value):
                return value.lower()

        s = MiniUserSchema()
        assert s.fields['uppername'].deserialize('STEVE') == 'steve'

    def test_deserialization_method_must_be_a_method(self):
        class BadSchema(Schema):
            uppername = fields.Method('uppercase_name', deserialize='lowercase_name')

        s = BadSchema()
        with pytest.raises(ValueError):
            s.fields['uppername'].deserialize('STEVE')

    def test_query_select_field_func_key_deserialization(self):
        query = lambda: [DummyModel(ch) for ch in 'abc']

        field = fields.QuerySelect(query, str)
        assert field.deserialize('bar a') == DummyModel('a')
        assert field.deserialize('bar b') == DummyModel('b')
        assert field.deserialize('bar c') == DummyModel('c')
        with pytest.raises(ValidationError):
            field.deserialize('bar d')
        with pytest.raises(ValidationError):
            field.deserialize('c')
        assert list(field.keys()) == ['bar ' + ch for ch in 'abc']
        assert list(field.results()) == [DummyModel(ch) for ch in 'abc']
        assert list(field.pairs()) == [('bar ' + ch, DummyModel(ch)) for ch in 'abc']
        assert list(field.labels()) == [('bar ' + ch, 'bar ' + ch) for ch in 'abc']
        assert list(field.labels('foo')) == [('bar ' + ch, ch) for ch in 'abc']
        assert list(field.labels(str)) == [('bar ' + ch, 'bar ' + ch) for ch in 'abc']

    def test_query_select_field_string_key_deserialization(self):
        query = lambda: [DummyModel(ch) for ch in 'abc']

        field = fields.QuerySelect(query, 'foo')
        assert field.deserialize('a') == DummyModel('a')
        assert field.deserialize('b') == DummyModel('b')
        assert field.deserialize('c') == DummyModel('c')
        with pytest.raises(ValidationError):
            field.deserialize('d')
        with pytest.raises(ValidationError):
            field.deserialize('bar d')
        assert list(field.keys()) == [ch for ch in 'abc']
        assert list(field.results()) == [DummyModel(ch) for ch in 'abc']
        assert list(field.pairs()) == [(ch, DummyModel(ch)) for ch in 'abc']
        assert list(field.labels()) == [(ch, 'bar ' + ch) for ch in 'abc']
        assert list(field.labels('foo')) == [(ch, ch) for ch in 'abc']
        assert list(field.labels(str)) == [(ch, 'bar ' + ch) for ch in 'abc']

    def test_query_select_list_field_func_key_deserialization(self):
        query = lambda: [DummyModel(ch) for ch in 'abecde']

        field = fields.QuerySelectList(query, str)
        assert field.deserialize(['bar a', 'bar c', 'bar b']) == \
               [DummyModel('a'), DummyModel('c'), DummyModel('b')]
        assert field.deserialize(['bar d', 'bar e', 'bar e']) == \
               [DummyModel('d'), DummyModel('e'), DummyModel('e')]
        assert field.deserialize([]) == []
        with pytest.raises(ValidationError):
            field.deserialize(['a', 'b', 'f'])
        with pytest.raises(ValidationError):
            field.deserialize(['a', 'b', 'b'])

    def test_query_select_list_field_string_key_deserialization(self):
        query = lambda: [DummyModel(ch) for ch in 'abecde']

        field = fields.QuerySelectList(query, 'foo')
        assert field.deserialize(['a', 'c', 'b']) == \
               [DummyModel('a'), DummyModel('c'), DummyModel('b')]
        assert field.deserialize(['d', 'e', 'e']) == \
               [DummyModel('d'), DummyModel('e'), DummyModel('e')]
        assert field.deserialize([]) == []
        with pytest.raises(ValidationError):
            field.deserialize(['a', 'b', 'f'])
        with pytest.raises(ValidationError):
            field.deserialize(['a', 'b', 'b'])

    def test_datetime_list_field_deserialization(self):
        dtimes = dt.datetime.now(), dt.datetime.now(), dt.datetime.utcnow()
        dstrings = [each.isoformat() for each in dtimes]
        field = fields.List(fields.DateTime())
        result = field.deserialize(dstrings)
        assert all([isinstance(each, dt.datetime) for each in result])
        for actual, expected in zip(result, dtimes):
            assert_date_equal(actual, expected)

    def test_list_field_deserialize_invalid_item(self):
        field = fields.List(fields.DateTime)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(['badvalue'])
        assert excinfo.value.args[0] == 'Not a valid datetime.'

        field = fields.List(fields.Str())
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(['good', 42])
        assert excinfo.value.args[0] == 'Not a valid string.'

    @pytest.mark.parametrize('value',
    [
        'notalist',
        42,
        {},
    ])
    def test_list_field_deserialize_value_that_is_not_a_list(self, value):
        field = fields.List(fields.Str())
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(value)
        assert excinfo.value.args[0] == 'Not a valid list.'

    def test_constant_field_deserialization(self):
        field = fields.Constant('something')
        assert field.deserialize('whatever') == 'something'

    def test_field_deserialization_with_user_validator_function(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid')
        assert field.deserialize('Valid') == 'Valid'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('invalid')
        assert excinfo.value.args[0][0] == 'Invalid value.'
        assert type(excinfo.value) == ValidationError

    def test_field_deserialization_with_user_validator_class_that_returns_bool(self):
        class MyValidator(object):
            def __call__(self, val):
                if val == 'valid':
                    return True
                return False

        field = fields.Field(validate=MyValidator())
        assert field.deserialize('valid') == 'valid'
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('invalid')
        assert 'Invalid value.' in str(excinfo)

    def test_field_deserialization_with_user_validator_that_raises_error_with_list(self):
        def validator(val):
            raise ValidationError(['err1', 'err2'])

        class MySchema(Schema):
            foo = fields.Field(validate=validator)

        errors = MySchema().validate({'foo': 42})
        assert errors['foo'] == ['err1', 'err2']

    def test_validator_must_return_false_to_raise_error(self):
        # validator returns None, so anything validates
        field = fields.String(validate=lambda s: None)
        assert field.deserialize('Valid') == 'Valid'
        # validator returns False, so nothing validates
        field2 = fields.String(validate=lambda s: False)
        with pytest.raises(ValidationError):
            field2.deserialize('invalid')

    def test_field_deserialization_with_validator_with_nonascii_input(self):
        field = fields.String(validate=lambda s: False)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(u'привет')
        assert type(excinfo.value) == ValidationError

    def test_field_deserialization_with_user_validators(self):
        validators_gen = (func for func in (lambda s: s.lower() == 'valid',
                                            lambda s: s.lower()[::-1] == 'dilav'))

        m_colletion_type = [
            fields.String(validate=[lambda s: s.lower() == 'valid',
                lambda s: s.lower()[::-1] == 'dilav']),
            fields.String(validate=(lambda s: s.lower() == 'valid',
                lambda s: s.lower()[::-1] == 'dilav')),
            fields.String(validate=validators_gen)
        ]

        for field in m_colletion_type:
            assert field.deserialize('Valid') == 'Valid'
            with pytest.raises(ValidationError) as excinfo:
                field.deserialize('invalid')
            assert 'Invalid value.' in str(excinfo)

    def test_field_deserialization_with_custom_error_message(self):
        field = fields.String(validate=lambda s: s.lower() == 'valid',
                error_messages={'validator_failed': 'Bad value.'})
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize('invalid')
        assert 'Bad value.' in str(excinfo)

# No custom deserialization behavior, so a dict is returned
class SimpleUserSchema(Schema):
    name = fields.String()
    age = fields.Float()

class Validator(Schema):
    email = fields.Email()
    colors = fields.Str(validate=validate.OneOf(['red', 'blue']))
    age = fields.Integer(validate=lambda n: n > 0)

class Validators(Schema):
    email = fields.Email()
    colors = fields.Str(validate=validate.OneOf(['red', 'blue']))
    age = fields.Integer(validate=[lambda n: n > 0, lambda n: n < 100])

class TestSchemaDeserialization:

    def test_deserialize_to_dict(self):
        user_dict = {'name': 'Monty', 'age': '42.3'}
        result, errors = SimpleUserSchema().load(user_dict)
        assert result['name'] == 'Monty'
        assert_almost_equal(result['age'], 42.3)

    def test_deserialize_with_missing_values(self):
        user_dict = {'name': 'Monty'}
        result, errs = SimpleUserSchema().load(user_dict)
        # 'age' is not included in result
        assert result == {'name': 'Monty'}

    def test_deserialize_many(self):
        users_data = [
            {'name': 'Mick', 'age': '914'},
            {'name': 'Keith', 'age': '8442'}
        ]
        result, errors = SimpleUserSchema(many=True).load(users_data)
        assert isinstance(result, list)
        user = result[0]
        assert user['age'] == int(users_data[0]['age'])

    def test_exclude(self):
        schema = SimpleUserSchema(exclude=('age', ))
        result = schema.load({'name': 'Monty', 'age': 42})
        assert 'name' in result.data
        assert 'age' not in result.data

    def test_nested_single_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            author = fields.Nested(SimpleUserSchema)

        blog_dict = {
            'title': 'Gimme Shelter',
            'author': {'name': 'Mick', 'age': '914', 'email': 'mick@stones.com'}
        }
        result, errors = SimpleBlogSerializer().load(blog_dict)
        author = result['author']
        assert author['name'] == 'Mick'
        assert author['age'] == 914
        assert 'email' not in author

    def test_nested_list_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            authors = fields.Nested(SimpleUserSchema, many=True)

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

    def test_nested_single_none_not_allowed(self):
        class PetSchema(Schema):
            name = fields.Str()

        class OwnerSchema(Schema):
            pet = fields.Nested(PetSchema(), allow_none=False)

        sch = OwnerSchema()
        errors = sch.validate({'pet': None})
        assert 'pet' in errors
        assert errors['pet'] == ['Field may not be null.']

    def test_nested_many_non_not_allowed(self):
        class PetSchema(Schema):
            name = fields.Str()

        class StoreSchema(Schema):
            pets = fields.Nested(PetSchema(), allow_none=False, many=True)

        sch = StoreSchema()
        errors = sch.validate({'pets': None})
        assert 'pets' in errors
        assert errors['pets'] == ['Field may not be null.']

    def test_nested_single_required_missing(self):
        class PetSchema(Schema):
            name = fields.Str()

        class OwnerSchema(Schema):
            pet = fields.Nested(PetSchema(), required=True)

        sch = OwnerSchema()
        errors = sch.validate({})
        assert 'pet' in errors
        assert errors['pet'] == ['Missing data for required field.']

    def test_nested_many_required_missing(self):
        class PetSchema(Schema):
            name = fields.Str()

        class StoreSchema(Schema):
            pets = fields.Nested(PetSchema(), required=True, many=True)

        sch = StoreSchema()
        errors = sch.validate({})
        assert 'pets' in errors
        assert errors['pets'] == ['Missing data for required field.']

    def test_none_deserialization(self):
        result, errors = SimpleUserSchema().load(None)
        assert result is None

    def test_nested_none_deserialization(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            author = fields.Nested(SimpleUserSchema, allow_none=True)

        blog_dict = {
            'title': 'Gimme Shelter',
            'author': None
        }
        result, errors = SimpleBlogSerializer().load(blog_dict)
        assert not errors
        assert result['author'] is None
        assert result['title'] == blog_dict['title']

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

    def test_deserialize_with_attribute_param_error_returns_field_name_not_attribute_name(self):
        class AliasingUserSerializer(Schema):
            username = fields.Email(attribute='email')
            years = fields.Integer(attribute='age')
        data = {
            'username': 'foobar.com',
            'years': '42'
        }
        result, errors = AliasingUserSerializer().load(data)
        assert errors
        assert errors['username'] == ['Not a valid email address.']

    def test_deserialize_with_attribute_param_error_returns_load_from_not_attribute_name(self):
        class AliasingUserSerializer(Schema):
            name = fields.String(load_from='Name')
            username = fields.Email(attribute='email', load_from='UserName')
            years = fields.Integer(attribute='age', load_from='Years')
        data = {
            'Name': 'Mick',
            'UserName': 'foobar.com',
            'years': 'abc'
        }
        result, errors = AliasingUserSerializer().load(data)
        assert errors['UserName'] == [u'Not a valid email address.']
        assert errors['years'] == [u'Not a valid integer.']

    def test_deserialize_with_load_from_param(self):
        class AliasingUserSerializer(Schema):
            name = fields.String(load_from='Name')
            username = fields.Email(attribute='email', load_from='UserName')
            years = fields.Integer(attribute='age', load_from='Years')
        data = {
            'Name': 'Mick',
            'UserName': 'foo@bar.com',
            'years': '42'
        }
        result, errors = AliasingUserSerializer().load(data)
        assert result['name'] == 'Mick'
        assert result['email'] == 'foo@bar.com'
        assert result['age'] == 42

    def test_deserialize_with_dump_only_param(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(dump_only=True)
            nicknames = fields.List(fields.Str(), dump_only=True)
        data = {
            'name': 'Mick',
            'years': '42',
            'nicknames': ['Your Majesty', 'Brenda']
        }
        result, errors = AliasingUserSerializer().load(data)
        assert result['name'] == 'Mick'
        assert 'years' not in result
        assert 'nicknames' not in result

    def test_deserialize_with_missing_param_value(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(missing=10)
        data = {
            'name': 'Mick',
        }
        result, errors = AliasingUserSerializer().load(data)
        assert result['name'] == 'Mick'
        assert result['years'] == 10

    def test_deserialize_with_missing_param_callable(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(missing=lambda: 13 + 7)
        data = {
            'name': 'Mick',
        }
        result, errors = AliasingUserSerializer().load(data)
        assert result['name'] == 'Mick'
        assert result['years'] == 20

    def test_deserialize_with_missing_param_none(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(missing=None, allow_none=True)
        data = {
            'name': 'Mick',
        }
        result, errors = AliasingUserSerializer().load(data)
        assert not errors
        assert result['name'] == 'Mick'
        assert result['years'] is None

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
        with pytest.raises(ValidationError):
            v.load(bad_data)

    def test_strict_mode_many(self):
        bad_data = [
            {'email': 'foo@bar.com', 'colors': 'red', 'age': 18},
            {'email': 'bad', 'colors': 'pizza', 'age': -1}
        ]
        v = Validator(strict=True, many=True)
        with pytest.raises(ValidationError):
            v.load(bad_data)

    def test_strict_mode_deserialization_with_multiple_validators(self):
        bad_data = {
            'email': 'invalid-email',
            'colors': 'burger',
            'age': -1,
        }
        v = Validators(strict=True)
        with pytest.raises(ValidationError):
            v.load(bad_data)

    def test_uncaught_validation_errors_are_stored(self):
        def validate_field(val):
            raise ValidationError('Something went wrong')

        class MySchema(Schema):
            foo = fields.Field(validate=validate_field)

        _, errors = MySchema().load({'foo': 42})
        assert 'Something went wrong' in errors['foo']

    def test_multiple_errors_can_be_stored_for_a_field(self):

        def validate_with_bool(n):
            return False

        def validate_with_error(n):
            raise ValidationError('foo is not valid')

        class MySchema(Schema):
            foo = fields.Field(required=True, validate=[
                validate_with_bool,
                validate_with_error,
            ])
        _, errors = MySchema().load({'foo': 'bar'})

        assert type(errors['foo']) == list
        assert len(errors['foo']) == 2

    def test_multiple_errors_can_be_stored_for_an_email_field(self):
        def validate_with_bool(val):
            return False

        class MySchema(Schema):
            email = fields.Email(validate=[
                validate_with_bool,
            ])
        _, errors = MySchema().load({'email': 'foo'})
        assert len(errors['email']) == 2
        assert 'Not a valid email address.' in errors['email'][0]

    def test_multiple_errors_can_be_stored_for_a_url_field(self):
        def validate_with_bool(val):
            return False

        class MySchema(Schema):
            url = fields.Url(validate=[
                validate_with_bool,
            ])
        _, errors = MySchema().load({'url': 'foo'})
        assert len(errors['url']) == 2
        assert 'Not a valid URL.' in errors['url'][0]

    def test_required_value_only_passed_to_validators_if_provided(self):
        class MySchema(Schema):
            foo = fields.Field(required=True, validate=lambda f: False)

        _, errors = MySchema().load({})
        # required value missing
        assert len(errors['foo']) == 1
        assert 'Missing data for required field.' in errors['foo']

validators_gen = (func for func in [lambda x: x <= 24, lambda x: 18 <= x])

validators_gen_float = (func for func in
                         [lambda f: f <= 4.1, lambda f: f >= 1.0])

validators_gen_str = (func for func in
                        [lambda n: len(n) == 3, lambda n: n[1].lower() == 'o'])

class TestValidation:

    def test_integer_with_validator(self):
        field = fields.Integer(validate=lambda x: 18 <= x <= 24)
        out = field.deserialize('20')
        assert out == 20
        with pytest.raises(ValidationError):
            field.deserialize(25)

    @pytest.mark.parametrize('field', [
        fields.Integer(validate=[lambda x: x <= 24, lambda x: 18 <= x]),
        fields.Integer(validate=(lambda x: x <= 24, lambda x: 18 <= x, )),
        fields.Integer(validate=validators_gen)
    ])
    def test_integer_with_validators(self, field):
        out = field.deserialize('20')
        assert out == 20
        with pytest.raises(ValidationError):
            field.deserialize(25)

    @pytest.mark.parametrize('field', [
        fields.Float(validate=[lambda f: f <= 4.1, lambda f: f >= 1.0]),
        fields.Float(validate=(lambda f: f <= 4.1, lambda f: f >= 1.0, )),
        fields.Float(validate=validators_gen_float)
    ])
    def test_float_with_validators(self, field):
        assert field.deserialize(3.14)
        with pytest.raises(ValidationError):
            field.deserialize(4.2)

    def test_string_validator(self):
        field = fields.String(validate=lambda n: len(n) == 3)
        assert field.deserialize('Joe') == 'Joe'
        with pytest.raises(ValidationError):
            field.deserialize('joseph')

    def test_function_validator(self):
        field = fields.Function(lambda d: d.name.upper(),
                                validate=lambda n: len(n) == 3)
        assert field.deserialize('joe')
        with pytest.raises(ValidationError):
            field.deserialize('joseph')

    @pytest.mark.parametrize('field', [
        fields.Function(lambda d: d.name.upper(),
            validate=[lambda n: len(n) == 3, lambda n: n[1].lower() == 'o']),
        fields.Function(lambda d: d.name.upper(),
            validate=(lambda n: len(n) == 3, lambda n: n[1].lower() == 'o')),
        fields.Function(lambda d: d.name.upper(),
            validate=validators_gen_str)
    ])
    def test_function_validators(self, field):
        assert field.deserialize('joe')
        with pytest.raises(ValidationError):
            field.deserialize('joseph')

    def test_method_validator(self):
        class MethodSerializer(Schema):
            name = fields.Method('get_name', deserialize='get_name',
                                      validate=lambda n: len(n) == 3)

            def get_name(self, val):
                return val.upper()
        assert MethodSerializer(strict=True).load({'name': 'joe'})
        with pytest.raises(ValidationError) as excinfo:
            MethodSerializer(strict=True).load({'name': 'joseph'})

        assert 'Invalid value.' in str(excinfo)

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/269
    def test_nested_data_is_stored_when_validation_fails(self):
        class SchemaA(Schema):
            x = fields.Integer()
            y = fields.Integer(validate=lambda n: n > 0)
            z = fields.Integer()

        class SchemaB(Schema):
            w = fields.Integer()
            n = fields.Nested(SchemaA)

        sch = SchemaB()

        data, errors = sch.load({'w': 90, 'n': {'x': 90, 'y': 89, 'z': None}})
        assert 'z' in errors['n']
        assert data == {'w': 90, 'n': {'x': 90, 'y': 89}}

        data, errors = sch.load({'w': 90, 'n': {'x': 90, 'y': -1, 'z': 180}})
        assert 'y' in errors['n']
        assert data == {'w': 90, 'n': {'x': 90, 'z': 180}}


FIELDS_TO_TEST = [f for f in ALL_FIELDS if f not in [fields.FormattedString]]
@pytest.mark.parametrize('FieldClass', FIELDS_TO_TEST)
def test_required_field_failure(FieldClass):  # noqa
    class RequireSchema(Schema):
        age = FieldClass(required=True)
    user_data = {"name": "Phil"}
    data, errs = RequireSchema().load(user_data)
    assert "Missing data for required field." in errs['age']
    assert data == {}

@pytest.mark.parametrize('message', ['My custom required message',
                                     {'error': 'something', 'code': 400},
                                     ['first error', 'second error']])
def test_required_message_can_be_changed(message):
    class RequireSchema(Schema):
        age = fields.Integer(required=message)

    user_data = {"name": "Phil"}
    data, errs = RequireSchema().load(user_data)
    expected = [message] if isinstance(message, basestring) else message
    assert expected == errs['age']
    assert data == {}

# Regression test for https://github.com/marshmallow-code/marshmallow/issues/261
def test_deserialize_doesnt_raise_exception_if_strict_is_false_and_input_type_is_incorrect():
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.Field()
    data, errs = MySchema().load([])
    assert '_schema' in errs
    assert errs['_schema'] == ['Invalid input type.']


def test_deserialize_raises_exception_if_strict_is_true_and_input_type_is_incorrect():
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.Field()
    with pytest.raises(ValidationError) as excinfo:
        MySchema(strict=True).load([])
    assert 'Invalid input type.' in str(excinfo)
    exc = excinfo.value
    assert exc.field_names == ['_schema']
    assert exc.fields == []
