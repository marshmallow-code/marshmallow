"""Tests for field serialization."""
from collections import namedtuple, OrderedDict
import datetime as dt
import itertools
import decimal
import uuid
import math

import pytest

from marshmallow import Schema, fields, utils, missing as missing_
from marshmallow.exceptions import ValidationError

from tests.base import User, ALL_FIELDS


class DateTimeList:
    def __init__(self, dtimes):
        self.dtimes = dtimes


class IntegerList:
    def __init__(self, ints):
        self.ints = ints


class DateTimeIntegerTuple:
    def __init__(self, dtime_int):
        self.dtime_int = dtime_int


class TestFieldSerialization:
    @pytest.fixture
    def user(self):
        return User("Foo", email="foo@bar.com", age=42)

    @pytest.mark.parametrize(
        ("value", "expected"), [(42, float(42)), (0, float(0)), (None, None)]
    )
    def test_number(self, value, expected, user):
        field = fields.Number()
        user.age = value
        assert field.serialize("age", user) == expected

    def test_number_as_string(self, user):
        user.age = 42
        field = fields.Number(as_string=True)
        assert field.serialize("age", user) == str(float(user.age))

    def test_number_as_string_passed_none(self, user):
        user.age = None
        field = fields.Number(as_string=True, allow_none=True)
        assert field.serialize("age", user) is None

    def test_function_field_passed_func(self, user):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", user)

    def test_function_field_passed_serialize_only_is_dump_only(self, user):
        field = fields.Function(serialize=lambda obj: obj.name.upper())
        assert field.dump_only is True

    def test_function_field_passed_deserialize_and_serialize_is_not_dump_only(self):
        field = fields.Function(
            serialize=lambda val: val.lower(), deserialize=lambda val: val.upper()
        )
        assert field.dump_only is False

    def test_function_field_passed_serialize(self, user):
        field = fields.Function(serialize=lambda obj: obj.name.upper())
        assert "FOO" == field.serialize("key", user)

    # https://github.com/marshmallow-code/marshmallow/issues/395
    def test_function_field_does_not_swallow_attribute_error(self, user):
        def raise_error(obj):
            raise AttributeError()

        field = fields.Function(serialize=raise_error)
        with pytest.raises(AttributeError):
            field.serialize("key", user)

    def test_function_field_load_only(self):
        field = fields.Function(deserialize=lambda obj: None)
        assert field.load_only

    def test_function_field_passed_serialize_with_context(self, user, monkeypatch):
        class Parent(Schema):
            pass

        field = fields.Function(
            serialize=lambda obj, context: obj.name.upper() + context["key"]
        )
        field.parent = Parent(context={"key": "BAR"})
        assert "FOOBAR" == field.serialize("key", user)

    def test_function_field_passed_uncallable_object(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_integer_field(self, user):
        field = fields.Integer()
        assert field.serialize("age", user) == 42

    def test_integer_as_string_field(self, user):
        field = fields.Integer(as_string=True)
        assert field.serialize("age", user) == "42"

    def test_integer_field_default(self, user):
        user.age = None
        field = fields.Integer(default=0)
        assert field.serialize("age", user) is None
        # missing
        assert field.serialize("age", {}) == 0

    def test_integer_field_default_set_to_none(self, user):
        user.age = None
        field = fields.Integer(default=None)
        assert field.serialize("age", user) is None

    def test_uuid_field(self, user):
        user.uuid1 = "{12345678-1234-5678-1234-567812345678}"
        user.uuid2 = uuid.UUID("12345678123456781234567812345678")
        user.uuid3 = None
        user.uuid4 = "this is not a UUID"
        user.uuid5 = 42
        user.uuid6 = {}

        field = fields.UUID()
        assert isinstance(field.serialize("uuid1", user), str)
        assert field.serialize("uuid1", user) == "12345678-1234-5678-1234-567812345678"
        assert isinstance(field.serialize("uuid2", user), str)
        assert field.serialize("uuid2", user) == "12345678-1234-5678-1234-567812345678"
        assert field.serialize("uuid3", user) is None
        with pytest.raises(ValidationError):
            field.serialize("uuid4", user)
        with pytest.raises(ValidationError):
            field.serialize("uuid5", user)
        with pytest.raises(ValidationError):
            field.serialize("uuid6", user)

    def test_decimal_field(self, user):
        user.m1 = 12
        user.m2 = "12.355"
        user.m3 = decimal.Decimal(1)
        user.m4 = None
        user.m5 = "abc"
        user.m6 = [1, 2]

        field = fields.Decimal()
        assert isinstance(field.serialize("m1", user), decimal.Decimal)
        assert field.serialize("m1", user) == decimal.Decimal(12)
        assert isinstance(field.serialize("m2", user), decimal.Decimal)
        assert field.serialize("m2", user) == decimal.Decimal("12.355")
        assert isinstance(field.serialize("m3", user), decimal.Decimal)
        assert field.serialize("m3", user) == decimal.Decimal(1)
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

        field = fields.Decimal(1)
        assert isinstance(field.serialize("m1", user), decimal.Decimal)
        assert field.serialize("m1", user) == decimal.Decimal(12)
        assert isinstance(field.serialize("m2", user), decimal.Decimal)
        assert field.serialize("m2", user) == decimal.Decimal("12.4")
        assert isinstance(field.serialize("m3", user), decimal.Decimal)
        assert field.serialize("m3", user) == decimal.Decimal(1)
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.serialize("m1", user), decimal.Decimal)
        assert field.serialize("m1", user) == decimal.Decimal(12)
        assert isinstance(field.serialize("m2", user), decimal.Decimal)
        assert field.serialize("m2", user) == decimal.Decimal("12.3")
        assert isinstance(field.serialize("m3", user), decimal.Decimal)
        assert field.serialize("m3", user) == decimal.Decimal(1)
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

    def test_decimal_field_string(self, user):
        user.m1 = 12
        user.m2 = "12.355"
        user.m3 = decimal.Decimal(1)
        user.m4 = None
        user.m5 = "abc"
        user.m6 = [1, 2]

        field = fields.Decimal(as_string=True)
        assert isinstance(field.serialize("m1", user), str)
        assert field.serialize("m1", user) == "12"
        assert isinstance(field.serialize("m2", user), str)
        assert field.serialize("m2", user) == "12.355"
        assert isinstance(field.serialize("m3", user), str)
        assert field.serialize("m3", user) == "1"
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

        field = fields.Decimal(1, as_string=True)
        assert isinstance(field.serialize("m1", user), str)
        assert field.serialize("m1", user) == "12.0"
        assert isinstance(field.serialize("m2", user), str)
        assert field.serialize("m2", user) == "12.4"
        assert isinstance(field.serialize("m3", user), str)
        assert field.serialize("m3", user) == "1.0"
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

        field = fields.Decimal(1, decimal.ROUND_DOWN, as_string=True)
        assert isinstance(field.serialize("m1", user), str)
        assert field.serialize("m1", user) == "12.0"
        assert isinstance(field.serialize("m2", user), str)
        assert field.serialize("m2", user) == "12.3"
        assert isinstance(field.serialize("m3", user), str)
        assert field.serialize("m3", user) == "1.0"
        assert field.serialize("m4", user) is None
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

    def test_decimal_field_special_values(self, user):
        user.m1 = "-NaN"
        user.m2 = "NaN"
        user.m3 = "-sNaN"
        user.m4 = "sNaN"
        user.m5 = "-Infinity"
        user.m6 = "Infinity"
        user.m7 = "-0"

        field = fields.Decimal(places=2, allow_nan=True)

        m1s = field.serialize("m1", user)
        assert isinstance(m1s, decimal.Decimal)
        assert m1s.is_qnan() and not m1s.is_signed()

        m2s = field.serialize("m2", user)
        assert isinstance(m2s, decimal.Decimal)
        assert m2s.is_qnan() and not m2s.is_signed()

        m3s = field.serialize("m3", user)
        assert isinstance(m3s, decimal.Decimal)
        assert m3s.is_qnan() and not m3s.is_signed()

        m4s = field.serialize("m4", user)
        assert isinstance(m4s, decimal.Decimal)
        assert m4s.is_qnan() and not m4s.is_signed()

        m5s = field.serialize("m5", user)
        assert isinstance(m5s, decimal.Decimal)
        assert m5s.is_infinite() and m5s.is_signed()

        m6s = field.serialize("m6", user)
        assert isinstance(m6s, decimal.Decimal)
        assert m6s.is_infinite() and not m6s.is_signed()

        m7s = field.serialize("m7", user)
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero() and m7s.is_signed()

        field = fields.Decimal(as_string=True, allow_nan=True)

        m2s = field.serialize("m2", user)
        assert isinstance(m2s, str)
        assert m2s == user.m2

        m5s = field.serialize("m5", user)
        assert isinstance(m5s, str)
        assert m5s == user.m5

        m6s = field.serialize("m6", user)
        assert isinstance(m6s, str)
        assert m6s == user.m6

    def test_decimal_field_special_values_not_permitted(self, user):
        user.m1 = "-NaN"
        user.m2 = "NaN"
        user.m3 = "-sNaN"
        user.m4 = "sNaN"
        user.m5 = "-Infinity"
        user.m6 = "Infinity"
        user.m7 = "-0"

        field = fields.Decimal(places=2)

        with pytest.raises(ValidationError):
            field.serialize("m1", user)
        with pytest.raises(ValidationError):
            field.serialize("m2", user)
        with pytest.raises(ValidationError):
            field.serialize("m3", user)
        with pytest.raises(ValidationError):
            field.serialize("m4", user)
        with pytest.raises(ValidationError):
            field.serialize("m5", user)
        with pytest.raises(ValidationError):
            field.serialize("m6", user)

        m7s = field.serialize("m7", user)
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero() and m7s.is_signed()

    @pytest.mark.parametrize("allow_nan", (None, False, True))
    @pytest.mark.parametrize("value", ("nan", "-nan", "inf", "-inf"))
    def test_float_field_allow_nan(self, value, allow_nan, user):

        user.key = value

        if allow_nan is None:
            # Test default case is False
            field = fields.Float()
        else:
            field = fields.Float(allow_nan=allow_nan)

        if allow_nan is True:
            res = field.serialize("key", user)
            assert isinstance(res, float)
            if value.endswith("nan"):
                assert math.isnan(res)
            else:
                assert res == float(value)
        else:
            with pytest.raises(ValidationError) as excinfo:
                field.serialize("key", user)
            assert str(excinfo.value.args[0]) == (
                "Special numeric values (nan or infinity) are not permitted."
            )

    def test_decimal_field_fixed_point_representation(self, user):
        """
        Test we get fixed-point string representation for a Decimal number that would normally
        output in engineering notation.
        """
        user.m1 = "0.00000000100000000"

        field = fields.Decimal()
        s = field.serialize("m1", user)
        assert isinstance(s, decimal.Decimal)
        assert s == decimal.Decimal("1.00000000E-9")

        field = fields.Decimal(as_string=True)
        s = field.serialize("m1", user)
        assert isinstance(s, str)
        assert s == user.m1

        field = fields.Decimal(as_string=True, places=2)
        s = field.serialize("m1", user)
        assert isinstance(s, str)
        assert s == "0.00"

    def test_boolean_field_serialization(self, user):
        field = fields.Boolean()

        user.truthy = "non-falsy-ish"
        user.falsy = "false"
        user.none = None

        assert field.serialize("truthy", user) is True
        assert field.serialize("falsy", user) is False
        assert field.serialize("none", user) is None

    def test_function_with_uncallable_param(self):
        with pytest.raises(ValueError):
            fields.Function("uncallable")

    def test_email_field_serialize_none(self, user):
        user.email = None
        field = fields.Email()
        assert field.serialize("email", user) is None

    def test_dict_field_serialize_none(self, user):
        user.various_data = None
        field = fields.Dict()
        assert field.serialize("various_data", user) is None

    def test_dict_field_invalid_dict_but_okay(self, user):
        user.various_data = "okaydict"
        field = fields.Dict()
        field.serialize("various_data", user)
        assert field.serialize("various_data", user) == "okaydict"

    def test_dict_field_serialize(self, user):
        user.various_data = {"foo": "bar"}
        field = fields.Dict()
        assert field.serialize("various_data", user) == {"foo": "bar"}

    def test_dict_field_serialize_ordereddict(self, user):
        user.various_data = OrderedDict([("foo", "bar"), ("bar", "baz")])
        field = fields.Dict()
        assert field.serialize("various_data", user) == OrderedDict(
            [("foo", "bar"), ("bar", "baz")]
        )

    def test_structured_dict_value_serialize(self, user):
        user.various_data = {"foo": decimal.Decimal("1")}
        field = fields.Dict(values=fields.Decimal)
        assert field.serialize("various_data", user) == {"foo": 1}

    def test_structured_dict_key_serialize(self, user):
        user.various_data = {1: "bar"}
        field = fields.Dict(keys=fields.Str)
        assert field.serialize("various_data", user) == {"1": "bar"}

    def test_structured_dict_key_value_serialize(self, user):
        user.various_data = {1: decimal.Decimal("1")}
        field = fields.Dict(keys=fields.Str, values=fields.Decimal)
        assert field.serialize("various_data", user) == {"1": 1}

    def test_structured_dict_validates(self, user):
        user.various_data = {"foo": "bar"}
        field = fields.Dict(values=fields.Decimal)
        with pytest.raises(ValidationError):
            field.serialize("various_data", user)

    def test_url_field_serialize_none(self, user):
        user.homepage = None
        field = fields.Url()
        assert field.serialize("homepage", user) is None

    def test_method_field_with_method_missing(self):
        class BadSerializer(Schema):
            bad_field = fields.Method("invalid")

        u = User("Foo")
        with pytest.raises(ValueError):
            BadSerializer().dump(u)

    def test_method_field_passed_serialize_only_is_dump_only(self, user):
        field = fields.Method(serialize="method")
        assert field.dump_only is True
        assert field.load_only is False

    def test_method_field_passed_deserialize_only_is_load_only(self):
        field = fields.Method(deserialize="somemethod")
        assert field.load_only is True
        assert field.dump_only is False

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Schema):
            foo = "not callable"
            bad_field = fields.Method("foo")

        u = User("Foo")
        with pytest.raises(ValueError):
            BadSerializer().dump(u)

    # https://github.com/marshmallow-code/marshmallow/issues/395
    def test_method_field_does_not_swallow_attribute_error(self):
        class MySchema(Schema):
            mfield = fields.Method("raise_error")

            def raise_error(self, obj):
                raise AttributeError()

        with pytest.raises(AttributeError):
            MySchema().dump({})

    def test_method_with_no_serialize_is_missing(self):
        m = fields.Method()
        m.parent = Schema()

        assert m.serialize("", "", "") is missing_

    def test_serialize_with_data_key_param(self):
        class DumpToSchema(Schema):
            name = fields.String(data_key="NamE")
            years = fields.Integer(data_key="YearS")

        data = {"name": "Richard", "years": 11}
        result = DumpToSchema().dump(data)
        assert result == {"NamE": "Richard", "YearS": 11}

    def test_serialize_with_attribute_and_data_key_uses_data_key(self):
        class ConfusedDumpToAndAttributeSerializer(Schema):
            name = fields.String(data_key="FullName")
            username = fields.String(attribute="uname", data_key="UserName")
            years = fields.Integer(attribute="le_wild_age", data_key="Years")

        data = {"name": "Mick", "uname": "mick_the_awesome", "le_wild_age": 999}
        result = ConfusedDumpToAndAttributeSerializer().dump(data)

        assert result == {
            "FullName": "Mick",
            "UserName": "mick_the_awesome",
            "Years": 999,
        }

    def test_datetime_serializes_to_iso_by_default(self, user):
        field = fields.DateTime()  # No format specified
        expected = utils.isoformat(user.created, localtime=False)
        assert field.serialize("created", user) == expected

    @pytest.mark.parametrize("value", ["invalid", [], 24])
    def test_datetime_invalid_serialization(self, value, user):
        field = fields.DateTime()
        user.created = value

        with pytest.raises(ValidationError) as excinfo:
            field.serialize("created", user)
        assert excinfo.value.args[
            0
        ] == '"{}" cannot be formatted as a datetime.'.format(value)

    @pytest.mark.parametrize("fmt", ["rfc", "rfc822"])
    def test_datetime_field_rfc822(self, fmt, user):
        field = fields.DateTime(format=fmt)
        expected = utils.rfcformat(user.created, localtime=False)
        assert field.serialize("created", user) == expected

    def test_localdatetime_rfc_field(self, user):
        field = fields.LocalDateTime(format="rfc")
        expected = utils.rfcformat(user.created, localtime=True)
        assert field.serialize("created", user) == expected

    @pytest.mark.parametrize("fmt", ["iso", "iso8601"])
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
        user = User(name=b"foo")
        assert field.serialize("name", user) == "foo"
        field = fields.String(allow_none=True)
        user.name = None
        assert field.serialize("name", user) is None

    def test_string_field_default_to_empty_string(self, user):
        field = fields.String(default="")
        assert field.serialize("notfound", {}) == ""

    def test_time_field(self, user):
        field = fields.Time()
        expected = user.time_registered.isoformat()[:15]
        assert field.serialize("time_registered", user) == expected

        user.time_registered = None
        assert field.serialize("time_registered", user) is None

    @pytest.mark.parametrize("in_data", ["badvalue", "", [], 42])
    def test_invalid_time_field_serialization(self, in_data, user):
        field = fields.Time()
        user.time_registered = in_data
        with pytest.raises(ValidationError) as excinfo:
            field.serialize("time_registered", user)
        msg = '"{}" cannot be formatted as a time.'.format(in_data)
        assert excinfo.value.args[0] == msg

    def test_date_field(self, user):
        field = fields.Date()
        assert field.serialize("birthdate", user) == user.birthdate.isoformat()

        user.birthdate = None
        assert field.serialize("birthdate", user) is None

    @pytest.mark.parametrize("in_data", ["badvalue", "", [], 42])
    def test_invalid_date_field_serialization(self, in_data, user):
        field = fields.Date()
        user.birthdate = in_data
        with pytest.raises(ValidationError) as excinfo:
            field.serialize("birthdate", user)
        msg = '"{}" cannot be formatted as a date.'.format(in_data)
        assert excinfo.value.args[0] == msg

    def test_timedelta_field(self, user):
        user.d1 = dt.timedelta(days=1, seconds=1, microseconds=1)
        user.d2 = dt.timedelta(days=0, seconds=86401, microseconds=1)
        user.d3 = dt.timedelta(days=0, seconds=0, microseconds=86401000001)
        user.d4 = dt.timedelta(days=0, seconds=0, microseconds=0)
        user.d5 = dt.timedelta(days=-1, seconds=0, microseconds=0)
        user.d6 = dt.timedelta(
            days=1,
            seconds=1,
            microseconds=1,
            milliseconds=1,
            minutes=1,
            hours=1,
            weeks=1,
        )

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d1", user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d1", user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d1", user) == 86401000001
        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        assert field.serialize("d1", user) == 24

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d2", user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d2", user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d2", user) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d3", user) == 1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d3", user) == 86401
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d3", user) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d4", user) == 0
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d4", user) == 0
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d4", user) == 0

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d5", user) == -1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d5", user) == -86400
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d5", user) == -86400000000

        field = fields.TimeDelta(fields.TimeDelta.WEEKS)
        assert field.serialize("d6", user) == 1
        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize("d6", user) == 7 + 1
        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        assert field.serialize("d6", user) == 7 * 24 + 24 + 1
        field = fields.TimeDelta(fields.TimeDelta.MINUTES)
        assert field.serialize("d6", user) == 7 * 24 * 60 + 24 * 60 + 60 + 1
        d6_seconds = (
            7 * 24 * 60 * 60
            + 24 * 60 * 60  # 1 week
            + 60 * 60  # 1 day
            + 60  # 1 hour
            + 1  # 1 minute
        )
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize("d6", user) == d6_seconds
        field = fields.TimeDelta(fields.TimeDelta.MILLISECONDS)
        assert field.serialize("d6", user) == d6_seconds * 1000 + 1
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize("d6", user) == d6_seconds * 10 ** 6 + 1000 + 1

        user.d7 = None
        assert field.serialize("d7", user) is None

    def test_datetime_list_field(self):
        obj = DateTimeList([dt.datetime.utcnow(), dt.datetime.now()])
        field = fields.List(fields.DateTime)
        result = field.serialize("dtimes", obj)
        assert all([type(each) == str for each in result])

    def test_list_field_with_error(self):
        obj = DateTimeList(["invaliddate"])
        field = fields.List(fields.DateTime)
        with pytest.raises(ValidationError):
            field.serialize("dtimes", obj)

    def test_datetime_list_serialize_single_value(self):
        obj = DateTimeList(dt.datetime.utcnow())
        field = fields.List(fields.DateTime)
        result = field.serialize("dtimes", obj)
        assert len(result) == 1
        assert type(result[0]) == str

    def test_list_field_serialize_none_returns_none(self):
        obj = DateTimeList(None)
        field = fields.List(fields.DateTime)
        assert field.serialize("dtimes", obj) is None

    def test_list_field_work_with_generator_single_value(self):
        def custom_generator():
            yield dt.datetime.utcnow()

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize("dtimes", obj)
        assert len(result) == 1

    def test_list_field_work_with_generators_multiple_values(self):
        def custom_generator():
            for dtime in [dt.datetime.utcnow(), dt.datetime.now()]:
                yield dtime

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize("dtimes", obj)
        assert len(result) == 2

    def test_list_field_work_with_generators_error(self):
        def custom_generator():
            for dtime in [dt.datetime.utcnow(), "m", dt.datetime.now()]:
                yield dtime

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        with pytest.raises(ValidationError):
            field.serialize("dtimes", obj)

    def test_list_field_work_with_generators_empty_generator_returns_none_for_every_non_returning_yield_statement(  # noqa: B950
        self
    ):
        def custom_generator():
            yield
            yield

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime, allow_none=True)
        result = field.serialize("dtimes", obj)
        assert len(result) == 2
        assert result[0] is None
        assert result[1] is None

    def test_list_field_work_with_set(self):
        custom_set = {1, 2, 3}
        obj = IntegerList(custom_set)
        field = fields.List(fields.Int)
        result = field.serialize("ints", obj)
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_list_field_work_with_custom_class_with_iterator_protocol(self):
        class IteratorSupportingClass:
            def __init__(self, iterable):
                self.iterable = iterable

            def __iter__(self):
                return iter(self.iterable)

        ints = IteratorSupportingClass([1, 2, 3])
        obj = IntegerList(ints)
        field = fields.List(fields.Int)
        result = field.serialize("ints", obj)
        assert len(result) == 3
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3

    def test_bad_list_field(self):
        class ASchema(Schema):
            id = fields.Int()

        with pytest.raises(ValueError):
            fields.List("string")
        expected_msg = (
            "The list elements must be a subclass or instance of "
            "marshmallow.base.FieldABC"
        )
        with pytest.raises(ValueError, match=expected_msg):
            fields.List(ASchema)

    def test_datetime_integer_tuple_field(self):
        obj = DateTimeIntegerTuple((dt.datetime.utcnow(), 42))
        field = fields.Tuple([fields.DateTime, fields.Integer])
        result = field.serialize("dtime_int", obj)
        assert type(result[0]) == str
        assert type(result[1]) == int

    @pytest.mark.parametrize(
        "obj",
        [
            DateTimeIntegerTuple(("invaliddate", 42)),
            DateTimeIntegerTuple((dt.datetime.utcnow(), "invalidint")),
            DateTimeIntegerTuple(("invaliddate", "invalidint")),
        ],
    )
    def test_tuple_field_with_error(self, obj):
        field = fields.Tuple([fields.DateTime, fields.Integer])
        with pytest.raises(ValidationError):
            field.serialize("dtime_int", obj)

    def test_tuple_field_serialize_none_returns_none(self):
        obj = DateTimeIntegerTuple(None)
        field = fields.Tuple([fields.DateTime, fields.Integer])
        assert field.serialize("dtime_int", obj) is None

    def test_bad_tuple_field(self):
        class ASchema(Schema):
            id = fields.Int()

        with pytest.raises(ValueError):
            fields.Tuple(["string"])
        with pytest.raises(ValueError):
            fields.Tuple(fields.String)
        expected_msg = (
            'Elements of "tuple_fields" must be subclasses or '
            "instances of marshmallow.base.FieldABC."
        )
        with pytest.raises(ValueError, match=expected_msg):
            fields.Tuple([ASchema])

    def test_serialize_does_not_apply_validators(self, user):
        field = fields.Field(validate=lambda x: False)
        # No validation error raised
        assert field.serialize("age", user) == user.age

    def test_constant_field_serialization(self, user):
        field = fields.Constant("something")
        assert field.serialize("whatever", user) == "something"

    def test_constant_is_always_included_in_serialized_data(self):
        class MySchema(Schema):
            foo = fields.Constant(42)

        sch = MySchema()
        assert sch.dump({"bar": 24})["foo"] == 42
        assert sch.dump({"foo": 24})["foo"] == 42

    def test_constant_field_serialize_when_omitted(self):
        class MiniUserSchema(Schema):
            name = fields.Constant("bill")

        s = MiniUserSchema()
        assert s.dump({})["name"] == "bill"

    @pytest.mark.parametrize("FieldClass", ALL_FIELDS)
    def test_all_fields_serialize_none_to_none(self, FieldClass):
        field = FieldClass(allow_none=True)
        res = field.serialize("foo", {"foo": None})
        assert res is None


