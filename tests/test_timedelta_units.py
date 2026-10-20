"""TimeDelta precision selects a time unit, not a rounding resolution."""

import datetime as dt

import pytest

from marshmallow import Schema, fields


@pytest.mark.parametrize(
    ("unit", "serialized"),
    [
        ("seconds", 0.000123),
        ("milliseconds", 0.123),
        ("microseconds", 123.0),
    ],
)
def test_subunit_timedelta_roundtrips_without_truncation(unit, serialized):
    class DurationSchema(Schema):
        duration = fields.TimeDelta(precision=unit)

    schema = DurationSchema()
    value = dt.timedelta(microseconds=123)
    assert schema.dump({"duration": value})["duration"] == pytest.approx(serialized)
    assert schema.load({"duration": serialized})["duration"] == value


@pytest.mark.parametrize("microseconds", [-123, 123])
def test_default_seconds_unit_preserves_subsecond_values(microseconds):
    # A named "precision" should not silently round the default seconds unit.
    class DurationSchema(Schema):
        duration = fields.TimeDelta()

    schema = DurationSchema()
    value = dt.timedelta(microseconds=microseconds)
    dumped = schema.dump({"duration": value})
    assert dumped["duration"] == pytest.approx(microseconds / 1_000_000)
    assert schema.load(dumped)["duration"] == value
