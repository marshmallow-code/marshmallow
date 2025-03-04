import datetime as dt
import math
import random
from collections import OrderedDict
from typing import NamedTuple

import pytest
import simplejson as json

from marshmallow import (
    EXCLUDE,
    INCLUDE,
    RAISE,
    Schema,
    class_registry,
    fields,
    validate,
    validates,
    validates_schema,
)
from marshmallow.exceptions import (
    RegistryError,
    StringNotCollectionError,
    ValidationError,
)
from tests.base import (
    Blog,
    BlogOnlySchema,
    BlogSchema,
    BlogSchemaExclude,
    ExtendedUserSchema,
    User,
    UserExcludeSchema,
    UserFloatStringSchema,
    UserIntSchema,
    UserRelativeUrlSchema,
    UserSchema,
    mockjson,
)

random.seed(1)


def test_serializing_basic_object(user):
    s = UserSchema()
    data = s.dump(user)
    assert data["name"] == user.name
    assert math.isclose(data["age"], 42.3)
    assert data["registered"]


def test_serializer_dump(user):
    s = UserSchema()
    result = s.dump(user)
    assert result["name"] == user.name


def test_load_resets_errors():
    class MySchema(Schema):
        email = fields.Email()

    schema = MySchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": "Joe", "email": "notvalid"})
    errors = excinfo.value.messages
    assert len(errors["email"]) == 1
    assert "Not a valid email address." in errors["email"][0]
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": "Joe", "email": "__invalid"})
    errors = excinfo.value.messages
    assert len(errors["email"]) == 1
    assert "Not a valid email address." in errors["email"][0]


def test_load_validation_error_stores_input_data_and_valid_data():
    def validator(val):
        raise ValidationError("oops")

    class MySchema(Schema):
        always_valid = fields.DateTime()
        always_invalid = fields.Raw(validate=[validator])

    schema = MySchema()
    input_data = {
        "always_valid": dt.datetime.now(dt.timezone.utc).isoformat(),
        "always_invalid": 24,
    }
    with pytest.raises(ValidationError) as excinfo:
        schema.load(input_data)
    err = excinfo.value
    # err.data is the raw input data
    assert err.data == input_data
    assert isinstance(err.valid_data, dict)
    assert "always_valid" in err.valid_data
    # err.valid_data contains valid, deserialized data
    assert isinstance(err.valid_data["always_valid"], dt.datetime)
    # excludes invalid data
    assert "always_invalid" not in err.valid_data


def test_load_resets_error_fields():
    class MySchema(Schema):
        email = fields.Email()
        name = fields.Str()

    schema = MySchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": "Joe", "email": "not-valid"})
    exc = excinfo.value
    assert isinstance(exc.messages, dict)
    assert len(exc.messages.keys()) == 1

    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": 12, "email": "mick@stones.com"})
    exc = excinfo.value


def test_errored_fields_do_not_appear_in_output():
    class MyField(fields.Field[int]):
        # Make sure validation fails during serialization
        def _serialize(self, value, attr, obj, **kwargs):
            raise ValidationError("oops")

    def validator(val):
        raise ValidationError("oops")

    class MySchema(Schema):
        foo = MyField(validate=validator)

    sch = MySchema()
    with pytest.raises(ValidationError) as excinfo:
        sch.load({"foo": 2})
    data, errors = excinfo.value.valid_data, excinfo.value.messages

    assert "foo" in errors
    assert isinstance(data, dict)
    assert "foo" not in data


def test_load_many_stores_error_indices():
    s = UserSchema()
    data = [
        {"name": "Mick", "email": "mick@stones.com"},
        {"name": "Keith", "email": "invalid-email", "homepage": "invalid-homepage"},
    ]
    with pytest.raises(ValidationError) as excinfo:
        s.load(data, many=True)
    errors = excinfo.value.messages
    assert 0 not in errors
    assert 1 in errors
    assert "email" in errors[1]
    assert "homepage" in errors[1]


def test_dump_many():
    s = UserSchema()
    u1, u2 = User("Mick"), User("Keith")
    data = s.dump([u1, u2], many=True)
    assert len(data) == 2
    assert data[0] == s.dump(u1)


def test_multiple_errors_can_be_stored_for_a_given_index():
    class MySchema(Schema):
        foo = fields.Str(validate=validate.Length(min=4))
        bar = fields.Int(validate=validate.Range(min=4))

    sch = MySchema()
    valid = {"foo": "loll", "bar": 42}
    invalid = {"foo": "lol", "bar": 3}
    errors = sch.validate([valid, invalid], many=True)

    assert 1 in errors
    assert len(errors[1]) == 2
    assert "foo" in errors[1]
    assert "bar" in errors[1]


def test_dump_returns_a_dict(user):
    s = UserSchema()
    result = s.dump(user)
    assert type(result) is dict


def test_dumps_returns_a_string(user):
    s = UserSchema()
    result = s.dumps(user)
    assert type(result) is str


def test_dumping_single_object_with_collection_schema(user):
    s = UserSchema(many=True)
    result = s.dump(user, many=False)
    assert type(result) is dict
    assert result == UserSchema().dump(user)


def test_loading_single_object_with_collection_schema():
    s = UserSchema(many=True)
    in_data = {"name": "Mick", "email": "mick@stones.com"}
    result = s.load(in_data, many=False)
    assert type(result) is User
    assert result.name == UserSchema().load(in_data).name


def test_dumps_many():
    s = UserSchema()
    u1, u2 = User("Mick"), User("Keith")
    json_result = s.dumps([u1, u2], many=True)
    data = json.loads(json_result)
    assert len(data) == 2
    assert data[0] == s.dump(u1)


def test_load_returns_an_object():
    s = UserSchema()
    result = s.load({"name": "Monty"})
    assert type(result) is User


def test_load_many():
    s = UserSchema()
    in_data = [{"name": "Mick"}, {"name": "Keith"}]
    result = s.load(in_data, many=True)
    assert type(result) is list
    assert type(result[0]) is User
    assert result[0].name == "Mick"


@pytest.mark.parametrize("val", (None, False, 1, 1.2, object(), [], set(), "lol"))
def test_load_invalid_input_type(val):
    class Sch(Schema):
        name = fields.Str()

    with pytest.raises(ValidationError) as e:
        Sch().load(val)
    assert e.value.messages == {"_schema": ["Invalid input type."]}
    assert e.value.valid_data == {}


# regression test for https://github.com/marshmallow-code/marshmallow/issues/906
@pytest.mark.parametrize("val", (None, False, 1, 1.2, object(), {}, {"1": 2}, "lol"))
def test_load_many_invalid_input_type(val):
    class Sch(Schema):
        name = fields.Str()

    with pytest.raises(ValidationError) as e:
        Sch(many=True).load(val)
    assert e.value.messages == {"_schema": ["Invalid input type."]}
    assert e.value.valid_data == []


@pytest.mark.parametrize("val", ([], tuple()))
def test_load_many_empty_collection(val):
    class Sch(Schema):
        name = fields.Str()

    assert Sch(many=True).load(val) == []


@pytest.mark.parametrize("val", (False, 1, 1.2, object(), {}, {"1": 2}, "lol"))
def test_load_many_in_nested_invalid_input_type(val):
    class Inner(Schema):
        name = fields.String()

    class Outer(Schema):
        list1 = fields.List(fields.Nested(Inner))
        list2 = fields.Nested(Inner, many=True)

    with pytest.raises(ValidationError) as e:
        Outer().load({"list1": val, "list2": val})
    # TODO: Error messages should be identical (#779)
    assert e.value.messages == {
        "list1": ["Not a valid list."],
        "list2": ["Invalid type."],
    }


@pytest.mark.parametrize("val", ([], tuple()))
def test_load_many_in_nested_empty_collection(val):
    class Inner(Schema):
        name = fields.String()

    class Outer(Schema):
        list1 = fields.List(fields.Nested(Inner))
        list2 = fields.Nested(Inner, many=True)

    assert Outer().load({"list1": val, "list2": val}) == {"list1": [], "list2": []}


def test_loads_returns_a_user():
    s = UserSchema()
    result = s.loads(json.dumps({"name": "Monty"}))
    assert type(result) is User


def test_loads_many():
    s = UserSchema()
    in_data = [{"name": "Mick"}, {"name": "Keith"}]
    in_json_data = json.dumps(in_data)
    result = s.loads(in_json_data, many=True)
    assert type(result) is list
    assert result[0].name == "Mick"


