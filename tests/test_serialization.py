"""Tests for field serialization."""

import datetime as dt
import decimal
import ipaddress
import itertools
import math
import uuid
from collections import OrderedDict
from typing import NamedTuple

import pytest

from marshmallow import Schema, fields
from marshmallow import missing as missing_
from tests.base import ALL_FIELDS, DateEnum, GenderEnum, HairColorEnum, central


class Point(NamedTuple):
    x: int
    y: int


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
    def test_function_field_passed_func(self):
        field = fields.Function(lambda value: value.upper())
        assert field.serialize("Foo") == "FOO"

    def test_function_field_passed_serialize_only_is_dump_only(self):
        field = fields.Function(serialize=lambda value: value.upper())
        assert field.dump_only is True

    def test_function_field_passed_deserialize_and_serialize_is_not_dump_only(self):
        field = fields.Function(
            serialize=lambda val: val.lower(), deserialize=lambda val: val.upper()
        )
        assert field.dump_only is False

    def test_function_field_passed_serialize(self):
        field = fields.Function(serialize=lambda value: value.upper())
        assert field.serialize("Foo") == "FOO"

    # https://github.com/marshmallow-code/marshmallow/issues/395
    def test_function_field_does_not_swallow_attribute_error(self):
        def raise_error(value):
            raise AttributeError

        field = fields.Function(serialize=raise_error)
        with pytest.raises(AttributeError):
            field.serialize("Foo")

    def test_serialize_with_load_only_param(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            years = fields.Integer(load_only=True)
            size = fields.Integer(dump_only=True, load_only=True)
            nicknames = fields.List(fields.Str(), load_only=True)

        data = {
            "name": "Mick",
            "years": "42",
            "size": "12",
            "nicknames": ["Your Majesty", "Brenda"],
        }
        result = AliasingUserSerializer().dump(data)
        assert result["name"] == "Mick"
        assert "years" not in result
        assert "size" not in result
        assert "nicknames" not in result

    def test_function_field_load_only(self):
        field = fields.Function(deserialize=lambda obj: None)
        assert field.load_only

    def test_function_field_passed_uncallable_object(self):
        with pytest.raises(TypeError):
            fields.Function("uncallable")  # type: ignore[arg-type]

    def test_integer_field(self):
        field = fields.Integer()
        assert field.serialize(42) == 42

    def test_integer_as_string_field(self):
        field = fields.Integer(as_string=True)
        assert field.serialize(42) == "42"

    def test_integer_field_default(self):
        field = fields.Integer(dump_default=0)
        assert field.serialize(None) is None
        # missing
        assert field.serialize(0) == 0

    def test_integer_field_default_set_to_none(self):
        field = fields.Integer(dump_default=None)
        assert field.serialize(None) is None

    def test_uuid_field(self):
        uuid1 = uuid.UUID("12345678123456781234567812345678")

        field = fields.UUID()
        assert isinstance(field.serialize(uuid1), str)
        assert field.serialize(uuid1) == "12345678-1234-5678-1234-567812345678"
        assert field.serialize(None) is None

    def test_ip_address_field(self):
        ipv4_string = "192.168.0.1"
        ipv6_string = "ffff::ffff"
        ipv6_exploded_string = ipaddress.ip_address("ffff::ffff").exploded

        ipv4 = ipaddress.ip_address(ipv4_string)
        ipv6 = ipaddress.ip_address(ipv6_string)

        field_compressed = fields.IP()
        assert isinstance(field_compressed.serialize(ipv4), str)
        assert field_compressed.serialize(ipv4) == ipv4_string
        assert isinstance(field_compressed.serialize(ipv6), str)
        assert field_compressed.serialize(ipv6) == ipv6_string
        assert field_compressed.serialize(None) is None

        field_exploded = fields.IP(exploded=True)
        assert isinstance(field_exploded.serialize(ipv6), str)
        assert field_exploded.serialize(ipv6) == ipv6_exploded_string

    def test_ipv4_address_field(self):
        ipv4_string = "192.168.0.1"

        ipv4 = ipaddress.ip_address(ipv4_string)

        field = fields.IPv4()
        assert isinstance(field.serialize(ipv4), str)
        assert field.serialize(ipv4) == ipv4_string
        assert field.serialize(None) is None

    def test_ipv6_address_field(self):
        ipv6_string = "ffff::ffff"
        ipv6_exploded_string = ipaddress.ip_address("ffff::ffff").exploded

        ipv6 = ipaddress.ip_address(ipv6_string)

        field_compressed = fields.IPv6()
        assert isinstance(field_compressed.serialize(ipv6), str)
        assert field_compressed.serialize(ipv6) == ipv6_string
        assert field_compressed.serialize(None) is None

        field_exploded = fields.IPv6(exploded=True)
        assert isinstance(field_exploded.serialize(ipv6), str)
        assert field_exploded.serialize(ipv6) == ipv6_exploded_string

    def test_ip_interface_field(self):
        ipv4interface_string = "192.168.0.1/24"
        ipv6interface_string = "ffff::ffff/128"
        ipv6interface_exploded_string = ipaddress.ip_interface(
            "ffff::ffff/128"
        ).exploded

        ipv4interface = ipaddress.ip_interface(ipv4interface_string)
        ipv6interface = ipaddress.ip_interface(ipv6interface_string)

        field_compressed = fields.IPInterface()
        assert isinstance(field_compressed.serialize(ipv4interface), str)
        assert field_compressed.serialize(ipv4interface) == ipv4interface_string
        assert isinstance(field_compressed.serialize(ipv6interface), str)
        assert field_compressed.serialize(ipv6interface) == ipv6interface_string
        assert field_compressed.serialize(None) is None

        field_exploded = fields.IPInterface(exploded=True)
        assert isinstance(field_exploded.serialize(ipv6interface), str)
        assert field_exploded.serialize(ipv6interface) == ipv6interface_exploded_string

    def test_ipv4_interface_field(self):
        ipv4interface_string = "192.168.0.1/24"

        ipv4interface = ipaddress.ip_interface(ipv4interface_string)

        field = fields.IPv4Interface()
        assert isinstance(field.serialize(ipv4interface), str)
        assert field.serialize(ipv4interface) == ipv4interface_string
        assert field.serialize(None) is None

    def test_ipv6_interface_field(self):
        ipv6interface_string = "ffff::ffff/128"
        ipv6interface_exploded_string = ipaddress.ip_interface(
            "ffff::ffff/128"
        ).exploded

        ipv6interface = ipaddress.ip_interface(ipv6interface_string)

        field_compressed = fields.IPv6Interface()
        assert isinstance(field_compressed.serialize(ipv6interface), str)
        assert field_compressed.serialize(ipv6interface) == ipv6interface_string
        assert field_compressed.serialize(None) is None

        field_exploded = fields.IPv6Interface(exploded=True)
        assert isinstance(field_exploded.serialize(ipv6interface), str)
        assert field_exploded.serialize(ipv6interface) == ipv6interface_exploded_string

    def test_enum_field_by_symbol_serialization(self):
        field = fields.Enum(GenderEnum)
        assert field.serialize(GenderEnum.male) == "male"

    def test_enum_field_by_value_true_serialization(self):
        field = fields.Enum(HairColorEnum, by_value=True)
        assert field.serialize(HairColorEnum.black) == "black hair"
        field2 = fields.Enum(GenderEnum, by_value=True)
        assert field2.serialize(GenderEnum.male) == 1

    def test_enum_field_by_value_field_serialization(self):
        field = fields.Enum(HairColorEnum, by_value=fields.String)
        assert field.serialize(HairColorEnum.black) == "black hair"
        field2 = fields.Enum(GenderEnum, by_value=fields.Integer)
        assert field2.serialize(GenderEnum.male) == 1
        field3 = fields.Enum(DateEnum, by_value=fields.Date(format="%d/%m/%Y"))
        assert field3.serialize(DateEnum.date_1) == "29/02/2004"

    def test_decimal_field(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = None

        field = fields.Decimal()
        assert isinstance(field.serialize(m1), decimal.Decimal)
        assert field.serialize(m1) == decimal.Decimal(12)
        assert isinstance(field.serialize(m2), decimal.Decimal)
        assert field.serialize(m2) == decimal.Decimal("12.355")
        assert isinstance(field.serialize(m3), decimal.Decimal)
        assert field.serialize(m3) == decimal.Decimal(1)
        assert field.serialize(m4) is None

        field = fields.Decimal(1)
        assert isinstance(field.serialize(m1), decimal.Decimal)
        assert field.serialize(m1) == decimal.Decimal(12)
        assert isinstance(field.serialize(m2), decimal.Decimal)
        assert field.serialize(m2) == decimal.Decimal("12.4")
        assert isinstance(field.serialize(m3), decimal.Decimal)
        assert field.serialize(m3) == decimal.Decimal(1)
        assert field.serialize(m4) is None

        field = fields.Decimal(1, decimal.ROUND_DOWN)
        assert isinstance(field.serialize(m1), decimal.Decimal)
        assert field.serialize(m1) == decimal.Decimal(12)
        assert isinstance(field.serialize(m2), decimal.Decimal)
        assert field.serialize(m2) == decimal.Decimal("12.3")
        assert isinstance(field.serialize(m3), decimal.Decimal)
        assert field.serialize(m3) == decimal.Decimal(1)
        assert field.serialize(m4) is None

    def test_decimal_field_string(self):
        m1 = 12
        m2 = "12.355"
        m3 = decimal.Decimal(1)
        m4 = None

        field = fields.Decimal(as_string=True)
        assert isinstance(field.serialize(m1), str)
        assert field.serialize(m1) == "12"
        assert isinstance(field.serialize(m2), str)
        assert field.serialize(m2) == "12.355"
        assert isinstance(field.serialize(m3), str)
        assert field.serialize(m3) == "1"
        assert field.serialize(m4) is None

        field = fields.Decimal(1, as_string=True)
        assert isinstance(field.serialize(m1), str)
        assert field.serialize(m1) == "12.0"
        assert isinstance(field.serialize(m2), str)
        assert field.serialize(m2) == "12.4"
        assert isinstance(field.serialize(m3), str)
        assert field.serialize(m3) == "1.0"
        assert field.serialize(m4) is None

        field = fields.Decimal(1, decimal.ROUND_DOWN, as_string=True)
        assert isinstance(field.serialize(m1), str)
        assert field.serialize(m1) == "12.0"
        assert isinstance(field.serialize(m2), str)
        assert field.serialize(m2) == "12.3"
        assert isinstance(field.serialize(m3), str)
        assert field.serialize(m3) == "1.0"
        assert field.serialize(m4) is None

    def test_decimal_field_special_values(self):
        m1 = "-NaN"
        m2 = "NaN"
        m3 = "-sNaN"
        m4 = "sNaN"
        m5 = "-Infinity"
        m6 = "Infinity"
        m7 = "-0"

        field = fields.Decimal(places=2, allow_nan=True)

        m1s = field.serialize(m1)
        assert isinstance(m1s, decimal.Decimal)
        assert m1s.is_qnan()
        assert not m1s.is_signed()

        m2s = field.serialize(m2)
        assert isinstance(m2s, decimal.Decimal)
        assert m2s.is_qnan()
        assert not m2s.is_signed()

        m3s = field.serialize(m3)
        assert isinstance(m3s, decimal.Decimal)
        assert m3s.is_qnan()
        assert not m3s.is_signed()

        m4s = field.serialize(m4)
        assert isinstance(m4s, decimal.Decimal)
        assert m4s.is_qnan()
        assert not m4s.is_signed()

        m5s = field.serialize(m5)
        assert isinstance(m5s, decimal.Decimal)
        assert m5s.is_infinite()
        assert m5s.is_signed()

        m6s = field.serialize(m6)
        assert isinstance(m6s, decimal.Decimal)
        assert m6s.is_infinite()
        assert not m6s.is_signed()

        m7s = field.serialize(m7)
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero()
        assert m7s.is_signed()

        field = fields.Decimal(as_string=True, allow_nan=True)

        m2s = field.serialize(m2)
        assert isinstance(m2s, str)
        assert m2s == m2

        m5s = field.serialize(m5)
        assert isinstance(m5s, str)
        assert m5s == m5

        m6s = field.serialize(m6)
        assert isinstance(m6s, str)
        assert m6s == m6

    def test_decimal_field_special_values_not_permitted(self):
        field = fields.Decimal(places=2)

        m7s = field.serialize("-0")
        assert isinstance(m7s, decimal.Decimal)
        assert m7s.is_zero()
        assert m7s.is_signed()

    def test_decimal_field_fixed_point_representation(self):
        """
        Test we get fixed-point string representation for a Decimal number that would normally
        output in engineering notation.
        """
        m1 = "0.00000000100000000"

        field = fields.Decimal()
        s = field.serialize(m1)
        assert isinstance(s, decimal.Decimal)
        assert s == decimal.Decimal("1.00000000E-9")

        field = fields.Decimal(as_string=True)
        s = field.serialize(m1)
        assert isinstance(s, str)
        assert s == m1

        field = fields.Decimal(as_string=True, places=2)
        s = field.serialize(m1)
        assert isinstance(s, str)
        assert s == "0.00"

    def test_email_field_serialize_none(self):
        field = fields.Email()
        assert field.serialize(None) is None

    def test_dict_field_serialize_none(self):
        field = fields.Dict()
        assert field.serialize(None) is None

    def test_dict_field_serialize(self):
        data = {"foo": "bar"}
        field = fields.Dict()
        dump = field.serialize(data)
        assert dump == {"foo": "bar"}
        # Check dump is a distinct object
        dump["foo"] = "baz"
        assert data["foo"] == "bar"

    def test_dict_field_serialize_ordereddict(self):
        field = fields.Dict()
        assert field.serialize(
            OrderedDict([("foo", "bar"), ("bar", "baz")])
        ) == OrderedDict([("foo", "bar"), ("bar", "baz")])

    def test_structured_dict_value_serialize(self):
        field = fields.Dict(values=fields.Decimal)
        assert field.serialize({"foo": decimal.Decimal(1)}) == {"foo": 1}

    def test_structured_dict_key_serialize(self):
        field = fields.Dict(keys=fields.Str)
        assert field.serialize({1: "bar"}) == {"1": "bar"}

    def test_structured_dict_key_value_serialize(self):
        field = fields.Dict(keys=fields.Str, values=fields.Decimal)
        assert field.serialize({1: decimal.Decimal(1)}) == {"1": 1}

    def test_url_field_serialize_none(self):
        field = fields.Url()
        assert field.serialize(None) is None

    def test_method_field_with_method_missing(self):
        class BadSerializer(Schema):
            bad_field = fields.Method("invalid")

        with pytest.raises(AttributeError):
            BadSerializer()

    def test_method_field_passed_serialize_only_is_dump_only(self):
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

        with pytest.raises(TypeError):
            BadSerializer()

    # https://github.com/marshmallow-code/marshmallow/issues/395
    def test_method_field_does_not_swallow_attribute_error(self):
        class MySchema(Schema):
            mfield = fields.Method("raise_error")

            def raise_error(self, value):
                raise AttributeError

        with pytest.raises(AttributeError):
            MySchema().dump({"mfield": "something"})

    def test_method_with_no_serialize_is_missing(self):
        m = fields.Method()
        m.parent = Schema()

        assert m.serialize(missing_) is missing_

    def test_serialize_with_data_key_param(self):
        class DumpToSchema(Schema):
            name = fields.String(data_key="NamE")
            years = fields.Integer(data_key="YearS")

        data = {"name": "Richard", "years": 11}
        result = DumpToSchema().dump(data)
        assert result == {"NamE": "Richard", "YearS": 11}

    def test_serialize_with_data_key_as_empty_string(self):
        class MySchema(Schema):
            name = fields.Raw(data_key="")

        schema = MySchema()
        assert schema.dump({"name": "Grace"}) == {"": "Grace"}

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

    @pytest.mark.parametrize("fmt", ["rfc", "rfc822"])
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (dt.datetime(2013, 11, 10, 1, 23, 45), "Sun, 10 Nov 2013 01:23:45 -0000"),
            (
                dt.datetime(2013, 11, 10, 1, 23, 45, tzinfo=dt.timezone.utc),
                "Sun, 10 Nov 2013 01:23:45 +0000",
            ),
            (
                dt.datetime(2013, 11, 10, 1, 23, 45, tzinfo=central),
                "Sun, 10 Nov 2013 01:23:45 -0600",
            ),
        ],
    )
    def test_datetime_field_rfc822(self, fmt, value, expected):
        field = fields.DateTime(format=fmt)
        assert field.serialize(value) == expected

    @pytest.mark.parametrize(
        ("fmt", "value", "expected"),
        [
            ("timestamp", dt.datetime(1970, 1, 1), 0),
            ("timestamp", dt.datetime(2013, 11, 10, 0, 23, 45), 1384043025),
            (
                "timestamp",
                dt.datetime(2013, 11, 10, 0, 23, 45, tzinfo=dt.timezone.utc),
                1384043025,
            ),
            (
                "timestamp",
                dt.datetime(2013, 11, 10, 0, 23, 45, tzinfo=central),
                1384064625,
            ),
            ("timestamp_ms", dt.datetime(2013, 11, 10, 0, 23, 45), 1384043025000),
            (
                "timestamp_ms",
                dt.datetime(2013, 11, 10, 0, 23, 45, tzinfo=dt.timezone.utc),
                1384043025000,
            ),
            (
                "timestamp_ms",
                dt.datetime(2013, 11, 10, 0, 23, 45, tzinfo=central),
                1384064625000,
            ),
        ],
    )
    def test_datetime_field_timestamp(self, fmt, value, expected):
        field = fields.DateTime(format=fmt)
        assert field.serialize(value) == expected

    @pytest.mark.parametrize("fmt", ["iso", "iso8601", None])
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (dt.datetime(2013, 11, 10, 1, 23, 45), "2013-11-10T01:23:45"),
            (
                dt.datetime(2013, 11, 10, 1, 23, 45, 123456, tzinfo=dt.timezone.utc),
                "2013-11-10T01:23:45.123456+00:00",
            ),
            (
                dt.datetime(2013, 11, 10, 1, 23, 45, tzinfo=dt.timezone.utc),
                "2013-11-10T01:23:45+00:00",
            ),
            (
                dt.datetime(2013, 11, 10, 1, 23, 45, tzinfo=central),
                "2013-11-10T01:23:45-06:00",
            ),
        ],
    )
    def test_datetime_field_iso8601(self, fmt, value, expected):
        if fmt is None:
            # Test default is ISO
            field = fields.DateTime()
        else:
            field = fields.DateTime(format=fmt)
        assert field.serialize(value) == expected

    def test_datetime_field_format(self):
        datetimeformat = "%Y-%m-%d"
        created = dt.datetime(2013, 11, 10, 14, 20, 58)
        field = fields.DateTime(format=datetimeformat)
        assert field.serialize(created) == created.strftime(datetimeformat)

    def test_string_field(self):
        field = fields.String()
        assert field.serialize(b"foo") == "foo"
        field = fields.String(allow_none=True)
        assert field.serialize(None) is None

    def test_string_field_default_to_empty_string(self):
        field = fields.String(dump_default="")
        assert field.serialize("") == ""

    def test_time_field(self):
        time_registered = dt.time(1, 23, 45, 6789)
        field = fields.Time()
        expected = time_registered.isoformat()[:15]
        assert field.serialize(time_registered) == expected

        assert field.serialize(None) is None

    @pytest.mark.parametrize("fmt", ["iso", "iso8601", None])
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (dt.time(1, 23, 45), "01:23:45"),
            (dt.time(1, 23, 45, 123000), "01:23:45.123000"),
            (dt.time(1, 23, 45, 123456), "01:23:45.123456"),
        ],
    )
    def test_time_field_iso8601(self, fmt, value, expected):
        if fmt is None:
            # Test default is ISO
            field = fields.Time()
        else:
            field = fields.Time(format=fmt)
        assert field.serialize(value) == expected

    def test_time_field_format(self):
        fmt = "%H:%M:%S"
        birthtime = dt.time(0, 1, 2, 3333)
        field = fields.Time(format=fmt)
        assert field.serialize(birthtime) == birthtime.strftime(fmt)

    def test_date_field(self):
        birthdate = dt.date(2013, 1, 23)
        field = fields.Date()
        assert field.serialize(birthdate) == birthdate.isoformat()

        assert field.serialize(None) is None

    def test_timedelta_field(self):
        d1 = dt.timedelta(days=1, seconds=1, microseconds=1)
        d2 = dt.timedelta(days=0, seconds=86401, microseconds=1)
        d3 = dt.timedelta(days=0, seconds=0, microseconds=86401000001)
        d4 = dt.timedelta(days=0, seconds=0, microseconds=0)
        d5 = dt.timedelta(days=-1, seconds=0, microseconds=0)
        d6 = dt.timedelta(
            days=1,
            seconds=1,
            microseconds=1,
            milliseconds=1,
            minutes=1,
            hours=1,
            weeks=1,
        )

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d1) == 1.0000115740856481
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d1) == 86401.000001
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d1) == 86401000001
        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        assert field.serialize(d1) == 24.000277778055555

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d2) == 1.0000115740856481
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d2) == 86401.000001
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d2) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d3) == 1.0000115740856481
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d3) == 86401.000001
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d3) == 86401000001

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d4) == 0
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d4) == 0
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d4) == 0

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d5) == -1
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d5) == -86400
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d5) == -86400000000

        field = fields.TimeDelta(fields.TimeDelta.WEEKS)
        assert field.serialize(d6) == 1.1489103852529763
        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        assert field.serialize(d6) == 8.042372696770833
        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        assert field.serialize(d6) == 193.0169447225
        field = fields.TimeDelta(fields.TimeDelta.MINUTES)
        assert field.serialize(d6) == 11581.01668335
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d6) == 694861.001001
        field = fields.TimeDelta(fields.TimeDelta.MILLISECONDS)
        assert field.serialize(d6) == 694861001.001
        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        assert field.serialize(d6) == 694861001001

        assert field.serialize(None) is None

        d8 = dt.timedelta(milliseconds=345)
        field = fields.TimeDelta(fields.TimeDelta.MILLISECONDS)
        assert field.serialize(d8) == 345

        d9 = dt.timedelta(milliseconds=1999)
        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert field.serialize(d9) == 1.999

        d10 = dt.timedelta(
            weeks=1,
            days=6,
            hours=2,
            minutes=5,
            seconds=51,
            milliseconds=10,
            microseconds=742,
        )

        field = fields.TimeDelta(fields.TimeDelta.MICROSECONDS)
        unit_value = dt.timedelta(microseconds=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

        field = fields.TimeDelta(fields.TimeDelta.MILLISECONDS)
        unit_value = dt.timedelta(milliseconds=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

        field = fields.TimeDelta(fields.TimeDelta.SECONDS)
        assert math.isclose(field.serialize(d10), d10.total_seconds())

        field = fields.TimeDelta(fields.TimeDelta.MINUTES)
        unit_value = dt.timedelta(minutes=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

        field = fields.TimeDelta(fields.TimeDelta.HOURS)
        unit_value = dt.timedelta(hours=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

        field = fields.TimeDelta(fields.TimeDelta.DAYS)
        unit_value = dt.timedelta(days=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

        field = fields.TimeDelta(fields.TimeDelta.WEEKS)
        unit_value = dt.timedelta(weeks=1).total_seconds()
        assert math.isclose(
            field.serialize(d10),
            d10.total_seconds() / unit_value,
        )

    def test_datetime_list_field(self):
        obj = DateTimeList([dt.datetime.now(dt.timezone.utc), dt.datetime.now()])
        field = fields.List(fields.DateTime)
        result = field.serialize(obj.dtimes)
        assert all(type(each) is str for each in result)

    def test_list_field_serialize_none_returns_none(self):
        obj = DateTimeList(None)
        field = fields.List(fields.DateTime)
        assert field.serialize(obj.dtimes) is None

    def test_list_field_work_with_generator_single_value(self):
        def custom_generator():
            yield dt.datetime.now(dt.timezone.utc)

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize(obj.dtimes)
        assert len(result) == 1

    def test_list_field_work_with_generators_multiple_values(self):
        def custom_generator():
            yield from [dt.datetime.now(dt.timezone.utc), dt.datetime.now()]

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime)
        result = field.serialize(obj.dtimes)
        assert len(result) == 2

    def test_list_field_work_with_generators_empty_generator_returns_none_for_every_non_returning_yield_statement(
        self,
    ):
        def custom_generator():
            yield
            yield

        obj = DateTimeList(custom_generator())
        field = fields.List(fields.DateTime, allow_none=True)
        result = field.serialize(obj.dtimes)
        assert len(result) == 2
        assert result[0] is None
        assert result[1] is None

    def test_list_field_work_with_set(self):
        custom_set = {1, 2, 3}
        obj = IntegerList(custom_set)
        field = fields.List(fields.Int)
        result = field.serialize(obj.ints)
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
        result = field.serialize(obj.ints)
        assert len(result) == 3
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3

    def test_bad_list_field(self):
        class ASchema(Schema):
            id = fields.Int()

        with pytest.raises(ValueError):
            fields.List("string")  # type: ignore[arg-type]
        expected_msg = (
            "The list elements must be a subclass or instance of "
            "marshmallow.fields.Field"
        )
        with pytest.raises(ValueError, match=expected_msg):
            fields.List(ASchema)  # type: ignore[arg-type]

    def test_datetime_integer_tuple_field(self):
        obj = DateTimeIntegerTuple((dt.datetime.now(dt.timezone.utc), 42))
        field = fields.Tuple([fields.DateTime, fields.Integer])
        result = field.serialize(obj.dtime_int)
        assert type(result[0]) is str
        assert type(result[1]) is int

    def test_tuple_field_serialize_none_returns_none(self):
        obj = DateTimeIntegerTuple(None)
        field = fields.Tuple([fields.DateTime, fields.Integer])
        assert field.serialize(obj.dtime_int) is None

    def test_bad_tuple_field(self):
        class ASchema(Schema):
            id = fields.Int()

        with pytest.raises(ValueError):
            fields.Tuple(["string"])  # type: ignore[list-item]
        with pytest.raises(ValueError):
            fields.Tuple(fields.String)  # type: ignore[arg-type]
        expected_msg = (
            'Elements of "tuple_fields" must be subclasses or '
            "instances of marshmallow.fields.Field."
        )
        with pytest.raises(ValueError, match=expected_msg):
            fields.Tuple([ASchema])  # type: ignore[list-item]

    def test_serialize_does_not_apply_validators(self):
        field = fields.Raw(validate=lambda x: False)
        # No validation error raised
        assert field.serialize(42) == 42

    def test_constant_field_serialization(self):
        field = fields.Constant("something")
        assert field.serialize("whatever") == "something"

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
        res = field.serialize(None)
        assert res is None


class TestSchemaSerialization:
    def test_serialize_with_missing_param_value(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(dump_default=dt.datetime(2017, 9, 29))

        data = {"name": "Mick"}
        result = AliasingUserSerializer().dump(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == "2017-09-29T00:00:00"

    def test_serialize_with_missing_param_callable(self):
        class AliasingUserSerializer(Schema):
            name = fields.String()
            birthdate = fields.DateTime(dump_default=lambda: dt.datetime(2017, 9, 29))

        data = {"name": "Mick"}
        result = AliasingUserSerializer().dump(data)
        assert result["name"] == "Mick"
        assert result["birthdate"] == "2017-09-29T00:00:00"


def test_serializing_named_tuple():
    field = fields.Raw()

    p = Point(x=4, y=2)

    assert field.serialize(p.x) == 4


def test_serializing_named_tuple_with_meta():
    p = Point(x=4, y=2)

    class PointSerializer(Schema):
        x = fields.Int()
        y = fields.Int()

    serialized = PointSerializer().dump(p)
    assert serialized["x"] == 4
    assert serialized["y"] == 2


def test_serializing_slice():
    values = [{"value": value} for value in range(5)]
    sliced = itertools.islice(values, None)

    class ValueSchema(Schema):
        value = fields.Int()

    serialized = ValueSchema(many=True).dump(sliced)
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
