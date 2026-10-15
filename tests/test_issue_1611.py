import pytest

from marshmallow import Schema, fields
from marshmallow.exceptions import StringNotCollectionError


class UserSchema(Schema):
    name = fields.Str()
    age = fields.Int()


@pytest.mark.parametrize("option", ["load_only", "dump_only"])
def test_field_options_reject_string(option):
    with pytest.raises(StringNotCollectionError):
        UserSchema(**{option: "name"})


@pytest.mark.parametrize("option", ["load_only", "dump_only"])
@pytest.mark.parametrize(
    "value",
    [
        ["name"],
        ("name",),
        {"name"},
    ],
)
def test_field_options_accept_collections(option, value):
    schema = UserSchema(**{option: value})

    assert getattr(schema, option) == {"name"}


def test_meta_load_only_rejects_string():
    with pytest.raises(ValueError, match="load_only"):

        class InvalidSchema(Schema):
            name = fields.Str()

            class Meta:
                load_only = "name"


def test_meta_dump_only_rejects_string():
    with pytest.raises(ValueError, match="dump_only"):

        class InvalidSchema(Schema):
            name = fields.Str()

            class Meta:
                dump_only = "name"