def test_loads_deserializes_from_json():
    user_dict = {"name": "Monty", "age": "42.3"}
    user_json = json.dumps(user_dict)
    result = UserSchema().loads(user_json)
    assert isinstance(result, User)
    assert result.name == "Monty"
    assert math.isclose(result.age, 42.3)


def test_serializing_none():
    class MySchema(Schema):
        id = fields.Str(dump_default="no-id")
        num = fields.Int()
        name = fields.Str()

    data = UserSchema().dump(None)
    assert data == {"id": "no-id"}


def test_default_many_symmetry():
    """The dump/load(s) methods should all default to the many value of the schema."""
    s_many = UserSchema(many=True, only=("name",))
    s_single = UserSchema(only=("name",))
    u1, u2 = User("King Arthur"), User("Sir Lancelot")
    s_single.load(s_single.dump(u1))
    s_single.loads(s_single.dumps(u1))
    s_many.load(s_many.dump([u1, u2]))
    s_many.loads(s_many.dumps([u1, u2]))


def test_on_bind_field_hook():
    class MySchema(Schema):
        foo = fields.Str()

        def on_bind_field(self, field_name, field_obj):
            assert field_obj.parent is self
            field_obj.metadata["fname"] = field_name

    schema = MySchema()
    assert schema.fields["foo"].metadata["fname"] == "foo"


def test_nested_on_bind_field_hook():
    class MySchema(Schema):
        class NestedSchema(Schema):
            bar = fields.Str()

            def on_bind_field(self, field_name, field_obj):
                assert field_obj.parent is self
                field_obj.metadata["fname"] = field_name

        foo = fields.Nested(NestedSchema)

    schema = MySchema()
    foo_field = schema.fields["foo"]
    assert isinstance(foo_field, fields.Nested)
    assert foo_field.schema.fields["bar"].metadata["fname"] == "bar"


class TestValidate:
    def test_validate_raises_with_errors_dict(self):
        s = UserSchema()
        errors = s.validate({"email": "bad-email", "name": "Valid Name"})
        assert type(errors) is dict
        assert "email" in errors
        assert "name" not in errors

        valid_data = {"name": "Valid Name", "email": "valid@email.com"}
        errors = s.validate(valid_data)
        assert errors == {}

    def test_validate_many(self):
        s = UserSchema(many=True)
        in_data = [
            {"name": "Valid Name", "email": "validemail@hotmail.com"},
            {"name": "Valid Name2", "email": "invalid"},
        ]
        errors = s.validate(in_data, many=True)
        assert 1 in errors
        assert "email" in errors[1]

    def test_validate_many_doesnt_store_index_if_index_errors_option_is_false(self):
        class NoIndex(Schema):
            email = fields.Email()

            class Meta:
                index_errors = False

        s = NoIndex()
        in_data = [
            {"name": "Valid Name", "email": "validemail@hotmail.com"},
            {"name": "Valid Name2", "email": "invalid"},
        ]
        errors = s.validate(in_data, many=True)
        assert 1 not in errors
        assert "email" in errors

    def test_validate(self):
        s = UserSchema()
        errors = s.validate({"email": "bad-email"})
        assert errors == {"email": ["Not a valid email address."]}

    def test_validate_required(self):
        class MySchema(Schema):
            foo = fields.Raw(required=True)

        s = MySchema()
        errors = s.validate({"bar": 42})
        assert "foo" in errors
        assert "required" in errors["foo"][0]


def test_fields_are_not_copies():
    s = UserSchema()
    s2 = UserSchema()
    assert s.fields is not s2.fields


def test_dumps_returns_json(user):
    ser = UserSchema()
    serialized = ser.dump(user)
    json_data = ser.dumps(user)
    assert type(json_data) is str
    expected = json.dumps(serialized)
    assert json_data == expected


def test_naive_datetime_field(user, serialized_user):
    expected = user.created.isoformat()
    assert serialized_user["created"] == expected


def test_datetime_formatted_field(user, serialized_user):
    result = serialized_user["created_formatted"]
    assert result == user.created.strftime("%Y-%m-%d")


def test_datetime_iso_field(user, serialized_user):
    assert serialized_user["created_iso"] == user.created.isoformat()


def test_tz_datetime_field(user, serialized_user):
    # Datetime is corrected back to GMT
    expected = user.updated.isoformat()
    assert serialized_user["updated"] == expected


def test_class_variable(serialized_user):
    assert serialized_user["species"] == "Homo sapiens"


def test_serialize_many():
    user1 = User(name="Mick", age=123)
    user2 = User(name="Keith", age=456)
    users = [user1, user2]
    serialized = UserSchema(many=True).dump(users)
    assert len(serialized) == 2
    assert serialized[0]["name"] == "Mick"
    assert serialized[1]["name"] == "Keith"


def test_inheriting_schema(user):
    sch = ExtendedUserSchema()
    result = sch.dump(user)
    assert result["name"] == user.name
    user.is_old = True
    result = sch.dump(user)
    assert result["is_old"] is True


def test_custom_field(serialized_user, user):
    assert serialized_user["uppername"] == user.name.upper()


def test_url_field(serialized_user, user):
    assert serialized_user["homepage"] == user.homepage


def test_relative_url_field():
    u = {"name": "John", "homepage": "/foo"}
    UserRelativeUrlSchema().load(u)


def test_stores_invalid_url_error():
    user = {"name": "Steve", "homepage": "www.foo.com"}
    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load(user)
    errors = excinfo.value.messages
    assert "homepage" in errors
    expected = ["Not a valid URL."]
    assert errors["homepage"] == expected


def test_email_field():
    u = User("John", email="john@example.com")
    s = UserSchema().dump(u)
    assert s["email"] == "john@example.com"


def test_stored_invalid_email():
    u = {"name": "John", "email": "johnexample.com"}
    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load(u)
    errors = excinfo.value.messages
    assert "email" in errors
    assert errors["email"][0] == "Not a valid email address."


def test_integer_field():
    u = User("John", age=42.3)
    serialized = UserIntSchema().dump(u)
    assert type(serialized["age"]) is int
    assert serialized["age"] == 42


def test_as_string():
    u = User("John", age=42.3)
    serialized = UserFloatStringSchema().dump(u)
    assert type(serialized["age"]) is str
    assert math.isclose(float(serialized["age"]), 42.3)


def test_method_field(serialized_user):
    assert serialized_user["is_old"] is False
    u = User("Joe", age=81)
    assert UserSchema().dump(u)["is_old"] is True


def test_function_field(serialized_user, user):
    assert serialized_user["lowername"] == user.name.lower()


def test_fields_must_be_declared_as_instances(user):
    with pytest.raises(
        TypeError, match='Field for "name" must be declared as a Field instance'
    ):

        class BadUserSchema(Schema):
            name = fields.String


# regression test
def test_bind_field_does_not_swallow_typeerror():
    class MySchema(Schema):
        name = fields.Str()

        def on_bind_field(self, field_name, field_obj):
            raise TypeError("boom")

    with pytest.raises(TypeError, match="boom"):
        MySchema()


def test_serializing_generator():
    users = [User("Foo"), User("Bar")]
    user_gen = (u for u in users)
    s = UserSchema(many=True).dump(user_gen)
    assert len(s) == 2
    assert s[0] == UserSchema().dump(users[0])


def test_serializing_empty_list_returns_empty_list():
    assert UserSchema(many=True).dump([]) == []


def test_serializing_dict():
    user = {
        "name": "foo",
        "email": "foo@bar.com",
        "age": 42,
        "various_data": {"foo": "bar"},
    }
    data = UserSchema().dump(user)
    assert data["name"] == "foo"
    assert data["age"] == 42
    assert data["various_data"] == {"foo": "bar"}


def test_exclude_in_init(user):
    s = UserSchema(exclude=("age", "homepage")).dump(user)
    assert "homepage" not in s
    assert "age" not in s
    assert "name" in s


def test_only_in_init(user):
    s = UserSchema(only=("name", "age")).dump(user)
    assert "homepage" not in s
    assert "name" in s
    assert "age" in s


def test_invalid_only_param(user):
    with pytest.raises(ValueError):
        UserSchema(only=("_invalid", "name")).dump(user)


def test_can_serialize_uuid(serialized_user, user):
    assert serialized_user["uid"] == str(user.uid)


def test_can_serialize_time(user, serialized_user):
    expected = user.time_registered.isoformat()[:15]
    assert serialized_user["time_registered"] == expected


