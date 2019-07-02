import datetime as dt
import uuid
import decimal
import math

import pytest

from marshmallow import EXCLUDE, INCLUDE, RAISE, fields, utils, Schema, validate
from marshmallow.exceptions import ValidationError
from marshmallow.validate import Equal

from tests.base import (
    assert_date_equal,
    assert_datetime_equal,
    assert_time_equal,
    central,
    ALL_FIELDS,
)


class TestDeserializingNone:
    @pytest.mark.parametrize("FieldClass", ALL_FIELDS)
    def test_fields_allow_none_deserialize_to_none(self, FieldClass):
        field = FieldClass(allow_none=True)
        field.deserialize(None) is None

    # https://github.com/marshmallow-code/marshmallow/issues/111
    @pytest.mark.parametrize("FieldClass", ALL_FIELDS)
    def test_fields_dont_allow_none_by_default(self, FieldClass):
        field = FieldClass()
        with pytest.raises(ValidationError, match="Field may not be null."):
            field.deserialize(None)

    def test_allow_none_is_true_if_missing_is_true(self):
        field = fields.Field(missing=None)
        assert field.allow_none is True
        field.deserialize(None) is None

    def test_list_field_deserialize_none_to_none(self):
        field = fields.List(fields.String(allow_none=True), allow_none=True)
        assert field.deserialize(None) is None

    def test_tuple_field_deserialize_none_to_none(self):
        field = fields.Tuple([fields.String()], allow_none=True)
        assert field.deserialize(None) is None


