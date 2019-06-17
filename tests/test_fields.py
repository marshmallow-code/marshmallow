import pytest

from marshmallow import (
    fields,
    Schema,
    ValidationError,
    EXCLUDE,
    INCLUDE,
    RAISE,
    missing,
)
from marshmallow.exceptions import StringNotCollectionError

from tests.base import ALL_FIELDS


@pytest.mark.parametrize(
    ("alias", "field"),
    [
        (fields.Int, fields.Integer),
        (fields.Str, fields.String),
        (fields.Bool, fields.Boolean),
        (fields.URL, fields.Url),
    ],
)
def test_field_aliases(alias, field):
    assert alias is field


class TestField:
    def test_repr(self):
        default = "œ∑´"
        field = fields.Field(default=default, attribute=None)
        assert repr(field) == (
            "<fields.Field(default={0!r}, attribute=None, "
            "validate=None, required=False, "
            "load_only=False, dump_only=False, "
            "missing={missing}, allow_none=False, "
            "error_messages={error_messages})>".format(
                default, missing=missing, error_messages=field.error_messages
            )
        )
        int_field = fields.Integer(validate=lambda x: True)
        assert "<fields.Integer" in repr(int_field)

    def test_error_raised_if_uncallable_validator_passed(self):
        with pytest.raises(ValueError, match="must be a callable"):
            fields.Field(validate="notcallable")

    def test_error_raised_if_missing_is_set_on_required_field(self):
        with pytest.raises(
            ValueError, match="'missing' must not be set for required fields"
        ):
            fields.Field(required=True, missing=42)

    def test_custom_field_receives_attr_and_obj(self):
        class MyField(fields.Field):
            def _deserialize(self, val, attr, data, **kwargs):
                assert attr == "name"
                assert data["foo"] == 42
                return val

        class MySchema(Schema):
            name = MyField()

        result = MySchema(unknown=EXCLUDE).load({"name": "Monty", "foo": 42})
        assert result == {"name": "Monty"}

    def test_custom_field_receives_data_key_if_set(self):
        class MyField(fields.Field):
            def _deserialize(self, val, attr, data, **kwargs):
                assert attr == "name"
                assert data["foo"] == 42
                return val

        class MySchema(Schema):
            Name = MyField(data_key="name")

        result = MySchema(unknown=EXCLUDE).load({"name": "Monty", "foo": 42})
        assert result == {"Name": "Monty"}

    def test_custom_field_follows_data_key_if_set(self):
        class MyField(fields.Field):
            def _serialize(self, val, attr, data):
                assert attr == "name"
                assert data["foo"] == 42
                return val

        class MySchema(Schema):
            name = MyField(data_key="_NaMe")

        result = MySchema().dump({"name": "Monty", "foo": 42})
        assert result == {"_NaMe": "Monty"}

    def test_number_fields_prohbits_boolean(self):
        strict_field = fields.Float()
        with pytest.raises(ValidationError) as excinfo:
            strict_field.serialize("value", {"value": False})
        assert excinfo.value.args[0] == "Not a valid number."
        with pytest.raises(ValidationError) as excinfo:
            strict_field.serialize("value", {"value": True})
        assert excinfo.value.args[0] == "Not a valid number."


class TestParentAndName:
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.List(fields.Str())
        baz = fields.Tuple([fields.Str(), fields.Int()])

    @pytest.fixture()
    def schema(self):
        return self.MySchema()

    def test_simple_field_parent_and_name(self, schema):
        assert schema.fields["foo"].parent == schema
        assert schema.fields["foo"].name == "foo"
        assert schema.fields["bar"].parent == schema
        assert schema.fields["bar"].name == "bar"

    # https://github.com/marshmallow-code/marshmallow/pull/572#issuecomment-275800288
    def test_unbound_field_root_returns_none(self):
        field = fields.Str()
        assert field.root is None

        inner_field = fields.Nested(self.MySchema())
        outer_field = fields.List(inner_field)

        assert outer_field.root is None
        assert inner_field.root is None

    def test_list_field_inner_parent_and_name(self, schema):
        assert schema.fields["bar"].inner.parent == schema.fields["bar"]
        assert schema.fields["bar"].inner.name == "bar"

    def test_tuple_field_inner_parent_and_name(self, schema):
        for field in schema.fields["baz"].tuple_fields:
            assert field.parent == schema.fields["baz"]
            assert field.name == "baz"

    def test_simple_field_root(self, schema):
        assert schema.fields["foo"].root == schema
        assert schema.fields["bar"].root == schema

    def test_list_field_inner_root(self, schema):
        assert schema.fields["bar"].inner.root == schema

    def test_tuple_field_inner_root(self, schema):
        for field in schema.fields["baz"].tuple_fields:
            assert field.root == schema

    def test_list_root_inheritance(self, schema):
        class OtherSchema(TestParentAndName.MySchema):
            pass

        schema2 = OtherSchema()
        assert schema.fields["bar"].inner.root == schema
        assert schema2.fields["bar"].inner.root == schema2

    def test_dict_root_inheritance(self):
        class MySchema(Schema):
            foo = fields.Dict(keys=fields.Str(), values=fields.Int())

        class OtherSchema(MySchema):
            pass

        schema = MySchema()
        schema2 = OtherSchema()
        assert schema.fields["foo"].key_field.root == schema
        assert schema.fields["foo"].value_field.root == schema
        assert schema2.fields["foo"].key_field.root == schema2
        assert schema2.fields["foo"].value_field.root == schema2