def test_render_module():
    class UserJSONSchema(Schema):
        name = fields.String()

        class Meta:
            render_module = mockjson

    user = User("Joe")
    s = UserJSONSchema()
    result = s.dumps(user)
    assert result == mockjson.dumps("val")


def test_custom_error_message():
    class ErrorSchema(Schema):
        email = fields.Email(error_messages={"invalid": "Invalid email"})
        homepage = fields.Url(error_messages={"invalid": "Bad homepage."})
        balance = fields.Decimal(error_messages={"invalid": "Bad balance."})

    u = {"email": "joe.net", "homepage": "joe@example.com", "balance": "blah"}
    s = ErrorSchema()
    with pytest.raises(ValidationError) as excinfo:
        s.load(u)
    errors = excinfo.value.messages
    assert "Bad balance." in errors["balance"]
    assert "Bad homepage." in errors["homepage"]
    assert "Invalid email" in errors["email"]


def test_custom_unknown_error_message():
    custom_message = "custom error message."

    class ErrorSchema(Schema):
        error_messages = {"unknown": custom_message}
        name = fields.String()

    s = ErrorSchema()
    u = {"name": "Joe", "age": 13}
    with pytest.raises(ValidationError) as excinfo:
        s.load(u)
    errors = excinfo.value.messages
    assert custom_message in errors["age"]


def test_custom_type_error_message():
    custom_message = "custom error message."

    class ErrorSchema(Schema):
        error_messages = {"type": custom_message}
        name = fields.String()

    s = ErrorSchema()
    u = ["Joe"]
    with pytest.raises(ValidationError) as excinfo:
        s.load(u)  # type: ignore[arg-type]
    errors = excinfo.value.messages
    assert custom_message in errors["_schema"]


def test_custom_type_error_message_with_many():
    custom_message = "custom error message."

    class ErrorSchema(Schema):
        error_messages = {"type": custom_message}
        name = fields.String()

    s = ErrorSchema(many=True)
    u = {"name": "Joe"}
    with pytest.raises(ValidationError) as excinfo:
        s.load(u)
    errors = excinfo.value.messages
    assert custom_message in errors["_schema"]


def test_custom_error_messages_with_inheritance():
    parent_type_message = "parent type error message."
    parent_unknown_message = "parent unknown error message."
    child_type_message = "child type error message."

    class ParentSchema(Schema):
        error_messages = {
            "type": parent_type_message,
            "unknown": parent_unknown_message,
        }
        name = fields.String()

    class ChildSchema(ParentSchema):
        error_messages = {"type": child_type_message}

    unknown_user = {"name": "Eleven", "age": 12}

    parent_schema = ParentSchema()
    with pytest.raises(ValidationError) as excinfo:
        parent_schema.load(unknown_user)
    assert parent_unknown_message in excinfo.value.messages["age"]
    with pytest.raises(ValidationError) as excinfo:
        parent_schema.load(11)  # type: ignore[arg-type]
    assert parent_type_message in excinfo.value.messages["_schema"]

    child_schema = ChildSchema()
    with pytest.raises(ValidationError) as excinfo:
        child_schema.load(unknown_user)
    assert parent_unknown_message in excinfo.value.messages["age"]
    with pytest.raises(ValidationError) as excinfo:
        child_schema.load(11)  # type: ignore[arg-type]
    assert child_type_message in excinfo.value.messages["_schema"]


def test_load_errors_with_many():
    class ErrorSchema(Schema):
        email = fields.Email()

    data = [
        {"email": "bademail"},
        {"email": "goo@email.com"},
        {"email": "anotherbademail"},
    ]

    with pytest.raises(ValidationError) as excinfo:
        ErrorSchema(many=True).load(data)
    errors = excinfo.value.messages
    assert 0 in errors
    assert 2 in errors
    assert "Not a valid email address." in errors[0]["email"][0]
    assert "Not a valid email address." in errors[2]["email"][0]


def test_error_raised_if_fields_option_is_not_list():
    with pytest.raises(ValueError):

        class BadSchema(Schema):
            name = fields.String()

            class Meta:
                fields = "name"


def test_nested_custom_set_in_exclude_reusing_schema():
    class CustomSet:
        # This custom set is to allow the obj check in BaseSchema.__filter_fields
        # to pass, since it'll be a valid instance, and this class overrides
        # getitem method to allow the hasattr check to pass too, which will try
        # to access the first obj index and will simulate a IndexError throwing.
        # e.g. SqlAlchemy.Query is a valid use case for this 'obj'.

        def __getitem__(self, item):
            return [][item]

    class ChildSchema(Schema):
        foo = fields.Raw(required=True)
        bar = fields.Raw()

        class Meta:
            only = ("bar",)

    class ParentSchema(Schema):
        child = fields.Nested(ChildSchema, many=True, exclude=("foo",))

    sch = ParentSchema()
    obj = dict(child=CustomSet())
    sch.dumps(obj)
    data = dict(child=[{"bar": 1}])
    sch.load(data, partial=True)


def test_nested_only():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema)

    sch = ParentSchema(only=("bla", "blubb.foo", "blubb.bar"))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_only_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema, only=("foo", "bar"))

    sch = ParentSchema(only=("blubb.foo", "blubb.baz"))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" not in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" in child
    assert "bar" not in child
    assert "baz" not in child


def test_nested_only_empty_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema, only=("bar",))

    sch = ParentSchema(only=("blubb.foo",))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" not in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" not in child
    assert "baz" not in child


def test_nested_exclude():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema)

    sch = ParentSchema(exclude=("bli", "blubb.baz"))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_exclude_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema, exclude=("baz",))

    sch = ParentSchema(exclude=("blubb.foo",))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_only_and_exclude():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema)

    sch = ParentSchema(only=("bla", "blubb.foo", "blubb.bar"), exclude=("blubb.foo",))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_only_then_exclude_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema, only=("foo", "bar"))

    sch = ParentSchema(exclude=("blubb.foo",))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_exclude_then_only_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema, exclude=("foo",))

    sch = ParentSchema(only=("blubb.bar",))
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" not in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" not in child


def test_nested_exclude_and_only_inheritance():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()
        ban = fields.Raw()
        fuu = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(
            ChildSchema, only=("foo", "bar", "baz", "ban"), exclude=("foo",)
        )

    sch = ParentSchema(
        only=("blubb.foo", "blubb.bar", "blubb.baz"), exclude=("blubb.baz",)
    )
    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert "bla" not in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" not in child
    assert "ban" not in child
    assert "fuu" not in child


# https://github.com/marshmallow-code/marshmallow/issues/1160
def test_nested_instance_many():
    class BookSchema(Schema):
        id = fields.Int()
        title = fields.String()

    class UserSchema(Schema):
        id = fields.Int()
        name = fields.String()
        books = fields.Nested(BookSchema(many=True))

    books = [{"id": 1, "title": "First book"}, {"id": 2, "title": "Second book"}]
    user = {"id": 1, "name": "Peter", "books": books}

    user_dump = UserSchema().dump(user)
    assert user_dump["books"] == books

    user_load = UserSchema().load(user_dump)
    assert user_load == user


def test_nested_instance_only():
    class ArtistSchema(Schema):
        first = fields.Str()
        last = fields.Str()

    class AlbumSchema(Schema):
        title = fields.Str()
        artist = fields.Nested(ArtistSchema(), only=("last",))

    schema = AlbumSchema()
    album = {"title": "Hunky Dory", "artist": {"last": "Bowie"}}
    loaded = schema.load(album)
    assert loaded == album
    full_album = {"title": "Hunky Dory", "artist": {"first": "David", "last": "Bowie"}}
    assert schema.dump(full_album) == album


def test_nested_instance_exclude():
    class ArtistSchema(Schema):
        first = fields.Str()
        last = fields.Str()

    class AlbumSchema(Schema):
        title = fields.Str()
        artist = fields.Nested(ArtistSchema(), exclude=("first",))

    schema = AlbumSchema()
    album = {"title": "Hunky Dory", "artist": {"last": "Bowie"}}
    loaded = schema.load(album)
    assert loaded == album
    full_album = {"title": "Hunky Dory", "artist": {"first": "David", "last": "Bowie"}}
    assert schema.dump(full_album) == album