class TestFieldDeserialization:
    def test_float_field_deserialization(self):
        field = fields.Float()
        assert math.isclose(field.deserialize("12.3"), 12.3)
        assert math.isclose(field.deserialize(12.3), 12.3)

    @pytest.mark.parametrize("in_val", ["bad", "", {}])
    def test_invalid_float_field_deserialization(self, in_val):
        field = fields.Float()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_val)
        assert excinfo.value.args[0] == "Not a valid number."

    def test_float_field_overflow(self):
        field = fields.Float()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(2 ** 1024)
        assert excinfo.value.args[0] == "Number too large."

    def test_integer_field_deserialization(self):
        field = fields.Integer()
        assert field.deserialize("42") == 42
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("42.0")
        assert excinfo.value.args[0] == "Not a valid integer."
        with pytest.raises(ValidationError):
            field.deserialize("bad")
        assert excinfo.value.args[0] == "Not a valid integer."
        with pytest.raises(ValidationError):
            field.deserialize({})
        assert excinfo.value.args[0] == "Not a valid integer."

    def test_strict_integer_field_deserialization(self):
        field = fields.Integer(strict=True)
        assert field.deserialize(42) == 42
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(42.0)
        assert excinfo.value.args[0] == "Not a valid integer."
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(decimal.Decimal("42.0"))
        assert excinfo.value.args[0] == "Not a valid integer."
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("42")
        assert excinfo.value.args[0] == "Not a valid integer."

    def test_decimal_field_deserialization(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = 3.14
        m5 = "abc"
        m6 = [1, 2]

        field = fields.Decimal()
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal("12.355")
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        assert isinstance(field.deserialize(m4), decimal.Decimal)
        assert field.deserialize(m4).as_tuple() == (0, (3, 1, 4), -2)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m5)
        assert excinfo.value.args[0] == "Not a valid number."
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m6)
        assert excinfo.value.args[0] == "Not a valid number."

    def test_decimal_field_with_places(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = "abc"
        m5 = [1, 2]

        field = fields.Decimal(1)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal("12.4")
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m4)
        assert excinfo.value.args[0] == "Not a valid number."
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m5)
        assert excinfo.value.args[0] == "Not a valid number."

    def test_decimal_field_with_places_and_rounding(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = "abc"
        m5 = [1, 2]

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal("12.3")
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError):
            field.deserialize(m4)
        with pytest.raises(ValidationError):
            field.deserialize(m5)

    def test_decimal_field_deserialization_string(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = "abc"
        m5 = [1, 2]

        field = fields.Decimal(as_string=True)
        assert isinstance(field.deserialize(m1), decimal.Decimal)
        assert field.deserialize(m1) == decimal.Decimal(12)
        assert isinstance(field.deserialize(m2), decimal.Decimal)
        assert field.deserialize(m2) == decimal.Decimal("12.355")
        assert isinstance(field.deserialize(m3), decimal.Decimal)
        assert field.deserialize(m3) == decimal.Decimal(1)
        with pytest.raises(ValidationError):
            field.deserialize(m4)
        with pytest.raises(ValidationError):
            field.deserialize(m5)

    def test_decimal_field_special_values(self):
        m1 = "-NaN"
        m2 = "NaN"
        m3 = "-sNaN"
        m4 = "sNaN"
        m5 = "-Infinity"
        m6 = "Infinity"
        m7 = "-0"

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
        m1 = "-NaN"
        m2 = "NaN"
        m3 = "-sNaN"
        m4 = "sNaN"
        m5 = "-Infinity"
        m6 = "Infinity"
        m7 = "-0"

        field = fields.Decimal(places=2)

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(m1)
        assert str(excinfo.value.args[0]) == (
            "Special numeric values (nan or infinity) are not permitted."
        )
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

    @pytest.mark.parametrize("allow_nan", (None, False, True))
    @pytest.mark.parametrize("value", ("nan", "-nan", "inf", "-inf"))
    def test_float_field_allow_nan(self, value, allow_nan):

        if allow_nan is None:
            # Test default case is False
            field = fields.Float()
        else:
            field = fields.Float(allow_nan=allow_nan)

        if allow_nan is True:
            res = field.deserialize(value)
            assert isinstance(res, float)
            if value.endswith("nan"):
                assert math.isnan(res)
            else:
                assert res == float(value)
        else:
            with pytest.raises(ValidationError) as excinfo:
                field.deserialize(value)
            assert str(excinfo.value.args[0]) == (
                "Special numeric values (nan or infinity) are not permitted."
            )

    def test_string_field_deserialization(self):
        field = fields.String()
        assert field.deserialize("foo") == "foo"
        assert field.deserialize(b"foo") == "foo"

        # https://github.com/marshmallow-code/marshmallow/issues/231
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(42)
        assert excinfo.value.args[0] == "Not a valid string."

        with pytest.raises(ValidationError):
            field.deserialize({})

    def test_boolean_field_deserialization(self):
        field = fields.Boolean()
        assert field.deserialize(True) is True
        assert field.deserialize(False) is False
        assert field.deserialize("True") is True
        assert field.deserialize("False") is False
        assert field.deserialize("true") is True
        assert field.deserialize("false") is False
        assert field.deserialize("1") is True
        assert field.deserialize("0") is False
        assert field.deserialize("on") is True
        assert field.deserialize("ON") is True
        assert field.deserialize("On") is True
        assert field.deserialize("off") is False
        assert field.deserialize("OFF") is False
        assert field.deserialize("Off") is False
        assert field.deserialize("y") is True
        assert field.deserialize("Y") is True
        assert field.deserialize("yes") is True
        assert field.deserialize("YES") is True
        assert field.deserialize("Yes") is True
        assert field.deserialize("n") is False
        assert field.deserialize("N") is False
        assert field.deserialize("no") is False
        assert field.deserialize("NO") is False
        assert field.deserialize("No") is False
        assert field.deserialize(1) is True
        assert field.deserialize(0) is False

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({})
        assert excinfo.value.args[0] == "Not a valid boolean."

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(42)

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("invalid-string")

    def test_boolean_field_deserialization_with_custom_truthy_values(self):
        class MyBoolean(fields.Boolean):
            truthy = {"yep"}

        field = MyBoolean()
        assert field.deserialize("yep") is True

        field = fields.Boolean(truthy=("yep",))
        assert field.deserialize("yep") is True
        assert field.deserialize(False) is False

    @pytest.mark.parametrize("in_val", ["notvalid", 123])
    def test_boolean_field_deserialization_with_custom_truthy_values_invalid(
        self, in_val
    ):
        class MyBoolean(fields.Boolean):
            truthy = {"yep"}

        field = MyBoolean()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_val)
        expected_msg = "Not a valid boolean."
        assert str(excinfo.value.args[0]) == expected_msg

        field = fields.Boolean(truthy=("yep",))
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_val)
        expected_msg = "Not a valid boolean."
        assert str(excinfo.value.args[0]) == expected_msg

        field2 = MyBoolean(error_messages={"invalid": "bad input"})
        with pytest.raises(ValidationError) as excinfo:
            field2.deserialize(in_val)
        assert str(excinfo.value.args[0]) == "bad input"

        field2 = fields.Boolean(
            truthy=("yep",), error_messages={"invalid": "bad input"}
        )

    def test_boolean_field_deserialization_with_empty_truthy(self):
        field = fields.Boolean(truthy=())
        assert field.deserialize("yep") is True
        assert field.deserialize(True) is True
        assert field.deserialize(False) is False

    def test_boolean_field_deserialization_with_custom_falsy_values(self):
        field = fields.Boolean(falsy=("nope",))
        assert field.deserialize("nope") is False
        assert field.deserialize(True) is True

    def test_field_toggle_show_invalid_value_in_error_message(self):
        error_messages = {"invalid": "Not valid: {input}"}
        boolfield = fields.Boolean(error_messages=error_messages)
        with pytest.raises(ValidationError) as excinfo:
            boolfield.deserialize("notabool")
        assert str(excinfo.value.args[0]) == "Not valid: notabool"

        numfield = fields.Number(error_messages=error_messages)
        with pytest.raises(ValidationError) as excinfo:
            numfield.deserialize("notanum")
        assert str(excinfo.value.args[0]) == "Not valid: notanum"

        intfield = fields.Integer(error_messages=error_messages)
        with pytest.raises(ValidationError) as excinfo:
            intfield.deserialize("notanint")
        assert str(excinfo.value.args[0]) == "Not valid: notanint"

        date_error_messages = {"invalid": "Not a valid {obj_type}: {input}"}
        datefield = fields.DateTime(error_messages=date_error_messages)
        with pytest.raises(ValidationError) as excinfo:
            datefield.deserialize("notadate")
        assert str(excinfo.value.args[0]) == "Not a valid datetime: notadate"

    @pytest.mark.parametrize(
        "in_value",
        [
            "not-a-datetime",
            42,
            "",
            [],
            "2018-01-01",
            dt.datetime.now().strftime("%H:%M:%S %Y-%m-%d"),
            dt.datetime.now().strftime("%m-%d-%Y %H:%M:%S"),
        ],
    )
    def test_invalid_datetime_deserialization(self, in_value):
        field = fields.DateTime()
        with pytest.raises(ValidationError, match="Not a valid datetime."):
            field.deserialize(in_value)

    def test_datetime_passed_year_is_invalid(self):
        field = fields.DateTime()
        with pytest.raises(ValidationError):
            field.deserialize("1916")

    def test_datetime_passed_date_is_invalid(self):
        field = fields.DateTime()
        with pytest.raises(ValidationError):
            field.deserialize("2017-04-13")

    def test_custom_date_format_datetime_field_deserialization(self):
        dtime = dt.datetime.now()
        datestring = dtime.strftime("%H:%M:%S.%f %Y-%m-%d")

        field = fields.DateTime(format="%d-%m-%Y %H:%M:%S")
        # deserialization should fail when datestring is not of same format
        with pytest.raises(ValidationError, match="Not a valid datetime."):
            field.deserialize(datestring)
        field = fields.DateTime(format="%H:%M:%S.%f %Y-%m-%d")
        assert_datetime_equal(field.deserialize(datestring), dtime)

    @pytest.mark.parametrize("fmt", ["rfc", "rfc822"])
    def test_rfc_datetime_field_deserialization(self, fmt):
        dtime = dt.datetime.now().replace(microsecond=0)
        datestring = utils.rfcformat(dtime)
        field = fields.DateTime(format=fmt)
        assert_datetime_equal(field.deserialize(datestring), dtime)

    @pytest.mark.parametrize("fmt", ["iso", "iso8601"])
    def test_iso_datetime_field_deserialization(self, fmt):
        dtime = dt.datetime.now()
        datestring = dtime.isoformat()
        field = fields.DateTime(format=fmt)
        assert_datetime_equal(field.deserialize(datestring), dtime)

    def test_localdatetime_field_deserialization(self):
        dtime = dt.datetime.now()
        localized_dtime = central.localize(dtime)
        field = fields.DateTime(format="iso")
        result = field.deserialize(localized_dtime.isoformat())
        assert_datetime_equal(result, dtime)
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

    @pytest.mark.parametrize("in_data", ["badvalue", "", [], 42])
    def test_invalid_time_field_deserialization(self, in_data):
        field = fields.Time()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_data)
        assert excinfo.value.args[0] == "Not a valid time."

    def test_invalid_timedelta_precision(self):
        with pytest.raises(ValueError, match='The precision must be "days",'):
            fields.TimeDelta("invalid")

    def test_timedelta_field_deserialization(self):
        field = fields.TimeDelta()
        result = field.deserialize("42")
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
        result = field.deserialize("-42")
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

        field = fields.TimeDelta(fields.TimeDelta.WEEKS)
        result = field.deserialize(1)
        assert isinstance(result, dt.timedelta)
        assert result.days == 7
        assert result.seconds == 0
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        result = field.deserialize(25)
        assert isinstance(result, dt.timedelta)
        assert result.days == 1
        assert result.seconds == 3600
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.MINUTES)
        result = field.deserialize(1441)
        assert isinstance(result, dt.timedelta)
        assert result.days == 1
        assert result.seconds == 60
        assert result.microseconds == 0

        field = fields.TimeDelta(fields.TimeDelta.MILLISECONDS)
        result = field.deserialize(123456)
        assert isinstance(result, dt.timedelta)
        assert result.days == 0
        assert result.seconds == 123
        assert result.microseconds == 456000

    @pytest.mark.parametrize("in_value", ["", "badvalue", [], 9999999999])
    def test_invalid_timedelta_field_deserialization(self, in_value):
        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)
        assert excinfo.value.args[0] == "Not a valid period of time."

    @pytest.mark.parametrize("format", (None, "%Y-%m-%d"))
    def test_date_field_deserialization(self, format):
        field = fields.Date(format=format)
        d = dt.date(2014, 8, 21)
        iso_date = d.isoformat()
        result = field.deserialize(iso_date)
        assert type(result) == dt.date
        assert_date_equal(result, d)

    @pytest.mark.parametrize(
        "in_value", ["", 123, [], dt.date(2014, 8, 21).strftime("%d-%m-%Y")]
    )
    def test_invalid_date_field_deserialization(self, in_value):
        field = fields.Date()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)
        msg = "Not a valid date."
        assert excinfo.value.args[0] == msg

    def test_dict_field_deserialization(self):
        field = fields.Dict()
        assert field.deserialize({"foo": "bar"}) == {"foo": "bar"}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("baddict")
        assert excinfo.value.args[0] == "Not a valid mapping type."

    def test_structured_dict_value_deserialization(self):
        field = fields.Dict(values=fields.List(fields.Str))
        assert field.deserialize({"foo": ["bar", "baz"]}) == {"foo": ["bar", "baz"]}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({"foo": [1, 2], "bar": "baz", "ham": ["spam"]})
        assert excinfo.value.args[0] == {
            "foo": {"value": {0: ["Not a valid string."], 1: ["Not a valid string."]}},
            "bar": {"value": ["Not a valid list."]},
        }
        assert excinfo.value.valid_data == {"foo": [], "ham": ["spam"]}

    def test_structured_dict_key_deserialization(self):
        field = fields.Dict(keys=fields.Str)
        assert field.deserialize({"foo": "bar"}) == {"foo": "bar"}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({1: "bar", "foo": "baz"})
        assert excinfo.value.args[0] == {1: {"key": ["Not a valid string."]}}
        assert excinfo.value.valid_data == {"foo": "baz"}

    def test_structured_dict_key_value_deserialization(self):
        field = fields.Dict(
            keys=fields.Str(
                validate=[validate.Email(), validate.Regexp(r".*@test\.com$")]
            ),
            values=fields.Decimal,
        )
        assert field.deserialize({"foo@test.com": 1}) == {
            "foo@test.com": decimal.Decimal(1)
        }
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({1: "bar"})
        assert excinfo.value.args[0] == {
            1: {"key": ["Not a valid string."], "value": ["Not a valid number."]}
        }
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({"foo@test.com": "bar"})
        assert excinfo.value.args[0] == {
            "foo@test.com": {"value": ["Not a valid number."]}
        }
        assert excinfo.value.valid_data == {}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({1: 1})
        assert excinfo.value.args[0] == {1: {"key": ["Not a valid string."]}}
        assert excinfo.value.valid_data == {}
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize({"foo": "bar"})
        assert excinfo.value.args[0] == {
            "foo": {
                "key": [
                    "Not a valid email address.",
                    "String does not match expected pattern.",
                ],
                "value": ["Not a valid number."],
            }
        }
        assert excinfo.value.valid_data == {}

    def test_url_field_deserialization(self):
        field = fields.Url()
        assert field.deserialize("https://duckduckgo.com") == "https://duckduckgo.com"
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("badurl")
        assert excinfo.value.args[0][0] == "Not a valid URL."
        # Relative URLS not allowed by default
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("/foo/bar")
        assert excinfo.value.args[0][0] == "Not a valid URL."

    def test_relative_url_field_deserialization(self):
        field = fields.Url(relative=True)
        assert field.deserialize("/foo/bar") == "/foo/bar"

    def test_url_field_schemes_argument(self):
        field = fields.URL()
        url = "ws://test.test"
        with pytest.raises(ValidationError):
            field.deserialize(url)
        field2 = fields.URL(schemes={"http", "https", "ws"})
        assert field2.deserialize(url) == url

    def test_email_field_deserialization(self):
        field = fields.Email()
        assert field.deserialize("foo@bar.com") == "foo@bar.com"
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("invalidemail")
        assert excinfo.value.args[0][0] == "Not a valid email address."

    def test_function_field_deserialization_is_noop_by_default(self):
        field = fields.Function(lambda x: None)
        # Default is noop
        assert field.deserialize("foo") == "foo"
        assert field.deserialize(42) == 42

    def test_function_field_deserialization_with_callable(self):
        field = fields.Function(lambda x: None, deserialize=lambda val: val.upper())
        assert field.deserialize("foo") == "FOO"

    def test_function_field_deserialization_with_context(self):
        class Parent(Schema):
            pass

        field = fields.Function(
            lambda x: None,
            deserialize=lambda val, context: val.upper() + context["key"],
        )
        field.parent = Parent(context={"key": "BAR"})
        assert field.deserialize("foo") == "FOOBAR"

    def test_function_field_passed_deserialize_only_is_load_only(self):
        field = fields.Function(deserialize=lambda val: val.upper())
        assert field.load_only is True

    def test_function_field_passed_deserialize_and_serialize_is_not_load_only(self):
        field = fields.Function(
            serialize=lambda val: val.lower(), deserialize=lambda val: val.upper()
        )
        assert field.load_only is False

    def test_uuid_field_deserialization(self):
        field = fields.UUID()
        uuid_str = str(uuid.uuid4())
        result = field.deserialize(uuid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uuid_str

        uuid4 = uuid.uuid4()
        result = field.deserialize(uuid4)
        assert isinstance(result, uuid.UUID)
        assert result == uuid4

        uuid_bytes = b"]\xc7wW\x132O\xf9\xa5\xbe\x13\x1f\x02\x18\xda\xbf"
        result = field.deserialize(uuid_bytes)
        assert isinstance(result, uuid.UUID)
        assert result.bytes == uuid_bytes

    @pytest.mark.parametrize("in_value", ["malformed", 123, [], b"tooshort"])
    def test_invalid_uuid_deserialization(self, in_value):
        field = fields.UUID()
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(in_value)

        assert excinfo.value.args[0] == "Not a valid UUID."

    def test_deserialization_function_must_be_callable(self):
        with pytest.raises(ValueError):
            fields.Function(lambda x: None, deserialize="notvalid")

    def test_method_field_deserialization_is_noop_by_default(self):
        class MiniUserSchema(Schema):
            uppername = fields.Method("uppercase_name")

            def uppercase_name(self, obj):
                return obj.upper()

        s = MiniUserSchema()
        assert s.fields["uppername"].deserialize("steve") == "steve"

    def test_deserialization_method(self):
        class MiniUserSchema(Schema):
            uppername = fields.Method("uppercase_name", deserialize="lowercase_name")

            def uppercase_name(self, obj):
                return obj.name.upper()

            def lowercase_name(self, value):
                return value.lower()

        s = MiniUserSchema()
        assert s.fields["uppername"].deserialize("STEVE") == "steve"

    def test_deserialization_method_must_be_a_method(self):
        class BadSchema(Schema):
            uppername = fields.Method("uppercase_name", deserialize="lowercase_name")

        s = BadSchema()
        with pytest.raises(ValueError):
            s.fields["uppername"].deserialize("STEVE")

    def test_method_field_deserialize_only(self):
        class MethodDeserializeOnly(Schema):
            def lowercase_name(self, value):
                return value.lower()

        m = fields.Method(deserialize="lowercase_name")
        m.parent = MethodDeserializeOnly()

        assert m.deserialize("ALEC") == "alec"

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
            field.deserialize(["badvalue"])
        assert excinfo.value.args[0] == {0: ["Not a valid datetime."]}

        field = fields.List(fields.Str())
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(["good", 42])
        assert excinfo.value.args[0] == {1: ["Not a valid string."]}

    def test_list_field_deserialize_multiple_invalid_items(self):
        field = fields.List(
            fields.Int(
                validate=validate.Range(10, 20, error="Value {input} not in range")
            )
        )
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize([10, 5, 25])
        assert len(excinfo.value.args[0]) == 2
        assert excinfo.value.args[0][1] == ["Value 5 not in range"]
        assert excinfo.value.args[0][2] == ["Value 25 not in range"]

    @pytest.mark.parametrize("value", ["notalist", 42, {}])
    def test_list_field_deserialize_value_that_is_not_a_list(self, value):
        field = fields.List(fields.Str())
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(value)
        assert excinfo.value.args[0] == "Not a valid list."

    def test_datetime_int_tuple_field_deserialization(self):
        dtime = dt.datetime.now()
        data = dtime.isoformat(), 42
        field = fields.Tuple([fields.DateTime(), fields.Integer()])
        result = field.deserialize(data)

        assert isinstance(result, tuple)
        assert len(result) == 2
        for val, type_, true_val in zip(result, (dt.datetime, int), (dtime, 42)):
            assert isinstance(val, type_)
            assert val == true_val

    def test_tuple_field_deserialize_invalid_item(self):
        field = fields.Tuple([fields.DateTime])
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(["badvalue"])
        assert excinfo.value.args[0] == {0: ["Not a valid datetime."]}

        field = fields.Tuple([fields.Str(), fields.Integer()])
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(["good", "bad"])
        assert excinfo.value.args[0] == {1: ["Not a valid integer."]}

    def test_tuple_field_deserialize_multiple_invalid_items(self):
        validator = validate.Range(10, 20, error="Value {input} not in range")
        field = fields.Tuple(
            [
                fields.Int(validate=validator),
                fields.Int(validate=validator),
                fields.Int(validate=validator),
            ]
        )

        with pytest.raises(ValidationError) as excinfo:
            field.deserialize([10, 5, 25])
        assert len(excinfo.value.args[0]) == 2
        assert excinfo.value.args[0][1] == ["Value 5 not in range"]
        assert excinfo.value.args[0][2] == ["Value 25 not in range"]

    @pytest.mark.parametrize("value", ["notalist", 42, {}])
    def test_tuple_field_deserialize_value_that_is_not_a_collection(self, value):
        field = fields.Tuple([fields.Str()])
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize(value)
        assert excinfo.value.args[0] == "Not a valid tuple."

    def test_tuple_field_deserialize_invalid_length(self):
        field = fields.Tuple([fields.Str(), fields.Str()])
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize([42])
        assert excinfo.value.args[0] == "Length must be 2."

    def test_constant_field_deserialization(self):
        field = fields.Constant("something")
        assert field.deserialize("whatever") == "something"

    def test_constant_is_always_included_in_deserialized_data(self):
        class MySchema(Schema):
            foo = fields.Constant(42)

        sch = MySchema()
        assert sch.load({})["foo"] == 42
        assert sch.load({"foo": 24})["foo"] == 42

    def test_field_deserialization_with_user_validator_function(self):
        field = fields.String(validate=lambda s: s.lower() == "valid")
        assert field.deserialize("Valid") == "Valid"
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("invalid")
        assert excinfo.value.args[0][0] == "Invalid value."
        assert type(excinfo.value) == ValidationError

    def test_field_deserialization_with_user_validator_class_that_returns_bool(self):
        class MyValidator:
            def __call__(self, val):
                if val == "valid":
                    return True
                return False

        field = fields.Field(validate=MyValidator())
        assert field.deserialize("valid") == "valid"
        with pytest.raises(ValidationError, match="Invalid value."):
            field.deserialize("invalid")

    def test_field_deserialization_with_user_validator_that_raises_error_with_list(
        self
    ):
        def validator(val):
            raise ValidationError(["err1", "err2"])

        class MySchema(Schema):
            foo = fields.Field(validate=validator)

        errors = MySchema().validate({"foo": 42})
        assert errors["foo"] == ["err1", "err2"]

    def test_validator_must_return_false_to_raise_error(self):
        # validator returns None, so anything validates
        field = fields.String(validate=lambda s: None)
        assert field.deserialize("Valid") == "Valid"
        # validator returns False, so nothing validates
        field2 = fields.String(validate=lambda s: False)
        with pytest.raises(ValidationError):
            field2.deserialize("invalid")

    def test_field_deserialization_with_validator_with_nonascii_input(self):
        field = fields.String(validate=lambda s: False)
        with pytest.raises(ValidationError) as excinfo:
            field.deserialize("привет")
        assert type(excinfo.value) == ValidationError

    def test_field_deserialization_with_user_validators(self):
        validators_gen = (
            func
            for func in (
                lambda s: s.lower() == "valid",
                lambda s: s.lower()[::-1] == "dilav",
            )
        )

        m_colletion_type = [
            fields.String(
                validate=[
                    lambda s: s.lower() == "valid",
                    lambda s: s.lower()[::-1] == "dilav",
                ]
            ),
            fields.String(
                validate=(
                    lambda s: s.lower() == "valid",
                    lambda s: s.lower()[::-1] == "dilav",
                )
            ),
            fields.String(validate=validators_gen),
        ]

        for field in m_colletion_type:
            assert field.deserialize("Valid") == "Valid"
            with pytest.raises(ValidationError, match="Invalid value."):
                field.deserialize("invalid")

    def test_field_deserialization_with_custom_error_message(self):
        field = fields.String(
            validate=lambda s: s.lower() == "valid",
            error_messages={"validator_failed": "Bad value."},
        )
        with pytest.raises(ValidationError, match="Bad value."):
            field.deserialize("invalid")


# No custom deserialization behavior, so a dict is returned
class SimpleUserSchema(Schema):
    name = fields.String()
    age = fields.Float()


class Validator(Schema):
    email = fields.Email()
    colors = fields.Str(validate=validate.OneOf(["red", "blue"]))
    age = fields.Integer(validate=lambda n: n > 0)


class Validators(Schema):
    email = fields.Email()
    colors = fields.Str(validate=validate.OneOf(["red", "blue"]))
    age = fields.Integer(validate=[lambda n: n > 0, lambda n: n < 100])


class TestSchemaDeserialization:
    def test_deserialize_to_dict(self):
        user_dict = {"name": "Monty", "age": "42.3"}
        result = SimpleUserSchema().load(user_dict)
        assert result["name"] == "Monty"
        assert math.isclose(result["age"], 42.3)

    def test_deserialize_with_missing_values(self):
        user_dict = {"name": "Monty"}
        result = SimpleUserSchema().load(user_dict)
        # 'age' is not included in result
        assert result == {"name": "Monty"}

    def test_deserialize_many(self):
        users_data = [{"name": "Mick", "age": "914"}, {"name": "Keith", "age": "8442"}]
        result = SimpleUserSchema(many=True).load(users_data)
        assert isinstance(result, list)
        user = result[0]
        assert user["age"] == int(users_data[0]["age"])

    def test_exclude(self):
        schema = SimpleUserSchema(exclude=("age",), unknown=EXCLUDE)
        result = schema.load({"name": "Monty", "age": 42})
        assert "name" in result
        assert "age" not in result

    def test_nested_single_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            author = fields.Nested(SimpleUserSchema, unknown=EXCLUDE)

        blog_dict = {
            "title": "Gimme Shelter",
            "author": {"name": "Mick", "age": "914", "email": "mick@stones.com"},
        }
        result = SimpleBlogSerializer().load(blog_dict)
        author = result["author"]
        assert author["name"] == "Mick"
        assert author["age"] == 914
        assert "email" not in author

    def test_nested_list_deserialization_to_dict(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            authors = fields.Nested(SimpleUserSchema, many=True)

        blog_dict = {
            "title": "Gimme Shelter",
            "authors": [
                {"name": "Mick", "age": "914"},
                {"name": "Keith", "age": "8442"},
            ],
        }
        result = SimpleBlogSerializer().load(blog_dict)
        assert isinstance(result["authors"], list)
        author = result["authors"][0]
        assert author["name"] == "Mick"
        assert author["age"] == 914

    def test_nested_single_none_not_allowed(self):
        class PetSchema(Schema):
            name = fields.Str()

        class OwnerSchema(Schema):
            pet = fields.Nested(PetSchema(), allow_none=False)

        sch = OwnerSchema()
        errors = sch.validate({"pet": None})
        assert "pet" in errors
        assert errors["pet"] == ["Field may not be null."]

    def test_nested_many_non_not_allowed(self):
        class PetSchema(Schema):
            name = fields.Str()

        class StoreSchema(Schema):
            pets = fields.Nested(PetSchema(), allow_none=False, many=True)

        sch = StoreSchema()
        errors = sch.validate({"pets": None})
        assert "pets" in errors
        assert errors["pets"] == ["Field may not be null."]

    def test_nested_single_required_missing(self):
        class PetSchema(Schema):
            name = fields.Str()

        class OwnerSchema(Schema):
            pet = fields.Nested(PetSchema(), required=True)

        sch = OwnerSchema()
        errors = sch.validate({})
        assert "pet" in errors
        assert errors["pet"] == ["Missing data for required field."]

    def test_nested_many_required_missing(self):
        class PetSchema(Schema):
            name = fields.Str()

        class StoreSchema(Schema):
            pets = fields.Nested(PetSchema(), required=True, many=True)

        sch = StoreSchema()
        errors = sch.validate({})
        assert "pets" in errors
        assert errors["pets"] == ["Missing data for required field."]

    def test_nested_only_basestring(self):
        class ANestedSchema(Schema):
            pk = fields.Str()

        class MainSchema(Schema):
            pk = fields.Str()
            child = fields.Pluck(ANestedSchema, "pk")

        sch = MainSchema()
        result = sch.load({"pk": "123", "child": "456"})
        assert result["child"]["pk"] == "456"

    def test_nested_only_basestring_with_list_data(self):
        class ANestedSchema(Schema):
            pk = fields.Str()

        class MainSchema(Schema):
            pk = fields.Str()
            children = fields.Pluck(ANestedSchema, "pk", many=True)

        sch = MainSchema()
        result = sch.load({"pk": "123", "children": ["456", "789"]})
        assert result["children"][0]["pk"] == "456"
        assert result["children"][1]["pk"] == "789"

    def test_nested_none_deserialization(self):
        class SimpleBlogSerializer(Schema):
            title = fields.String()
            author = fields.Nested(SimpleUserSchema, allow_none=True)

        blog_dict = {"title": "Gimme Shelter", "author": None}
        result = SimpleBlogSerializer().load(blog_dict)
        assert result["author"] is None
        assert result["title"] == blog_dict["title"]

    def test_deserialize_with_attribute_param(self):
        class AliasingUserSerializer(Schema):
            username = fields.Email(attribute="email")
            years = fields.Integer(attribute="age")

        data = {"username": "foo@bar.com", "years": "42"}
        result = AliasingUserSerializer().load(data)
        assert result["email"] == "foo@bar.com"
        assert result["age"] == 42

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/450
    def test_deserialize_with_attribute_param_symmetry(self):
        class MySchema(Schema):
            foo = fields.Field(attribute="bar.baz")

        schema = MySchema()
        dump_data = schema.dump({"bar": {"baz": 42}})
        assert dump_data == {"foo": 42}

        load_data = schema.load({"foo": 42})
        assert load_data == {"bar": {"baz": 42}}

    def test_deserialize_with_attribute_param_error_returns_field_name_not_attribute_name(
        self
    ):
        class AliasingUserSerializer(Schema):
            username = fields.Email(attribute="email")
            years = fields.Integer(attribute="age")

        data = {"username": "foobar.com", "years": "42"}
        with pytest.raises(ValidationError) as excinfo:
            AliasingUserSerializer().load(data)
        errors = excinfo.value.messages
        assert errors["username"] == ["Not a valid email address."]

    def test_deserialize_with_attribute_param_error_returns_data_key_not_attribute_name(
        self
    ):
        class AliasingUserSerializer(Schema):
            name = fields.String(data_key="Name")
            username = fields.Email(attribute="email", data_key="UserName")
            years = fields.Integer(attribute="age", data_key="Years")

        data = {"Name": "Mick", "UserName": "foobar.com", "Years": "abc"}
        with pytest.raises(ValidationError) as excinfo:
            AliasingUserSerializer().load(data)
        errors = excinfo.value.messages
        assert errors["UserName"] == ["Not a valid email address."]
        assert errors["Years"] == ["Not a valid integer."]

    def test_deserialize_with_data_key_param(self):
        class AliasingUserSerializer(Schema):
            name = fields.String(data_key="Name")
            username = fields.Email(attribute="email", data_key="UserName")
            years = fields.Integer(data_key="Years")

        data = {"Name": "Mick", "UserName": "foo@bar.com", "years": "42"}
        result = AliasingUserSerializer(unknown=EXCLUDE).load(data)
        assert result["name"] == "Mick"
        assert result["email"] == "foo@bar.com"
        assert "years" not in result

    def test_deserialize_with_dump_only_param(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(dump_only=True)
            nicknames = fields.List(fields.Str(), dump_only=True)

        data = {"name": "Mick", "years": "42", "nicknames": ["Your Majesty", "Brenda"]}
        result = AliasingUserSerializer(unknown=EXCLUDE).load(data)
        assert result["name"] == "Mick"
        assert "years" not in result
        assert "nicknames" not in result

    def test_deserialize_with_missing_param_value(self):
        bdate = dt.datetime(2017, 9, 29)

        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(missing=bdate)

        data = {"name": "Mick"}
        result = AliasingUserSerializer().load(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == bdate

    def test_deserialize_with_missing_param_callable(self):
        bdate = dt.datetime(2017, 9, 29)

        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(missing=lambda: bdate)

        data = {"name": "Mick"}
        result = AliasingUserSerializer().load(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == bdate

    def test_deserialize_with_missing_param_none(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(missing=None, allow_none=True)

        data = {"name": "Mick"}
        result = AliasingUserSerializer().load(data)
        assert result["name"] == "Mick"
        assert result["years"] is None

    def test_deserialization_raises_with_errors(self):
        bad_data = {"email": "invalid-email", "colors": "burger", "age": -1}
        v = Validator()
        with pytest.raises(ValidationError) as excinfo:
            v.load(bad_data)
        errors = excinfo.value.messages
        assert "email" in errors
        assert "colors" in errors
        assert "age" in errors

    def test_deserialization_raises_with_errors_with_multiple_validators(self):
        bad_data = {"email": "invalid-email", "colors": "burger", "age": -1}
        v = Validators()
        with pytest.raises(ValidationError) as excinfo:
            v.load(bad_data)
        errors = excinfo.value.messages
        assert "email" in errors
        assert "colors" in errors
        assert "age" in errors

    def test_deserialization_many_raises_errors(self):
        bad_data = [
            {"email": "foo@bar.com", "colors": "red", "age": 18},
            {"email": "bad", "colors": "pizza", "age": -1},
        ]
        v = Validator(many=True)
        with pytest.raises(ValidationError):
            v.load(bad_data)

    def test_validation_errors_are_stored(self):
        def validate_field(val):
            raise ValidationError("Something went wrong")

        class MySchema(Schema):
            foo = fields.Field(validate=validate_field)

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"foo": 42})
        errors = excinfo.value.messages
        assert "Something went wrong" in errors["foo"]

    def test_multiple_errors_can_be_stored_for_a_field(self):
        def validate_with_bool(n):
            return False

        def validate_with_error(n):
            raise ValidationError("foo is not valid")

        class MySchema(Schema):
            foo = fields.Field(
                required=True, validate=[validate_with_bool, validate_with_error]
            )

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"foo": "bar"})
        errors = excinfo.value.messages

        assert type(errors["foo"]) == list
        assert len(errors["foo"]) == 2

    def test_multiple_errors_can_be_stored_for_an_email_field(self):
        def validate_with_bool(val):
            return False

        class MySchema(Schema):
            email = fields.Email(validate=[validate_with_bool])

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"email": "foo"})
        errors = excinfo.value.messages
        assert len(errors["email"]) == 2
        assert "Not a valid email address." in errors["email"][0]

    def test_multiple_errors_can_be_stored_for_a_url_field(self):
        def validate_with_bool(val):
            return False

        class MySchema(Schema):
            url = fields.Url(validate=[validate_with_bool])

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"url": "foo"})
        errors = excinfo.value.messages
        assert len(errors["url"]) == 2
        assert "Not a valid URL." in errors["url"][0]

    def test_required_value_only_passed_to_validators_if_provided(self):
        class MySchema(Schema):
            foo = fields.Field(required=True, validate=lambda f: False)

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({})
        errors = excinfo.value.messages
        # required value missing
        assert len(errors["foo"]) == 1
        assert "Missing data for required field." in errors["foo"]

    @pytest.mark.parametrize("partial_schema", [True, False])
    def test_partial_deserialization(self, partial_schema):
        class MySchema(Schema):
            foo = fields.Field(required=True)
            bar = fields.Field(required=True)

        schema_args = {}
        load_args = {}
        if partial_schema:
            schema_args["partial"] = True
        else:
            load_args["partial"] = True
        data = MySchema(**schema_args).load({"foo": 3}, **load_args)

        assert data["foo"] == 3
        assert "bar" not in data

    def test_partial_fields_deserialization(self):
        class MySchema(Schema):
            foo = fields.Field(required=True)
            bar = fields.Field(required=True)
            baz = fields.Field(required=True)

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"foo": 3}, partial=tuple())
        data, errors = excinfo.value.valid_data, excinfo.value.messages
        assert data["foo"] == 3
        assert "bar" in errors
        assert "baz" in errors

        data = MySchema().load({"foo": 3}, partial=("bar", "baz"))
        assert data["foo"] == 3
        assert "bar" not in data
        assert "baz" not in data

        data = MySchema(partial=True).load({"foo": 3}, partial=("bar", "baz"))
        assert data["foo"] == 3
        assert "bar" not in data
        assert "baz" not in data

    def test_partial_fields_validation(self):
        class MySchema(Schema):
            foo = fields.Field(required=True)
            bar = fields.Field(required=True)
            baz = fields.Field(required=True)

        errors = MySchema().validate({"foo": 3}, partial=tuple())
        assert "bar" in errors
        assert "baz" in errors

        errors = MySchema().validate({"foo": 3}, partial=("bar", "baz"))
        assert errors == {}

        errors = MySchema(partial=True).validate({"foo": 3}, partial=("bar", "baz"))
        assert errors == {}

    def test_unknown_fields_deserialization(self):
        class MySchema(Schema):
            foo = fields.Integer()

        data = MySchema(unknown=EXCLUDE).load({"foo": 3, "bar": 5})
        assert data["foo"] == 3
        assert "bar" not in data

        data = MySchema(unknown=INCLUDE).load({"foo": 3, "bar": 5}, unknown=EXCLUDE)
        assert data["foo"] == 3
        assert "bar" not in data

        data = MySchema(unknown=EXCLUDE).load({"foo": 3, "bar": 5}, unknown=INCLUDE)
        assert data["foo"] == 3
        assert data["bar"]

        data = MySchema(unknown=INCLUDE).load({"foo": 3, "bar": 5})
        assert data["foo"] == 3
        assert data["bar"]

        with pytest.raises(ValidationError, match="foo"):
            MySchema(unknown=INCLUDE).load({"foo": "asd", "bar": 5})

        data = MySchema(unknown=INCLUDE, many=True).load(
            [{"foo": 1}, {"foo": 3, "bar": 5}]
        )
        assert "foo" in data[1]
        assert "bar" in data[1]

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"foo": 3, "bar": 5})
        err = excinfo.value
        assert "bar" in err.messages
        assert err.messages["bar"] == ["Unknown field."]

        with pytest.raises(ValidationError) as excinfo:
            MySchema(many=True).load([{"foo": "abc"}, {"foo": 3, "bar": 5}])
        err = excinfo.value
        assert 0 in err.messages
        assert "foo" in err.messages[0]
        assert err.messages[0]["foo"] == ["Not a valid integer."]
        assert 1 in err.messages
        assert "bar" in err.messages[1]
        assert err.messages[1]["bar"] == ["Unknown field."]

    def test_unknown_fields_deserialization_precedence(self):
        class MySchema(Schema):
            class Meta:
                unknown = INCLUDE

            foo = fields.Integer()

        data = MySchema().load({"foo": 3, "bar": 5})
        assert data["foo"] == 3
        assert data["bar"] == 5

        data = MySchema(unknown=EXCLUDE).load({"foo": 3, "bar": 5})
        assert data["foo"] == 3
        assert "bar" not in data

        data = MySchema().load({"foo": 3, "bar": 5}, unknown=EXCLUDE)
        assert data["foo"] == 3
        assert "bar" not in data

        with pytest.raises(ValidationError):
            MySchema(unknown=EXCLUDE).load({"foo": 3, "bar": 5}, unknown=RAISE)

    def test_unknown_fields_deserialization_with_data_key(self):
        class MySchema(Schema):
            foo = fields.Integer(data_key="Foo")

        data = MySchema().load({"Foo": 1})
        assert data["foo"] == 1
        assert "Foo" not in data

        data = MySchema(unknown=RAISE).load({"Foo": 1})
        assert data["foo"] == 1
        assert "Foo" not in data

        with pytest.raises(ValidationError):
            MySchema(unknown=RAISE).load({"foo": 1})

        data = MySchema(unknown=INCLUDE).load({"Foo": 1})
        assert data["foo"] == 1
        assert "Foo" not in data

    def test_unknown_fields_deserialization_with_index_errors_false(self):
        class MySchema(Schema):
            foo = fields.Integer()

            class Meta:
                unknown = RAISE
                index_errors = False

        with pytest.raises(ValidationError) as excinfo:
            MySchema(many=True).load([{"foo": "invalid"}, {"foo": 42, "bar": 24}])
        err = excinfo.value
        assert 1 not in err.messages
        assert "foo" in err.messages
        assert "bar" in err.messages
        assert err.messages["foo"] == ["Not a valid integer."]
        assert err.messages["bar"] == ["Unknown field."]

    def test_dump_only_fields_considered_unknown(self):
        class MySchema(Schema):
            foo = fields.Int(dump_only=True)

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"foo": 42})
        err = excinfo.value
        assert "foo" in err.messages
        assert err.messages["foo"] == ["Unknown field."]

        # When unknown = INCLUDE, dump-only fields are included as unknown
        # without any validation.
        data = MySchema(unknown=INCLUDE).load({"foo": "LOL"})
        assert data["foo"] == "LOL"


