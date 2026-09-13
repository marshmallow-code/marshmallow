import pytest

from marshmallow import Schema, ValidationError, fields


class BoolSchema(Schema):
    is_active = fields.Boolean(required=True)
    opt_flag = fields.Boolean(load_default=False)


def test_boolean_field_truthy_string_deserialization():
    schema = BoolSchema()
    data = schema.load({"is_active": "true", "opt_flag": "1"})
    assert data == {"is_active": True, "opt_flag": True}


def test_boolean_field_falsy_string_deserialization():
    schema = BoolSchema()
    data = schema.load({"is_active": "false", "opt_flag": "0"})
    assert data == {"is_active": False, "opt_flag": False}


def test_boolean_field_invalid_string_raises():
    schema = BoolSchema()
    with pytest.raises(ValidationError):
        schema.load({"is_active": "invalid_bool"})