def test_meta_nested_exclude():
    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema)

        class Meta:
            exclude = ("blubb.foo",)

    data = dict(bla=1, bli=2, blubb=dict(foo=42, bar=24, baz=242))

    sch = ParentSchema()
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" in child

    # Test fields with dot notations in Meta.exclude on multiple instantiations
    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/1212
    sch = ParentSchema()
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" in result
    child = result["blubb"]
    assert "foo" not in child
    assert "bar" in child
    assert "baz" in child


def test_nested_custom_set_not_implementing_getitem():
    # This test checks that marshmallow can serialize implementations of
    # :mod:`collections.abc.MutableSequence`, with ``__getitem__`` arguments
    # that are not integers.

    class ListLikeParent:
        """
        Implements a list-like object that can get children using a
        non-integer key
        """

        def __init__(self, required_key, child):
            """
            :param required_key: The key to use in ``__getitem__`` in order
                to successfully get the ``child``
            :param child: The return value of the ``child`` if
            ``__getitem__`` succeeds
            """
            self.children = {required_key: child}

    class Child:
        """
        Implements an object with some attribute
        """

        def __init__(self, attribute: str):
            """
            :param attribute: The attribute to initialize
            """
            self.attribute = attribute

    class ChildSchema(Schema):
        """
        The marshmallow schema for the child
        """

        attribute = fields.Str()

    class ParentSchema(Schema):
        """
        The schema for the parent
        """

        children = fields.Nested(ChildSchema, many=True)

    attribute = "Foo"
    required_key = "key"
    child = Child(attribute)

    parent = ListLikeParent(required_key, child)

    ParentSchema().dump(parent)


def test_deeply_nested_only_and_exclude():
    class GrandChildSchema(Schema):
        goo = fields.Raw()
        gah = fields.Raw()
        bah = fields.Raw()

    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        flubb = fields.Nested(GrandChildSchema)

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(ChildSchema)

    sch = ParentSchema(
        only=("bla", "blubb.foo", "blubb.flubb.goo", "blubb.flubb.gah"),
        exclude=("blubb.flubb.goo",),
    )
    data = dict(bla=1, bli=2, blubb=dict(foo=3, bar=4, flubb=dict(goo=5, gah=6, bah=7)))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" in child
    assert "flubb" in child
    assert "bar" not in child
    grand_child = child["flubb"]
    assert "gah" in grand_child
    assert "goo" not in grand_child
    assert "bah" not in grand_child


def test_nested_lambda():
    class ChildSchema(Schema):
        id = fields.Str()
        name = fields.Str()
        parent = fields.Nested(lambda: ParentSchema(only=("id",)), dump_only=True)
        siblings = fields.List(fields.Nested(lambda: ChildSchema(only=("id", "name"))))

    class ParentSchema(Schema):
        id = fields.Str()
        spouse = fields.Nested(lambda: ParentSchema(only=("id",)))
        children = fields.List(
            fields.Nested(lambda: ChildSchema(only=("id", "parent", "siblings")))
        )

    sch = ParentSchema()
    data_to_load = {
        "id": "p1",
        "spouse": {"id": "p2"},
        "children": [{"id": "c1", "siblings": [{"id": "c2", "name": "sis"}]}],
    }
    loaded = sch.load(data_to_load)
    assert loaded == data_to_load

    data_to_dump = dict(
        id="p2",
        spouse=dict(id="p2"),
        children=[
            dict(
                id="c1",
                name="bar",
                parent=dict(id="p2"),
                siblings=[dict(id="c2", name="sis")],
            )
        ],
    )
    dumped = sch.dump(data_to_dump)
    assert dumped == {
        "id": "p2",
        "spouse": {"id": "p2"},
        "children": [
            {
                "id": "c1",
                "parent": {"id": "p2"},
                "siblings": [{"id": "c2", "name": "sis"}],
            }
        ],
    }


@pytest.mark.parametrize("data_key", ("f1", "f5", None))
def test_data_key_collision(data_key):
    class MySchema(Schema):
        f1 = fields.Raw()
        f2 = fields.Raw(data_key=data_key)
        f3 = fields.Raw(data_key="f5")
        f4 = fields.Raw(data_key="f1", load_only=True)

    if data_key is None:
        MySchema()
    else:
        with pytest.raises(ValueError, match=data_key):
            MySchema()


@pytest.mark.parametrize("attribute", ("f1", "f5", None))
def test_attribute_collision(attribute):
    class MySchema(Schema):
        f1 = fields.Raw()
        f2 = fields.Raw(attribute=attribute)
        f3 = fields.Raw(attribute="f5")
        f4 = fields.Raw(attribute="f1", dump_only=True)

    if attribute is None:
        MySchema()
    else:
        with pytest.raises(ValueError, match=attribute):
            MySchema()


class TestDeeplyNestedLoadOnly:
    @pytest.fixture
    def schema(self):
        class GrandChildSchema(Schema):
            str_dump_only = fields.String()
            str_load_only = fields.String()
            str_regular = fields.String()

        class ChildSchema(Schema):
            str_dump_only = fields.String()
            str_load_only = fields.String()
            str_regular = fields.String()
            grand_child = fields.Nested(GrandChildSchema, unknown=EXCLUDE)

        class ParentSchema(Schema):
            str_dump_only = fields.String()
            str_load_only = fields.String()
            str_regular = fields.String()
            child = fields.Nested(ChildSchema, unknown=EXCLUDE)

        return ParentSchema(
            dump_only=(
                "str_dump_only",
                "child.str_dump_only",
                "child.grand_child.str_dump_only",
            ),
            load_only=(
                "str_load_only",
                "child.str_load_only",
                "child.grand_child.str_load_only",
            ),
        )

    @pytest.fixture
    def data(self):
        return dict(
            str_dump_only="Dump Only",
            str_load_only="Load Only",
            str_regular="Regular String",
            child=dict(
                str_dump_only="Dump Only",
                str_load_only="Load Only",
                str_regular="Regular String",
                grand_child=dict(
                    str_dump_only="Dump Only",
                    str_load_only="Load Only",
                    str_regular="Regular String",
                ),
            ),
        )

    def test_load_only(self, schema, data):
        result = schema.dump(data)
        assert "str_load_only" not in result
        assert "str_dump_only" in result
        assert "str_regular" in result
        child = result["child"]
        assert "str_load_only" not in child
        assert "str_dump_only" in child
        assert "str_regular" in child
        grand_child = child["grand_child"]
        assert "str_load_only" not in grand_child
        assert "str_dump_only" in grand_child
        assert "str_regular" in grand_child

    def test_dump_only(self, schema, data):
        result = schema.load(data, unknown=EXCLUDE)
        assert "str_dump_only" not in result
        assert "str_load_only" in result
        assert "str_regular" in result
        child = result["child"]
        assert "str_dump_only" not in child
        assert "str_load_only" in child
        assert "str_regular" in child
        grand_child = child["grand_child"]
        assert "str_dump_only" not in grand_child
        assert "str_load_only" in grand_child
        assert "str_regular" in grand_child


class TestDeeplyNestedListLoadOnly:
    @pytest.fixture
    def schema(self):
        class ChildSchema(Schema):
            str_dump_only = fields.String()
            str_load_only = fields.String()
            str_regular = fields.String()

        class ParentSchema(Schema):
            str_dump_only = fields.String()
            str_load_only = fields.String()
            str_regular = fields.String()
            child = fields.List(fields.Nested(ChildSchema, unknown=EXCLUDE))

        return ParentSchema(
            dump_only=("str_dump_only", "child.str_dump_only"),
            load_only=("str_load_only", "child.str_load_only"),
        )

    @pytest.fixture
    def data(self):
        return dict(
            str_dump_only="Dump Only",
            str_load_only="Load Only",
            str_regular="Regular String",
            child=[
                dict(
                    str_dump_only="Dump Only",
                    str_load_only="Load Only",
                    str_regular="Regular String",
                )
            ],
        )

    def test_load_only(self, schema, data):
        result = schema.dump(data)
        assert "str_load_only" not in result
        assert "str_dump_only" in result
        assert "str_regular" in result
        child = result["child"][0]
        assert "str_load_only" not in child
        assert "str_dump_only" in child
        assert "str_regular" in child

    def test_dump_only(self, schema, data):
        result = schema.load(data, unknown=EXCLUDE)
        assert "str_dump_only" not in result
        assert "str_load_only" in result
        assert "str_regular" in result
        child = result["child"][0]
        assert "str_dump_only" not in child
        assert "str_load_only" in child
        assert "str_regular" in child