class TestMetadata:
    @pytest.mark.parametrize("FieldClass", ALL_FIELDS)
    def test_extra_metadata_may_be_added_to_field(self, FieldClass):  # noqa
        field = FieldClass(description="Just a normal field.")
        assert field.metadata["description"] == "Just a normal field."
        field = FieldClass(
            required=True,
            default=None,
            validate=lambda v: True,
            description="foo",
            widget="select",
        )
        assert field.metadata == {"description": "foo", "widget": "select"}


class TestErrorMessages:
    class MyField(fields.Field):
        default_error_messages = {"custom": "Custom error message."}

    def test_default_error_messages_get_merged_with_parent_error_messages_cstm_msg(
        self
    ):
        field = self.MyField()
        assert field.error_messages["custom"] == "Custom error message."
        assert "required" in field.error_messages

    def test_default_error_messages_get_merged_with_parent_error_messages(self):
        field = self.MyField(error_messages={"passed": "Passed error message"})
        assert field.error_messages["passed"] == "Passed error message"

    def test_fail(self):
        field = self.MyField()

        with pytest.raises(ValidationError) as excinfo:
            field.fail("required")
        assert excinfo.value.args[0] == "Missing data for required field."

        with pytest.raises(ValidationError) as excinfo:
            field.fail("null")
        assert excinfo.value.args[0] == "Field may not be null."

        with pytest.raises(ValidationError) as excinfo:
            field.fail("custom")
        assert excinfo.value.args[0] == "Custom error message."

        with pytest.raises(ValidationError) as excinfo:
            field.fail("validator_failed")
        assert excinfo.value.args[0] == "Invalid value."

        with pytest.raises(AssertionError) as excinfo:
            field.fail("doesntexist")

        assert "doesntexist" in excinfo.value.args[0]
        assert "MyField" in excinfo.value.args[0]


class TestNestedField:
    @pytest.mark.parametrize("param", ("only", "exclude"))
    def test_nested_only_and_exclude_as_string(self, param):
        with pytest.raises(StringNotCollectionError):
            fields.Nested(Schema, **{param: "foo"})

    @pytest.mark.parametrize("schema_unknown", (EXCLUDE, INCLUDE, RAISE))
    @pytest.mark.parametrize("field_unknown", (None, EXCLUDE, INCLUDE, RAISE))
    def test_nested_unknown_override(self, schema_unknown, field_unknown):
        class NestedSchema(Schema):
            class Meta:
                unknown = schema_unknown

        class MySchema(Schema):
            nested = fields.Nested(NestedSchema, unknown=field_unknown)

        if field_unknown == EXCLUDE or (
            schema_unknown == EXCLUDE and not field_unknown
        ):
            assert MySchema().load({"nested": {"x": 1}}) == {"nested": {}}
        elif field_unknown == INCLUDE or (
            schema_unknown == INCLUDE and not field_unknown
        ):
            assert MySchema().load({"nested": {"x": 1}}) == {"nested": {"x": 1}}
        elif field_unknown == RAISE or (schema_unknown == RAISE and not field_unknown):
            with pytest.raises(ValidationError):
                MySchema().load({"nested": {"x": 1}})


class TestListNested:
    @pytest.mark.parametrize("param", ("only", "exclude", "dump_only", "load_only"))
    def test_list_nested_only_exclude_dump_only_load_only_propagated_to_nested(
        self, param
    ):
        class Child(Schema):
            name = fields.String()
            age = fields.Integer()

        class Family(Schema):
            children = fields.List(fields.Nested(Child))

        schema = Family(**{param: ["children.name"]})
        assert getattr(schema.fields["children"].inner.schema, param) == {"name"}

    @pytest.mark.parametrize(
        ("param", "expected"),
        (("only", {"name"}), ("exclude", {"name", "surname", "age"})),
    )
    def test_list_nested_only_and_exclude_merged_with_nested(self, param, expected):
        class Child(Schema):
            name = fields.String()
            surname = fields.String()
            age = fields.Integer()

        class Family(Schema):
            children = fields.List(fields.Nested(Child, **{param: ("name", "surname")}))

        schema = Family(**{param: ["children.name", "children.age"]})
        assert getattr(schema.fields["children"].inner, param) == expected

    def test_list_nested_partial_propagated_to_nested(self):
        class Child(Schema):
            name = fields.String(required=True)
            age = fields.Integer(required=True)

        class Family(Schema):
            children = fields.List(fields.Nested(Child))

        payload = {"children": [{"name": "Lucette"}]}

        for val in (True, ("children.age",)):
            result = Family(partial=val).load(payload)
            assert result["children"][0]["name"] == "Lucette"
            result = Family().load(payload, partial=val)
            assert result["children"][0]["name"] == "Lucette"

        for val in (False, ("children.name",)):
            with pytest.raises(ValidationError) as excinfo:
                result = Family(partial=val).load(payload)
            assert excinfo.value.args[0] == {
                "children": {0: {"age": ["Missing data for required field."]}}
            }
            with pytest.raises(ValidationError) as excinfo:
                result = Family().load(payload, partial=val)
            assert excinfo.value.args[0] == {
                "children": {0: {"age": ["Missing data for required field."]}}
            }


