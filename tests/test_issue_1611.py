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


def test_valid_meta_options_control_field_behaviour():
    class EmployeeSchema(Schema):
        name = fields.Str()
        age = fields.Int()

        class Meta:
            load_only = ("age",)
            dump_only = ("name",)

    schema = EmployeeSchema()

    assert schema.dump({"name": "Ama", "age": 21}) == {"name": "Ama"}
    assert schema.load({"age": 21}) == {"age": 21}


def test_meta_options_are_inherited():
    class ParentSchema(Schema):
        name = fields.Str()
        age = fields.Int()

        class Meta:
            load_only = ("age",)
            dump_only = ("name",)

    class ChildSchema(ParentSchema):
        pass

    schema = ChildSchema()

    assert schema.load_only == {"age"}
    assert schema.dump_only == {"name"}