def test_nested_constructor_only_and_exclude():
    class GrandChildSchema(Schema):
        goo = fields.Raw()
        gah = fields.Raw()
        bah = fields.Raw()

    class ChildSchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        flubb = fields.Nested(GrandChildSchema)

    class ParentSchema(Schema):
        bla = fields.Raw()
        bli = fields.Raw()
        blubb = fields.Nested(
            ChildSchema, only=("foo", "flubb.goo", "flubb.gah"), exclude=("flubb.goo",)
        )

    sch = ParentSchema(only=("bla", "blubb"))
    data = dict(bla=1, bli=2, blubb=dict(foo=3, bar=4, flubb=dict(goo=5, gah=6, bah=7)))
    result = sch.dump(data)
    assert "bla" in result
    assert "blubb" in result
    assert "bli" not in result
    child = result["blubb"]
    assert "foo" in child
    assert "flubb" in child
    assert "bar" not in child
    grand_child = child["flubb"]
    assert "gah" in grand_child
    assert "goo" not in grand_child
    assert "bah" not in grand_child


def test_only_and_exclude():
    class MySchema(Schema):
        foo = fields.Raw()
        bar = fields.Raw()
        baz = fields.Raw()

    sch = MySchema(only=("foo", "bar"), exclude=("bar",))
    data = dict(foo=42, bar=24, baz=242)
    result = sch.dump(data)
    assert "foo" in result
    assert "bar" not in result


def test_invalid_only_and_exclude_with_fields():
    class MySchema(Schema):
        foo = fields.Raw()

        class Meta:
            fields = ("bar", "baz")

    with pytest.raises(ValueError) as excinfo:
        MySchema(only=("foo", "par"), exclude=("ban",))

    assert "foo" in str(excinfo.value)
    assert "par" in str(excinfo.value)
    assert "ban" in str(excinfo.value)


def test_exclude_invalid_attribute():
    class MySchema(Schema):
        foo = fields.Raw()

    with pytest.raises(ValueError, match="'bar'"):
        MySchema(exclude=("bar",))


def test_only_bounded_by_fields():
    class MySchema(Schema):
        class Meta:
            fields = ("foo",)

    with pytest.raises(ValueError, match="'baz'"):
        MySchema(only=("baz",))


def test_only_bounded_by_additional():
    class MySchema(Schema):
        class Meta:
            additional = ("b",)

    with pytest.raises(ValueError):
        MySchema(only=("c",)).dump({"c": 3})


def test_only_empty():
    class MySchema(Schema):
        foo = fields.Raw()

    sch = MySchema(only=())
    assert "foo" not in sch.dump({"foo": "bar"})


@pytest.mark.parametrize("param", ("only", "exclude"))
def test_only_and_exclude_as_string(param):
    class MySchema(Schema):
        foo = fields.Raw()

    with pytest.raises(StringNotCollectionError):
        MySchema(**{param: "foo"})  # type: ignore[arg-type]


def test_nested_with_sets():
    class Inner(Schema):
        foo = fields.Raw()

    class Outer(Schema):
        inners = fields.Nested(Inner, many=True)

    sch = Outer()

    class Thing(NamedTuple):
        foo: int

    data = dict(inners={Thing(42), Thing(2)})
    result = sch.dump(data)
    assert len(result["inners"]) == 2


def test_meta_field_not_on_obj_raises_attribute_error(user):
    class BadUserSchema(Schema):
        class Meta:
            fields = ("name",)
            exclude = ("notfound",)

    with pytest.raises(ValueError, match="'notfound'"):
        BadUserSchema().dump(user)


def test_exclude_fields(user):
    s = UserExcludeSchema().dump(user)
    assert "created" not in s
    assert "updated" not in s
    assert "name" in s


def test_fields_option_must_be_list_or_tuple():
    with pytest.raises(ValueError):

        class BadFields(Schema):
            class Meta:
                fields = "name"


def test_exclude_option_must_be_list_or_tuple():
    with pytest.raises(ValueError):

        class BadExclude(Schema):
            class Meta:
                exclude = "name"


def test_datetimeformat_option(user):
    meta_fmt = "%Y-%m"
    field_fmt = "%m-%d"

    class DateTimeFormatSchema(Schema):
        created = fields.DateTime()
        updated = fields.DateTime(field_fmt)

        class Meta:
            datetimeformat = meta_fmt

    serialized = DateTimeFormatSchema().dump(user)
    assert serialized["created"] == user.created.strftime(meta_fmt)
    assert serialized["updated"] == user.updated.strftime(field_fmt)


def test_dateformat_option(user):
    fmt = "%Y-%m"
    field_fmt = "%m-%d"

    class DateFormatSchema(Schema):
        birthdate = fields.Date(field_fmt)
        activation_date = fields.Date()

        class Meta:
            dateformat = fmt

    serialized = DateFormatSchema().dump(user)
    assert serialized["birthdate"] == user.birthdate.strftime(field_fmt)
    assert serialized["activation_date"] == user.activation_date.strftime(fmt)


def test_timeformat_option(user):
    fmt = "%H:%M:%S"
    field_fmt = "%H:%M"

    class TimeFormatSchema(Schema):
        birthtime = fields.Time(field_fmt)
        time_registered = fields.Time()

        class Meta:
            timeformat = fmt

    serialized = TimeFormatSchema().dump(user)
    assert serialized["birthtime"] == user.birthtime.strftime(field_fmt)
    assert serialized["time_registered"] == user.time_registered.strftime(fmt)


def test_default_dateformat(user):
    class DateFormatSchema(Schema):
        created = fields.DateTime()
        updated = fields.DateTime(format="%m-%d")

    serialized = DateFormatSchema().dump(user)
    assert serialized["created"] == user.created.isoformat()
    assert serialized["updated"] == user.updated.strftime("%m-%d")


class CustomError(Exception):
    pass


class MySchema(Schema):
    name = fields.String()
    email = fields.Email()
    age = fields.Integer()

    def handle_error(self, error, data, *args, **kwargs):
        raise CustomError("Something bad happened")

    def test_load_with_custom_error_handler(self):
        in_data = {"email": "invalid"}

        class MySchema3(Schema):
            email = fields.Email()

            def handle_error(self, error, data, **kwargs):
                assert type(error) is ValidationError
                assert "email" in error.messages
                assert isinstance(error.messages, dict)
                assert list(error.messages.keys()) == ["email"]
                assert data == in_data
                raise CustomError("Something bad happened")

        with pytest.raises(CustomError):
            MySchema3().load(in_data)

    def test_load_with_custom_error_handler_and_partially_valid_data(self):
        in_data = {"email": "invalid", "url": "http://valid.com"}

        class MySchema(Schema):
            email = fields.Email()
            url = fields.URL()

            def handle_error(self, error, data, **kwargs):
                assert type(error) is ValidationError
                assert "email" in error.messages
                assert isinstance(error.messages, dict)
                assert list(error.messages.keys()) == ["email"]
                assert data == in_data
                raise CustomError("Something bad happened")

        with pytest.raises(CustomError):
            MySchema().load(in_data)

    def test_custom_error_handler_with_validates_decorator(self):
        in_data = {"num": -1}

        class MySchema(Schema):
            num = fields.Int()

            @validates("num")
            def validate_num(self, value):
                if value < 0:
                    raise ValidationError("Must be greater than 0.")

            def handle_error(self, error, data, **kwargs):
                assert type(error) is ValidationError
                assert "num" in error.messages
                assert isinstance(error.messages, dict)
                assert list(error.messages.keys()) == ["num"]
                assert data == in_data
                raise CustomError("Something bad happened")

        with pytest.raises(CustomError):
            MySchema().load(in_data)

    def test_custom_error_handler_with_validates_schema_decorator(self):
        in_data = {"num": -1}

        class MySchema(Schema):
            num = fields.Int()

            @validates_schema
            def validates_schema(self, data, **kwargs):
                raise ValidationError("Invalid schema!")

            def handle_error(self, error, data, **kwargs):
                assert type(error) is ValidationError
                assert isinstance(error.messages, dict)
                assert list(error.messages.keys()) == ["_schema"]
                assert data == in_data
                raise CustomError("Something bad happened")

        with pytest.raises(CustomError):
            MySchema().load(in_data)

    def test_validate_with_custom_error_handler(self):
        with pytest.raises(CustomError):
            MySchema().validate({"age": "notvalid", "email": "invalid"})


