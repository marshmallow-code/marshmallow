import typing

from marshmallow import Schema, fields, validates
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
                if (context := Context.get(None)) is not None:
                    value *= context.get("factor", 1)
                return super()._serialize(value, attr, obj, **kwargs)

            def _deserialize(self, value, attr, data, **kwargs):
                val = super()._deserialize(value, attr, data, **kwargs)
                if (context := Context.get(None)) is not None:
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
        with Context({"info": "i like bikes"}):
            obj = {"inner": {}}
            result = ser.dump(obj)
            assert result["inner"]["likes_bikes"] is True

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/820
    def test_nested_list_fields_inherit_context(self):
        class InnerSchema(Schema):
            foo = fields.Field()

            @validates("foo")
            def validate_foo(self, value):
                if "foo_context" not in Context.get():
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
            foo = fields.Field()

            @validates("foo")
            def validate_foo(self, value):
                if "foo_context" not in Context.get():
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
            foo = fields.Field()

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