class TestSchemaSerialization:
    def test_serialize_with_missing_param_value(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(default=dt.datetime(2017, 9, 29))

        data = {"name": "Mick"}
        result = AliasingUserSerializer().dump(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == "2017-09-29T00:00:00+00:00"

    def test_serialize_with_missing_param_callable(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(default=lambda: dt.datetime(2017, 9, 29))

        data = {"name": "Mick"}
        result = AliasingUserSerializer().dump(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == "2017-09-29T00:00:00+00:00"


def test_serializing_named_tuple():
    Point = namedtuple("Point", ["x", "y"])

    field = fields.Field()

    p = Point(x=4, y=2)

    assert field.serialize("x", p) == 4


def test_serializing_named_tuple_with_meta():
    Point = namedtuple("Point", ["x", "y"])
    p = Point(x=4, y=2)

    class PointSerializer(Schema):
        class Meta:
            fields = ("x", "y")

    serialized = PointSerializer().dump(p)
    assert serialized["x"] == 4
    assert serialized["y"] == 2


def test_serializing_slice():
    values = [{"value": value} for value in range(5)]
    slice = itertools.islice(values, None)

    class ValueSchema(Schema):
        value = fields.Int()

    serialized = ValueSchema(many=True).dump(slice)
    assert serialized == values


# https://github.com/marshmallow-code/marshmallow/issues/1163
def test_nested_field_many_serializing_generator():
    class MySchema(Schema):
        name = fields.Str()

    class OtherSchema(Schema):
        objects = fields.Nested(MySchema, many=True)

    def gen():
        yield {"name": "foo"}
        yield {"name": "bar"}

    obj = {"objects": gen()}
    data = OtherSchema().dump(obj)

    assert data.get("objects") == [{"name": "foo"}, {"name": "bar"}]