class TestFieldValidation:
    def test_errors_are_cleared_after_loading_collection(self):
        def always_fail(val):
            raise ValidationError("lol")

        class MySchema(Schema):
            foo = fields.Str(validate=always_fail)

        schema = MySchema()
        with pytest.raises(ValidationError) as excinfo:
            schema.load([{"foo": "bar"}, {"foo": "baz"}], many=True)
        errors = excinfo.value.messages
        assert len(errors[0]["foo"]) == 1
        assert len(errors[1]["foo"]) == 1
        with pytest.raises(ValidationError) as excinfo:
            schema.load({"foo": "bar"})
        errors = excinfo.value.messages
        assert len(errors["foo"]) == 1

    def test_raises_error_with_list(self):
        def validator(val):
            raise ValidationError(["err1", "err2"])

        class MySchema(Schema):
            foo = fields.Raw(validate=validator)

        s = MySchema()
        errors = s.validate({"foo": 42})
        assert errors["foo"] == ["err1", "err2"]

    # https://github.com/marshmallow-code/marshmallow/issues/110
    def test_raises_error_with_dict(self):
        def validator(val):
            raise ValidationError({"code": "invalid_foo"})

        class MySchema(Schema):
            foo = fields.Raw(validate=validator)

        s = MySchema()
        errors = s.validate({"foo": 42})
        assert errors["foo"] == [{"code": "invalid_foo"}]

    def test_ignored_if_not_in_only(self):
        class MySchema(Schema):
            a = fields.Raw()
            b = fields.Raw()

            @validates("a")
            def validate_a(self, val, **kwargs):
                raise ValidationError({"code": "invalid_a"})

            @validates("b")
            def validate_b(self, val, **kwargs):
                raise ValidationError({"code": "invalid_b"})

        s = MySchema(only=("b",))
        errors = s.validate({"b": "data"})
        assert errors == {"b": {"code": "invalid_b"}}


def test_schema_repr():
    class MySchema(Schema):
        name = fields.String()

    ser = MySchema(many=True)
    rep = repr(ser)
    assert "MySchema" in rep
    assert "many=True" in rep


class TestNestedSchema:
    @pytest.fixture
    def user(self):
        return User(name="Monty", age=81)

    @pytest.fixture
    def blog(self, user):
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        return Blog(
            "Monty's blog",
            user=user,
            categories=["humor", "violence"],
            collaborators=[col1, col2],
        )

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/64
    def test_nested_many_with_missing_attribute(self, user):
        class SimpleBlogSchema(Schema):
            title = fields.Str()
            wat = fields.Nested(UserSchema, many=True)

        blog = Blog("Simple blog", user=user, collaborators=None)
        schema = SimpleBlogSchema()
        result = schema.dump(blog)
        assert "wat" not in result

    def test_nested_with_attribute_none(self):
        class InnerSchema(Schema):
            bar = fields.Raw()

        class MySchema(Schema):
            foo = fields.Nested(InnerSchema)

        class MySchema2(Schema):
            foo = fields.Nested(InnerSchema)

        s = MySchema()
        result = s.dump({"foo": None})
        assert result["foo"] is None

        s2 = MySchema2()
        result2 = s2.dump({"foo": None})
        assert result2["foo"] is None

    def test_nested_field_does_not_validate_required(self):
        class BlogRequiredSchema(Schema):
            user = fields.Nested(UserSchema, required=True)

        b = Blog("Authorless blog", user=None)
        BlogRequiredSchema().dump(b)

    def test_nested_none(self):
        class BlogDefaultSchema(Schema):
            user = fields.Nested(UserSchema, dump_default=0)

        b = Blog("Just the default blog", user=None)
        data = BlogDefaultSchema().dump(b)
        assert data["user"] is None

    def test_nested(self, user, blog):
        blog_serializer = BlogSchema()
        serialized_blog = blog_serializer.dump(blog)
        user_serializer = UserSchema()
        serialized_user = user_serializer.dump(user)
        assert serialized_blog["user"] == serialized_user

        with pytest.raises(ValidationError, match="email"):
            BlogSchema().load(
                {"title": "Monty's blog", "user": {"name": "Monty", "email": "foo"}}
            )

    def test_nested_many_fields(self, blog):
        serialized_blog = BlogSchema().dump(blog)
        expected = [UserSchema().dump(col) for col in blog.collaborators]
        assert serialized_blog["collaborators"] == expected

    def test_nested_only(self, blog):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        blog.collaborators = [col1, col2]
        serialized_blog = BlogOnlySchema().dump(blog)
        assert serialized_blog["collaborators"] == [{"id": col1.id}, {"id": col2.id}]

    def test_exclude(self, blog):
        serialized = BlogSchemaExclude().dump(blog)
        assert "uppername" not in serialized["user"]

    def test_list_field(self, blog):
        serialized = BlogSchema().dump(blog)
        assert serialized["categories"] == ["humor", "violence"]

    def test_nested_load_many(self):
        in_data = {
            "title": "Shine A Light",
            "collaborators": [
                {"name": "Mick", "email": "mick@stones.com"},
                {"name": "Keith", "email": "keith@stones.com"},
            ],
        }
        data = BlogSchema().load(in_data)
        collabs = data["collaborators"]
        assert len(collabs) == 2
        assert all(type(each) is User for each in collabs)
        assert collabs[0].name == in_data["collaborators"][0]["name"]

    def test_nested_errors(self):
        with pytest.raises(ValidationError) as excinfo:
            BlogSchema().load(
                {"title": "Monty's blog", "user": {"name": "Monty", "email": "foo"}}
            )
        errors = excinfo.value.messages
        assert "email" in errors["user"]
        assert len(errors["user"]["email"]) == 1
        assert "Not a valid email address." in errors["user"]["email"][0]
        # No problems with collaborators
        assert "collaborators" not in errors

    def test_nested_method_field(self, blog):
        data = BlogSchema().dump(blog)
        assert data["user"]["is_old"]
        assert data["collaborators"][0]["is_old"]

    def test_nested_function_field(self, blog, user):
        data = BlogSchema().dump(blog)
        assert data["user"]["lowername"] == user.name.lower()
        expected = blog.collaborators[0].name.lower()
        assert data["collaborators"][0]["lowername"] == expected

    def test_nested_fields_must_be_passed_a_serializer(self, blog):
        class BadNestedFieldSchema(BlogSchema):
            user = fields.Nested(fields.String)  # type: ignore[arg-type]

        with pytest.raises(ValueError):
            BadNestedFieldSchema().dump(blog)

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/188
    def test_invalid_type_passed_to_nested_field(self):
        class InnerSchema(Schema):
            foo = fields.Raw()

        class MySchema(Schema):
            inner = fields.Nested(InnerSchema, many=True)

        sch = MySchema()

        sch.load({"inner": [{"foo": 42}]})

        with pytest.raises(ValidationError) as excinfo:
            sch.load({"inner": "invalid"})
        errors = excinfo.value.messages
        assert "inner" in errors
        assert errors["inner"] == ["Invalid type."]

        class OuterSchema(Schema):
            inner = fields.Nested(InnerSchema)

        schema = OuterSchema()
        with pytest.raises(ValidationError) as excinfo:
            schema.load({"inner": 1})
        errors = excinfo.value.messages
        assert errors["inner"]["_schema"] == ["Invalid input type."]

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/298
    def test_all_errors_on_many_nested_field_with_validates_decorator(self):
        class Inner(Schema):
            req = fields.Raw(required=True)

        class Outer(Schema):
            inner = fields.Nested(Inner, many=True)

            @validates("inner")
            def validates_inner(self, data, **kwargs):
                raise ValidationError("not a chance")

        outer = Outer()
        with pytest.raises(ValidationError) as excinfo:
            outer.load({"inner": [{}]})
        errors = excinfo.value.messages
        assert "inner" in errors
        assert "_schema" in errors["inner"]

    @pytest.mark.parametrize("unknown", (None, RAISE, INCLUDE, EXCLUDE))
    def test_nested_unknown_validation(self, unknown):
        class ChildSchema(Schema):
            num = fields.Int()

        class ParentSchema(Schema):
            child = fields.Nested(ChildSchema, unknown=unknown)

        data = {"child": {"num": 1, "extra": 1}}
        if unknown is None or unknown == RAISE:
            with pytest.raises(ValidationError) as excinfo:
                ParentSchema().load(data)
            exc = excinfo.value
            assert exc.messages == {"child": {"extra": ["Unknown field."]}}
        else:
            output = {
                INCLUDE: {"child": {"num": 1, "extra": 1}},
                EXCLUDE: {"child": {"num": 1}},
            }[unknown]
            assert ParentSchema().load(data) == output