class TestTupleNested:
    @pytest.mark.parametrize("param", ("dump_only", "load_only"))
    def test_tuple_nested_only_exclude_dump_only_load_only_propagated_to_nested(
        self, param
    ):
        class Child(Schema):
            name = fields.String()
            age = fields.Integer()

        class Family(Schema):
            children = fields.Tuple((fields.Nested(Child), fields.Nested(Child)))

        schema = Family(**{param: ["children.name"]})
        assert getattr(schema.fields["children"].tuple_fields[0].schema, param) == {
            "name"
        }
        assert getattr(schema.fields["children"].tuple_fields[1].schema, param) == {
            "name"
        }

    def test_tuple_nested_partial_propagated_to_nested(self):
        class Child(Schema):
            name = fields.String(required=True)
            age = fields.Integer(required=True)

        class Family(Schema):
            children = fields.Tuple((fields.Nested(Child),))

        payload = {"children": [{"name": "Lucette"}]}

        for val in (True, ("children.age",)):
            result = Family(partial=val).load(payload)
            assert result["children"][0]["name"] == "Lucette"
            result = Family().load(payload, partial=val)
            assert result["children"][0]["name"] == "Lucette"

        for val in (False, ("children.name",)):
            with pytest.raises(ValidationError) as excinfo:
                result = Family(partial=val).load(payload)
            assert excinfo.value.args[0] == {
                "children": {0: {"age": ["Missing data for required field."]}}
            }
            with pytest.raises(ValidationError) as excinfo:
                result = Family().load(payload, partial=val)
            assert excinfo.value.args[0] == {
                "children": {0: {"age": ["Missing data for required field."]}}
            }


class TestDictNested:
    @pytest.mark.parametrize("param", ("only", "exclude", "dump_only", "load_only"))
    def test_dict_nested_only_exclude_dump_only_load_only_propagated_to_nested(
        self, param
    ):
        class Child(Schema):
            name = fields.String()
            age = fields.Integer()

        class Family(Schema):
            children = fields.Dict(values=fields.Nested(Child))

        schema = Family(**{param: ["children.name"]})
        assert getattr(schema.fields["children"].value_field.schema, param) == {"name"}

    @pytest.mark.parametrize(
        ("param", "expected"),
        (("only", {"name"}), ("exclude", {"name", "surname", "age"})),
    )
    def test_dict_nested_only_and_exclude_merged_with_nested(self, param, expected):
        class Child(Schema):
            name = fields.String()
            surname = fields.String()
            age = fields.Integer()

        class Family(Schema):
            children = fields.Dict(
                values=fields.Nested(Child, **{param: ("name", "surname")})
            )

        schema = Family(**{param: ["children.name", "children.age"]})
        assert getattr(schema.fields["children"].value_field, param) == expected

    def test_dict_nested_partial_propagated_to_nested(self):
        class Child(Schema):
            name = fields.String(required=True)
            age = fields.Integer(required=True)

        class Family(Schema):
            children = fields.Dict(values=fields.Nested(Child))

        payload = {"children": {"daughter": {"name": "Lucette"}}}

        for val in (True, ("children.age",)):
            result = Family(partial=val).load(payload)
            assert result["children"]["daughter"]["name"] == "Lucette"
            result = Family().load(payload, partial=val)
            assert result["children"]["daughter"]["name"] == "Lucette"

        for val in (False, ("children.name",)):
            with pytest.raises(ValidationError) as excinfo:
                result = Family(partial=val).load(payload)
            assert excinfo.value.args[0] == {
                "children": {
                    "daughter": {"value": {"age": ["Missing data for required field."]}}
                }
            }
            with pytest.raises(ValidationError) as excinfo:
                result = Family().load(payload, partial=val)
            assert excinfo.value.args[0] == {
                "children": {
                    "daughter": {"value": {"age": ["Missing data for required field."]}}
                }
            }