validators_gen = (func for func in [lambda x: x <= 24, lambda x: 18 <= x])

validators_gen_float = (func for func in [lambda f: f <= 4.1, lambda f: f >= 1.0])

validators_gen_str = (
    func for func in [lambda n: len(n) == 3, lambda n: n[1].lower() == "o"]
)


class TestValidation:
    def test_integer_with_validator(self):
        field = fields.Integer(validate=lambda x: 18 <= x <= 24)
        out = field.deserialize("20")
        assert out == 20
        with pytest.raises(ValidationError):
            field.deserialize(25)

    @pytest.mark.parametrize(
        "field",
        [
            fields.Integer(validate=[lambda x: x <= 24, lambda x: 18 <= x]),
            fields.Integer(validate=(lambda x: x <= 24, lambda x: 18 <= x)),
            fields.Integer(validate=validators_gen),
        ],
    )
    def test_integer_with_validators(self, field):
        out = field.deserialize("20")
        assert out == 20
        with pytest.raises(ValidationError):
            field.deserialize(25)

    @pytest.mark.parametrize(
        "field",
        [
            fields.Float(validate=[lambda f: f <= 4.1, lambda f: f >= 1.0]),
            fields.Float(validate=(lambda f: f <= 4.1, lambda f: f >= 1.0)),
            fields.Float(validate=validators_gen_float),
        ],
    )
    def test_float_with_validators(self, field):
        assert field.deserialize(3.14)
        with pytest.raises(ValidationError):
            field.deserialize(4.2)

    def test_string_validator(self):
        field = fields.String(validate=lambda n: len(n) == 3)
        assert field.deserialize("Joe") == "Joe"
        with pytest.raises(ValidationError):
            field.deserialize("joseph")

    def test_function_validator(self):
        field = fields.Function(
            lambda d: d.name.upper(), validate=lambda n: len(n) == 3
        )
        assert field.deserialize("joe")
        with pytest.raises(ValidationError):
            field.deserialize("joseph")

    @pytest.mark.parametrize(
        "field",
        [
            fields.Function(
                lambda d: d.name.upper(),
                validate=[lambda n: len(n) == 3, lambda n: n[1].lower() == "o"],
            ),
            fields.Function(
                lambda d: d.name.upper(),
                validate=(lambda n: len(n) == 3, lambda n: n[1].lower() == "o"),
            ),
            fields.Function(lambda d: d.name.upper(), validate=validators_gen_str),
        ],
    )
    def test_function_validators(self, field):
        assert field.deserialize("joe")
        with pytest.raises(ValidationError):
            field.deserialize("joseph")

    def test_method_validator(self):
        class MethodSerializer(Schema):
            name = fields.Method(
                "get_name", deserialize="get_name", validate=lambda n: len(n) == 3
            )

            def get_name(self, val):
                return val.upper()

        assert MethodSerializer().load({"name": "joe"})
        with pytest.raises(ValidationError, match="Invalid value."):
            MethodSerializer().load({"name": "joseph"})

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

        with pytest.raises(ValidationError) as excinfo:
            sch.load({"w": 90, "n": {"x": 90, "y": 89, "z": None}})
        data, errors = excinfo.value.valid_data, excinfo.value.messages
        assert "z" in errors["n"]
        assert data == {"w": 90, "n": {"x": 90, "y": 89}}

        with pytest.raises(ValidationError) as excinfo:
            sch.load({"w": 90, "n": {"x": 90, "y": -1, "z": 180}})
        data, errors = excinfo.value.valid_data, excinfo.value.messages
        assert "y" in errors["n"]
        assert data == {"w": 90, "n": {"x": 90, "z": 180}}

    def test_false_value_validation(self):
        class Sch(Schema):
            lamb = fields.Raw(validate=lambda x: x is False)
            equal = fields.Raw(validate=Equal(False))

        errors = Sch().validate({"lamb": False, "equal": False})
        assert not errors
        errors = Sch().validate({"lamb": True, "equal": True})
        assert "lamb" in errors
        assert errors["lamb"] == ["Invalid value."]
        assert "equal" in errors
        assert errors["equal"] == ["Must be equal to False."]

    def test_nested_partial_load(self):
        class SchemaA(Schema):
            x = fields.Integer(required=True)
            y = fields.Integer()

        class SchemaB(Schema):
            z = fields.Nested(SchemaA)

        b_dict = {"z": {"y": 42}}
        # Partial loading shouldn't generate any errors.
        result = SchemaB().load(b_dict, partial=True)
        assert result["z"]["y"] == 42
        # Non partial loading should complain about missing values.
        with pytest.raises(ValidationError) as excinfo:
            SchemaB().load(b_dict)
        data, errors = excinfo.value.valid_data, excinfo.value.messages
        assert data["z"]["y"] == 42
        assert "z" in errors
        assert "x" in errors["z"]

    def test_deeply_nested_partial_load(self):
        class SchemaC(Schema):
            x = fields.Integer(required=True)
            y = fields.Integer()

        class SchemaB(Schema):
            c = fields.Nested(SchemaC)

        class SchemaA(Schema):
            b = fields.Nested(SchemaB)

        a_dict = {"b": {"c": {"y": 42}}}
        # Partial loading shouldn't generate any errors.
        result = SchemaA().load(a_dict, partial=True)
        assert result["b"]["c"]["y"] == 42
        # Non partial loading should complain about missing values.
        with pytest.raises(ValidationError) as excinfo:
            SchemaA().load(a_dict)
        data, errors = excinfo.value.valid_data, excinfo.value.messages
        assert data["b"]["c"]["y"] == 42
        assert "b" in errors
        assert "c" in errors["b"]
        assert "x" in errors["b"]["c"]

    def test_nested_partial_tuple(self):
        class SchemaA(Schema):
            x = fields.Integer(required=True)
            y = fields.Integer(required=True)

        class SchemaB(Schema):
            z = fields.Nested(SchemaA)

        b_dict = {"z": {"y": 42}}
        # If we ignore the missing z.x, z.y should still load.
        result = SchemaB().load(b_dict, partial=("z.x",))
        assert result["z"]["y"] == 42
        # If we ignore a missing z.y we should get a validation error.
        with pytest.raises(ValidationError):
            SchemaB().load(b_dict, partial=("z.y",))