class TestPluckSchema:
    @pytest.mark.parametrize("user_schema", [UserSchema, UserSchema()])
    def test_pluck(self, user_schema, blog):
        class FlatBlogSchema(Schema):
            user = fields.Pluck(user_schema, "name")
            collaborators = fields.Pluck(user_schema, "name", many=True)

        s = FlatBlogSchema()
        data = s.dump(blog)
        assert data["user"] == blog.user.name
        for i, name in enumerate(data["collaborators"]):
            assert name == blog.collaborators[i].name

    def test_pluck_none(self, blog):
        class FlatBlogSchema(Schema):
            user = fields.Pluck(UserSchema, "name")
            collaborators = fields.Pluck(UserSchema, "name", many=True)

        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        blog = Blog(title="Unowned Blog", user=None, collaborators=[col1, col2])
        s = FlatBlogSchema()
        data = s.dump(blog)
        assert data["user"] == blog.user
        for i, name in enumerate(data["collaborators"]):
            assert name == blog.collaborators[i].name

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/800
    def test_pluck_with_data_key(self, blog):
        class UserSchema(Schema):
            name = fields.String(data_key="username")
            age = fields.Int()

        class FlatBlogSchema(Schema):
            user = fields.Pluck(UserSchema, "name")
            collaborators = fields.Pluck(UserSchema, "name", many=True)

        s = FlatBlogSchema()
        data = s.dump(blog)
        assert data["user"] == blog.user.name
        for i, name in enumerate(data["collaborators"]):
            assert name == blog.collaborators[i].name
        assert s.load(data) == {
            "user": {"name": "Monty"},
            "collaborators": [{"name": "Mick"}, {"name": "Keith"}],
        }


class TestSelfReference:
    @pytest.fixture
    def employer(self):
        return User(name="Joe", age=59)

    @pytest.fixture
    def user(self, employer):
        return User(name="Tom", employer=employer, age=28)

    def test_nesting_schema_by_passing_lambda(self, user, employer):
        class SelfReferencingSchema(Schema):
            name = fields.Str()
            age = fields.Int()
            employer = fields.Nested(
                lambda: SelfReferencingSchema(exclude=("employer",))
            )

        data = SelfReferencingSchema().dump(user)
        assert data["name"] == user.name
        assert data["employer"]["name"] == employer.name
        assert data["employer"]["age"] == employer.age

    def test_nesting_schema_by_passing_class_name(self, user, employer):
        class SelfReferencingSchema(Schema):
            name = fields.Str()
            age = fields.Int()
            employer = fields.Nested("SelfReferencingSchema", exclude=("employer",))

        data = SelfReferencingSchema().dump(user)
        assert data["name"] == user.name
        assert data["employer"]["name"] == employer.name
        assert data["employer"]["age"] == employer.age

    def test_nesting_within_itself_exclude(self, user, employer):
        class SelfSchema(Schema):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested(lambda: SelfSchema(exclude=("employer",)))

        data = SelfSchema().dump(user)
        assert data["name"] == user.name
        assert data["age"] == user.age
        assert data["employer"]["name"] == employer.name
        assert data["employer"]["age"] == employer.age

    def test_nested_self_with_only_param(self, user, employer):
        class SelfSchema(Schema):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested(lambda: SelfSchema(only=("name",)))

        data = SelfSchema().dump(user)
        assert data["employer"]["name"] == employer.name
        assert "age" not in data["employer"]

    def test_multiple_pluck_self_lambda(self, user):
        class MultipleSelfSchema(Schema):
            name = fields.String()
            emp = fields.Pluck(
                lambda: MultipleSelfSchema(), "name", attribute="employer"
            )
            rels = fields.Pluck(
                lambda: MultipleSelfSchema(), "name", many=True, attribute="relatives"
            )

        schema = MultipleSelfSchema()
        user.relatives = [User(name="Bar", age=12), User(name="Baz", age=34)]
        data = schema.dump(user)
        assert len(data["rels"]) == len(user.relatives)
        relative = data["rels"][0]
        assert relative == user.relatives[0].name

    def test_nested_self_many_lambda(self):
        class SelfManySchema(Schema):
            relatives = fields.Nested(lambda: SelfManySchema(), many=True)
            name = fields.String()
            age = fields.Integer()

        person = User(name="Foo")
        person.relatives = [User(name="Bar", age=12), User(name="Baz", age=34)]
        data = SelfManySchema().dump(person)
        assert data["name"] == person.name
        assert len(data["relatives"]) == len(person.relatives)
        assert data["relatives"][0]["name"] == person.relatives[0].name
        assert data["relatives"][0]["age"] == person.relatives[0].age

    def test_nested_self_list(self):
        class SelfListSchema(Schema):
            relatives = fields.List(fields.Nested(lambda: SelfListSchema()))
            name = fields.String()
            age = fields.Integer()

        person = User(name="Foo")
        person.relatives = [User(name="Bar", age=12), User(name="Baz", age=34)]
        data = SelfListSchema().dump(person)
        assert data["name"] == person.name
        assert len(data["relatives"]) == len(person.relatives)
        assert data["relatives"][0]["name"] == person.relatives[0].name
        assert data["relatives"][0]["age"] == person.relatives[0].age


class RequiredUserSchema(Schema):
    name = fields.Raw(required=True)


def test_serialization_with_required_field():
    user = User(name=None)
    RequiredUserSchema().dump(user)


def test_deserialization_with_required_field():
    with pytest.raises(ValidationError) as excinfo:
        RequiredUserSchema().load({})
    data, errors = excinfo.value.valid_data, excinfo.value.messages
    assert "name" in errors
    assert "Missing data for required field." in errors["name"]
    assert isinstance(data, dict)
    # field value should also not be in output data
    assert "name" not in data


def test_deserialization_with_required_field_and_custom_validator():
    def validator(val):
        if val.lower() not in {"red", "blue"}:
            raise ValidationError("Color must be red or blue")

    class ValidatingSchema(Schema):
        color = fields.String(
            required=True,
            validate=validator,
        )

    with pytest.raises(ValidationError) as excinfo:
        ValidatingSchema().load({"name": "foo"})
    errors = excinfo.value.messages
    assert errors
    assert "color" in errors
    assert "Missing data for required field." in errors["color"]

    with pytest.raises(ValidationError) as excinfo:
        ValidatingSchema().load({"color": "green"})
    errors = excinfo.value.messages
    assert "color" in errors
    assert "Color must be red or blue" in errors["color"]


def test_serializer_can_specify_nested_object_as_attribute(blog):
    class BlogUsernameSchema(Schema):
        author_name = fields.String(attribute="user.name")

    ser = BlogUsernameSchema()
    result = ser.dump(blog)
    assert result["author_name"] == blog.user.name


class TestFieldInheritance:
    def test_inherit_fields_from_schema_subclass(self):
        expected = {
            "field_a": fields.Integer(),
            "field_b": fields.Integer(),
        }

        class SerializerA(Schema):
            field_a = expected["field_a"]

        class SerializerB(SerializerA):
            field_b = expected["field_b"]

        assert SerializerB._declared_fields == expected

    def test_inherit_fields_from_non_schema_subclass(self):
        expected = {
            "field_a": fields.Integer(),
            "field_b": fields.Integer(),
        }

        class PlainBaseClass:
            field_a = expected["field_a"]

        class SerializerB1(Schema, PlainBaseClass):
            field_b = expected["field_b"]

        class SerializerB2(PlainBaseClass, Schema):
            field_b = expected["field_b"]

        assert SerializerB1._declared_fields == expected
        assert SerializerB2._declared_fields == expected

    def test_inheritance_follows_mro(self):
        expected = {
            "field_a": fields.String(),
            "field_b": fields.String(),
            "field_c": fields.String(),
            "field_d": fields.String(),
        }
        # Diamond inheritance graph
        # MRO: D -> B -> C -> A

        class SerializerA(Schema):
            field_a = expected["field_a"]

        class SerializerB(SerializerA):
            field_b = expected["field_b"]

        class SerializerC(SerializerA):
            field_c = expected["field_c"]

        class SerializerD(SerializerB, SerializerC):
            field_d = expected["field_d"]

        assert SerializerD._declared_fields == expected


