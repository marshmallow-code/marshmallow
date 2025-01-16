import typing

import pytest

from marshmallow import (
    Schema,
    fields,
    post_dump,
    post_load,
    pre_dump,
    pre_load,
    validates,
    validates_schema,
)
from marshmallow.exceptions import ValidationError
from marshmallow.experimental.context import Context
from tests.base import Blog, User


class UserContextSchema(Schema):
    is_owner = fields.Method("get_is_owner")
    is_collab = fields.Function(
        lambda user: user in Context[dict[str, typing.Any]].get()["blog"]
    )

    def get_is_owner(self, user):
        return Context.get()["blog"].user.name == user.name


class TestContext:
    def test_context_load_dump(self):
        class ContextField(fields.Integer):
            def _serialize(self, value, attr, obj, **kwargs):
                if (context := Context[dict].get(None)) is not None:
                    value *= context.get("factor", 1)
                return super()._serialize(value, attr, obj, **kwargs)

            def _deserialize(self, value, attr, data, **kwargs):
                val = super()._deserialize(value, attr, data, **kwargs)
                if (context := Context[dict].get(None)) is not None:
                    val *= context.get("factor", 1)
                return val

        class ContextSchema(Schema):
            ctx_fld = ContextField()

        ctx_schema = ContextSchema()

        assert ctx_schema.load({"ctx_fld": 1}) == {"ctx_fld": 1}
        assert ctx_schema.dump({"ctx_fld": 1}) == {"ctx_fld": 1}
        with Context({"factor": 2}):
            assert ctx_schema.load({"ctx_fld": 1}) == {"ctx_fld": 2}
            assert ctx_schema.dump({"ctx_fld": 1}) == {"ctx_fld": 2}

    def test_context_method(self):
        owner = User("Joe")
        blog = Blog(title="Joe Blog", user=owner)
        serializer = UserContextSchema()
        with Context({"blog": blog}):
            data = serializer.dump(owner)
            assert data["is_owner"] is True
            nonowner = User("Fred")
            data = serializer.dump(nonowner)
            assert data["is_owner"] is False

    def test_context_function(self):
        owner = User("Fred")
        blog = Blog("Killer Queen", user=owner)
        collab = User("Brian")
        blog.collaborators.append(collab)
        with Context({"blog": blog}):
            serializer = UserContextSchema()
            data = serializer.dump(collab)
            assert data["is_collab"] is True
            noncollab = User("Foo")
            data = serializer.dump(noncollab)
            assert data["is_collab"] is False

    def test_function_field_handles_bound_serializer(self):
        class SerializeA:
            def __call__(self, value):
                return "value"

        serialize = SerializeA()

        # only has a function field
        class UserFunctionContextSchema(Schema):
            is_collab = fields.Function(serialize)

        owner = User("Joe")
        serializer = UserFunctionContextSchema()
        data = serializer.dump(owner)
        assert data["is_collab"] == "value"

    def test_nested_fields_inherit_context(self):
        class InnerSchema(Schema):
            likes_bikes = fields.Function(lambda obj: "bikes" in Context.get()["info"])

        class CSchema(Schema):
            inner = fields.Nested(InnerSchema)

        ser = CSchema()
        with Context[dict]({"info": "i like bikes"}):
            obj: dict[str, dict] = {"inner": {}}
            result = ser.dump(obj)
            assert result["inner"]["likes_bikes"] is True

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/820
    def test_nested_list_fields_inherit_context(self):
        class InnerSchema(Schema):
            foo = fields.Raw()

            @validates("foo")
            def validate_foo(self, value):
                if "foo_context" not in Context[dict].get():
                    raise ValidationError("Missing context")

        class OuterSchema(Schema):
            bars = fields.List(fields.Nested(InnerSchema()))

        inner = InnerSchema()
        with Context({"foo_context": "foo"}):
            assert inner.load({"foo": 42})

        outer = OuterSchema()
        with Context({"foo_context": "foo"}):
            assert outer.load({"bars": [{"foo": 42}]})

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/820
    def test_nested_dict_fields_inherit_context(self):
        class InnerSchema(Schema):
            foo = fields.Raw()

            @validates("foo")
            def validate_foo(self, value):
                if "foo_context" not in Context[dict].get():
                    raise ValidationError("Missing context")

        class OuterSchema(Schema):
            bars = fields.Dict(values=fields.Nested(InnerSchema()))

        inner = InnerSchema()
        with Context({"foo_context": "foo"}):
            assert inner.load({"foo": 42})

        outer = OuterSchema()
        with Context({"foo_context": "foo"}):
            assert outer.load({"bars": {"test": {"foo": 42}}})

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/1404
    def test_nested_field_with_unpicklable_object_in_context(self):
        class Unpicklable:
            def __deepcopy__(self, _):
                raise NotImplementedError

        class InnerSchema(Schema):
            foo = fields.Raw()

        class OuterSchema(Schema):
            inner = fields.Nested(InnerSchema())

        outer = OuterSchema()
        obj = {"inner": {"foo": 42}}
        with Context({"unp": Unpicklable()}):
            assert outer.dump(obj)

    def test_function_field_passed_serialize_with_context(self, user):
        class Parent(Schema):
            pass

        field = fields.Function(
            serialize=lambda obj: obj.name.upper() + Context.get()["key"]
        )
        field.parent = Parent()
        with Context({"key": "BAR"}):
            assert field.serialize("key", user) == "MONTYBAR"

    def test_function_field_deserialization_with_context(self):
        class Parent(Schema):
            pass

        field = fields.Function(
            lambda x: None,
            deserialize=lambda val: val.upper() + Context.get()["key"],
        )
        field.parent = Parent()
        with Context({"key": "BAR"}):
            assert field.deserialize("foo") == "FOOBAR"

    def test_decorated_processors_with_context(self):
        NumDictContext = Context[dict[int, int]]

        class MySchema(Schema):
            f_1 = fields.Integer()
            f_2 = fields.Integer()
            f_3 = fields.Integer()
            f_4 = fields.Integer()

            @pre_dump
            def multiply_f_1(self, item, **kwargs):
                item["f_1"] *= NumDictContext.get()[1]
                return item

            @pre_load
            def multiply_f_2(self, data, **kwargs):
                data["f_2"] *= NumDictContext.get()[2]
                return data

            @post_dump
            def multiply_f_3(self, item, **kwargs):
                item["f_3"] *= NumDictContext.get()[3]
                return item

            @post_load
            def multiply_f_4(self, data, **kwargs):
                data["f_4"] *= NumDictContext.get()[4]
                return data

        schema = MySchema()

        with NumDictContext({1: 2, 2: 3, 3: 4, 4: 5}):
            assert schema.dump({"f_1": 1, "f_2": 1, "f_3": 1, "f_4": 1}) == {
                "f_1": 2,
                "f_2": 1,
                "f_3": 4,
                "f_4": 1,
            }
            assert schema.load({"f_1": 1, "f_2": 1, "f_3": 1, "f_4": 1}) == {
                "f_1": 1,
                "f_2": 3,
                "f_3": 1,
                "f_4": 5,
            }

    def test_validates_schema_with_context(self):
        class MySchema(Schema):
            f_1 = fields.Integer()
            f_2 = fields.Integer()

            @validates_schema
            def validate_schema(self, data, **kwargs):
                if data["f_2"] != data["f_1"] * Context.get():
                    raise ValidationError("Fail")

        schema = MySchema()

        with Context(2):
            schema.load({"f_1": 1, "f_2": 2})
            with pytest.raises(ValidationError) as excinfo:
                schema.load({"f_1": 1, "f_2": 3})
            assert excinfo.value.messages["_schema"] == ["Fail"]