@pytest.mark.parametrize("FieldClass", ALL_FIELDS)
def test_required_field_failure(FieldClass):  # noqa
    class RequireSchema(Schema):
        age = FieldClass(required=True)

    user_data = {"name": "Phil"}
    with pytest.raises(ValidationError) as excinfo:
        RequireSchema().load(user_data)
    errors = excinfo.value.messages
    assert "Missing data for required field." in errors["age"]


@pytest.mark.parametrize(
    "message",
    [
        "My custom required message",
        {"error": "something", "code": 400},
        ["first error", "second error"],
    ],
)
def test_required_message_can_be_changed(message):
    class RequireSchema(Schema):
        age = fields.Integer(required=True, error_messages={"required": message})

    user_data = {"name": "Phil"}
    with pytest.raises(ValidationError) as excinfo:
        RequireSchema().load(user_data)
    errors = excinfo.value.messages
    expected = [message] if isinstance(message, str) else message
    assert expected == errors["age"]


@pytest.mark.parametrize("unknown", (EXCLUDE, INCLUDE, RAISE))
@pytest.mark.parametrize("data", [True, False, 42, None, []])
def test_deserialize_raises_exception_if_input_type_is_incorrect(data, unknown):
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.Field()

    with pytest.raises(ValidationError, match="Invalid input type.") as excinfo:
        MySchema(unknown=unknown).load(data)
    exc = excinfo.value
    assert list(exc.messages.keys()) == ["_schema"]