def get_from_dict(schema, obj, key, default=None):
    return obj.get("_" + key, default)


class TestGetAttribute:
    def test_get_attribute_is_used(self):
        class UserDictSchema(Schema):
            name = fields.Str()
            email = fields.Email()

            def get_attribute(self, obj, attr, default):
                return get_from_dict(self, obj, attr, default)

        user_dict = {"_name": "joe", "_email": "joe@shmoe.com"}
        schema = UserDictSchema()
        result = schema.dump(user_dict)
        assert result["name"] == user_dict["_name"]
        assert result["email"] == user_dict["_email"]
        # can't serialize User object
        user = User(name="joe", email="joe@shmoe.com")
        with pytest.raises(AttributeError):
            schema.dump(user)

    def test_get_attribute_with_many(self):
        class UserDictSchema(Schema):
            name = fields.Str()
            email = fields.Email()

            def get_attribute(self, obj, attr, default):
                return get_from_dict(self, obj, attr, default)

        user_dicts = [
            {"_name": "joe", "_email": "joe@shmoe.com"},
            {"_name": "jane", "_email": "jane@shmane.com"},
        ]
        schema = UserDictSchema(many=True)
        results = schema.dump(user_dicts)
        for result, user_dict in zip(results, user_dicts):
            assert result["name"] == user_dict["_name"]
            assert result["email"] == user_dict["_email"]
        # can't serialize User object
        users = [
            User(name="joe", email="joe@shmoe.com"),
            User(name="jane", email="jane@shmane.com"),
        ]
        with pytest.raises(AttributeError):
            schema.dump(users)


class TestRequiredFields:
    class StringSchema(Schema):
        required_field = fields.Str(required=True)
        allow_none_field = fields.Str(allow_none=True)
        allow_none_required_field = fields.Str(required=True, allow_none=True)

    @pytest.fixture
    def string_schema(self):
        return self.StringSchema()

    @pytest.fixture
    def data(self):
        return dict(
            required_field="foo",
            allow_none_field="bar",
            allow_none_required_field="one",
        )

    def test_required_string_field_missing(self, string_schema, data):
        del data["required_field"]
        errors = string_schema.validate(data)
        assert errors["required_field"] == ["Missing data for required field."]

    def test_required_string_field_failure(self, string_schema, data):
        data["required_field"] = None
        errors = string_schema.validate(data)
        assert errors["required_field"] == ["Field may not be null."]

    def test_allow_none_param(self, string_schema, data):
        data["allow_none_field"] = None
        errors = string_schema.validate(data)
        assert errors == {}

        data["allow_none_required_field"] = None
        string_schema.validate(data)

        del data["allow_none_required_field"]
        errors = string_schema.validate(data)
        assert "allow_none_required_field" in errors

    def test_allow_none_custom_message(self, data):
        class MySchema(Schema):
            allow_none_field = fields.Raw(
                allow_none=False, error_messages={"null": "<custom>"}
            )

        schema = MySchema()
        errors = schema.validate({"allow_none_field": None})
        assert errors["allow_none_field"][0] == "<custom>"


class TestDefaults:
    class MySchema(Schema):
        int_no_default = fields.Int(allow_none=True)
        str_no_default = fields.Str(allow_none=True)
        list_no_default = fields.List(fields.Str, allow_none=True)
        nested_no_default = fields.Nested(UserSchema, many=True, allow_none=True)

        int_with_default = fields.Int(allow_none=True, dump_default=42)
        str_with_default = fields.Str(allow_none=True, dump_default="foo")

    @pytest.fixture
    def schema(self):
        return self.MySchema()

    @pytest.fixture
    def data(self):
        return dict(
            int_no_default=None,
            str_no_default=None,
            list_no_default=None,
            nested_no_default=None,
            int_with_default=None,
            str_with_default=None,
        )

    def test_missing_inputs_are_excluded_from_dump_output(self, schema, data):
        for key in [
            "int_no_default",
            "str_no_default",
            "list_no_default",
            "nested_no_default",
        ]:
            d = data.copy()
            del d[key]
            result = schema.dump(d)
            # the missing key is not in the serialized result
            assert key not in result
            # the rest of the keys are in the result
            assert all(k in result for k in d)

    def test_none_is_serialized_to_none(self, schema, data):
        errors = schema.validate(data)
        assert errors == {}
        result = schema.dump(data)
        for key in data:
            msg = f"result[{key!r}] should be None"
            assert result[key] is None, msg

    def test_default_and_value_missing(self, schema, data):
        del data["int_with_default"]
        del data["str_with_default"]
        result = schema.dump(data)
        assert result["int_with_default"] == 42
        assert result["str_with_default"] == "foo"

    def test_loading_none(self, schema, data):
        result = schema.load(data)
        for key in data:
            assert result[key] is None

    def test_missing_inputs_are_excluded_from_load_output(self, schema, data):
        for key in [
            "int_no_default",
            "str_no_default",
            "list_no_default",
            "nested_no_default",
        ]:
            d = data.copy()
            del d[key]
            result = schema.load(d)
            # the missing key is not in the deserialized result
            assert key not in result
            # the rest of the keys are in the result
            assert all(k in result for k in d)


class TestLoadOnly:
    class MySchema(Schema):
        class Meta:
            load_only = ("str_load_only",)
            dump_only = ("str_dump_only",)

        str_dump_only = fields.String()
        str_load_only = fields.String()
        str_regular = fields.String()

    @pytest.fixture
    def schema(self):
        return self.MySchema()

    @pytest.fixture
    def data(self):
        return dict(
            str_dump_only="Dump Only",
            str_load_only="Load Only",
            str_regular="Regular String",
        )

    def test_load_only(self, schema, data):
        result = schema.dump(data)
        assert "str_load_only" not in result
        assert "str_dump_only" in result
        assert "str_regular" in result

    def test_dump_only(self, schema, data):
        result = schema.load(data, unknown=EXCLUDE)
        assert "str_dump_only" not in result
        assert "str_load_only" in result
        assert "str_regular" in result

    # regression test for https://github.com/marshmallow-code/marshmallow/pull/765
    def test_url_field_requre_tld_false(self):
        class NoTldTestSchema(Schema):
            url = fields.Url(require_tld=False, schemes=["marshmallow"])

        schema = NoTldTestSchema()
        data_with_no_top_level_domain = {"url": "marshmallow://app/discounts"}
        result = schema.load(data_with_no_top_level_domain)
        assert result == data_with_no_top_level_domain


class TestFromDict:
    def test_generates_schema(self):
        MySchema = Schema.from_dict({"foo": fields.Str()})
        assert issubclass(MySchema, Schema)

    def test_name(self):
        MySchema = Schema.from_dict({"foo": fields.Str()})
        assert "GeneratedSchema" in repr(MySchema)
        SchemaWithName = Schema.from_dict(
            {"foo": fields.Int()}, name="MyGeneratedSchema"
        )
        assert "MyGeneratedSchema" in repr(SchemaWithName)

    def test_generated_schemas_are_not_registered(self):
        n_registry_entries = len(class_registry._registry)
        Schema.from_dict({"foo": fields.Str()})
        Schema.from_dict({"bar": fields.Str()}, name="MyGeneratedSchema")
        assert len(class_registry._registry) == n_registry_entries
        with pytest.raises(RegistryError):
            class_registry.get_class("GeneratedSchema")
        with pytest.raises(RegistryError):
            class_registry.get_class("MyGeneratedSchema")

    def test_meta_options_are_applied(self):
        class OrderedSchema(Schema):
            class Meta:
                load_only = ("bar",)

        OSchema = OrderedSchema.from_dict({"foo": fields.Int(), "bar": fields.Int()})
        dumped = OSchema().dump({"foo": 42, "bar": 24})
        assert "bar" not in dumped


def test_class_registry_returns_schema_type():
    class DefinitelyUniqueSchema(Schema):
        """
        Just a schema
        """

    SchemaClass = class_registry.get_class(DefinitelyUniqueSchema.__name__)
    assert SchemaClass is DefinitelyUniqueSchema


@pytest.mark.parametrize("dict_cls", (dict, OrderedDict))
def test_set_dict_class(dict_cls):
    """Demonstrate how to specify dict_class as class attribute"""

    class MySchema(Schema):
        dict_class = dict_cls
        foo = fields.String()

    result = MySchema().dump({"foo": "bar"})
    assert result == {"foo": "bar"}
    assert isinstance(result, dict_cls)
