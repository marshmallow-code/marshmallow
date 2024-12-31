import datetime as dt

from marshmallow import EXCLUDE, Schema, fields


class UserSchema(Schema):
    name = fields.String(allow_none=True)
    email = fields.Email(allow_none=True)
    age = fields.Integer()
    created = fields.DateTime()
    id = fields.Integer(allow_none=True)
    homepage = fields.Url()
    birthdate = fields.Date()


class ProfileSchema(Schema):
    user = fields.Nested(UserSchema)


class TestFieldOrdering:
    def test_declared_field_order_is_maintained_on_dump(self, user):
        ser = UserSchema()
        data = ser.dump(user)
        keys = list(data)
        assert keys == [
            "name",
            "email",
            "age",
            "created",
            "id",
            "homepage",
            "birthdate",
        ]

    def test_declared_field_order_is_maintained_on_load(self, serialized_user):
        schema = UserSchema(unknown=EXCLUDE)
        data = schema.load(serialized_user)
        keys = list(data)
        assert keys == [
            "name",
            "email",
            "age",
            "created",
            "id",
            "homepage",
            "birthdate",
        ]

    def test_nested_field_order_with_only_arg_is_maintained_on_dump(self, user):
        schema = ProfileSchema()
        data = schema.dump({"user": user})
        user_data = data["user"]
        keys = list(user_data)
        assert keys == [
            "name",
            "email",
            "age",
            "created",
            "id",
            "homepage",
            "birthdate",
        ]

    def test_nested_field_order_with_only_arg_is_maintained_on_load(self):
        schema = ProfileSchema()
        data = schema.load(
            {
                "user": {
                    "name": "Foo",
                    "email": "Foo@bar.com",
                    "age": 42,
                    "created": dt.datetime.now().isoformat(),
                    "id": 123,
                    "homepage": "http://foo.com",
                    "birthdate": dt.datetime.now().date().isoformat(),
                }
            }
        )
        user_data = data["user"]
        keys = list(user_data)
        assert keys == [
            "name",
            "email",
            "age",
            "created",
            "id",
            "homepage",
            "birthdate",
        ]

    def test_nested_field_order_with_exclude_arg_is_maintained(self, user):
        class HasNestedExclude(Schema):
            user = fields.Nested(UserSchema, exclude=("birthdate",))

        ser = HasNestedExclude()
        data = ser.dump({"user": user})
        user_data = data["user"]
        keys = list(user_data)
        assert keys == ["name", "email", "age", "created", "id", "homepage"]


class TestIncludeOption:
    class AddFieldsSchema(Schema):
        name = fields.Str()

        class Meta:
            include = {"from": fields.Str()}

    def test_fields_are_added(self):
        s = self.AddFieldsSchema()
        in_data = {"name": "Steve", "from": "Oskosh"}
        result = s.load({"name": "Steve", "from": "Oskosh"})
        assert result == in_data

    def test_included_fields_ordered_after_declared_fields(self):
        class AddFieldsOrdered(Schema):
            name = fields.Str()
            email = fields.Str()

            class Meta:
                include = {
                    "from": fields.Str(),
                    "in": fields.Str(),
                    "@at": fields.Str(),
                }

        s = AddFieldsOrdered()
        in_data = {
            "name": "Steve",
            "from": "Oskosh",
            "email": "steve@steve.steve",
            "in": "VA",
            "@at": "Charlottesville",
        }
        # declared fields, then "included" fields
        expected_fields = ["name", "email", "from", "in", "@at"]
        assert list(AddFieldsOrdered._declared_fields.keys()) == expected_fields

        result = s.load(in_data)
        assert list(result.keys()) == expected_fields

    def test_added_fields_are_inherited(self):
        class AddFieldsChild(self.AddFieldsSchema):
            email = fields.Str()

        s = AddFieldsChild()
        assert "email" in s._declared_fields.keys()
        assert "from" in s._declared_fields.keys()
        assert isinstance(s._declared_fields["from"], fields.Str)


class TestManyOption:
    class ManySchema(Schema):
        foo = fields.Str()

        class Meta:
            many = True

    def test_many_by_default(self):
        test = self.ManySchema()
        assert test.load([{"foo": "bar"}]) == [{"foo": "bar"}]

    def test_explicit_single(self):
        test = self.ManySchema(many=False)
        assert test.load({"foo": "bar"}) == {"foo": "bar"}
