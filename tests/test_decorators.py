import pytest

from marshmallow import (
    Schema,
    fields,
    pre_dump,
    post_dump,
    pre_load,
    post_load,
    validates,
    validates_schema,
    ValidationError,
    EXCLUDE,
    INCLUDE,
    RAISE,
)


@pytest.mark.parametrize("partial_val", (True, False))
def test_decorated_processors(partial_val):
    class ExampleSchema(Schema):
        """Includes different ways to invoke decorators and set up methods"""

        TAG = "TAG"

        value = fields.Integer(as_string=True)

        # Implicit default raw, pre dump, static method.
        @pre_dump
        def increment_value(self, item, **kwargs):
            assert "many" in kwargs
            item["value"] += 1
            return item

        # Implicit default raw, post dump, class method.
        @post_dump
        def add_tag(self, item, **kwargs):
            assert "many" in kwargs
            item["value"] = self.TAG + item["value"]
            return item

        # Explicitly raw, post dump, instance method.
        @post_dump(pass_many=True)
        def add_envelope(self, data, many, **kwargs):
            key = self.get_envelope_key(many)
            return {key: data}

        # Explicitly raw, pre load, instance method.
        @pre_load(pass_many=True)
        def remove_envelope(self, data, many, partial, **kwargs):
            assert partial is partial_val
            key = self.get_envelope_key(many)
            return data[key]

        @staticmethod
        def get_envelope_key(many):
            return "data" if many else "datum"

        # Explicitly not raw, pre load, instance method.
        @pre_load(pass_many=False)
        def remove_tag(self, item, partial, **kwargs):
            assert partial is partial_val
            assert "many" in kwargs
            item["value"] = item["value"][len(self.TAG) :]
            return item

        # Explicit default raw, post load, instance method.
        @post_load()
        def decrement_value(self, item, partial, **kwargs):
            assert partial is partial_val
            assert "many" in kwargs
            item["value"] -= 1
            return item

    schema = ExampleSchema(partial=partial_val)

    # Need to re-create these because the processors will modify in place.
    make_item = lambda: {"value": 3}
    make_items = lambda: [make_item(), {"value": 5}]

    item_dumped = schema.dump(make_item())
    assert item_dumped == {"datum": {"value": "TAG4"}}
    item_loaded = schema.load(item_dumped)
    assert item_loaded == make_item()

    items_dumped = schema.dump(make_items(), many=True)
    assert items_dumped == {"data": [{"value": "TAG4"}, {"value": "TAG6"}]}
    items_loaded = schema.load(items_dumped, many=True)
    assert items_loaded == make_items()


#  Regression test for https://github.com/marshmallow-code/marshmallow/issues/347
@pytest.mark.parametrize("unknown", (EXCLUDE, INCLUDE, RAISE))
def test_decorated_processor_returning_none(unknown):
    class PostSchema(Schema):
        value = fields.Integer()

        @post_load
        def load_none(self, item, **kwargs):
            return None

        @post_dump
        def dump_none(self, item, **kwargs):
            return None

    class PreSchema(Schema):
        value = fields.Integer()

        @pre_load
        def load_none(self, item, **kwargs):
            return None

        @pre_dump
        def dump_none(self, item, **kwargs):
            return None

    schema = PostSchema(unknown=unknown)
    assert schema.dump({"value": 3}) is None
    assert schema.load({"value": 3}) is None
    schema = PreSchema(unknown=unknown)
    assert schema.dump({"value": 3}) == {}
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"value": 3})
    assert excinfo.value.messages == {"_schema": ["Invalid input type."]}


class TestPassOriginal:
    def test_pass_original_single(self):
        class MySchema(Schema):
            foo = fields.Field()

            @post_load(pass_original=True)
            def post_load(self, data, original_data, **kwargs):
                ret = data.copy()
                ret["_post_load"] = original_data["sentinel"]
                return ret

            @post_dump(pass_original=True)
            def post_dump(self, data, obj, **kwargs):
                ret = data.copy()
                ret["_post_dump"] = obj["sentinel"]
                return ret

        schema = MySchema(unknown=EXCLUDE)
        datum = {"foo": 42, "sentinel": 24}
        item_loaded = schema.load(datum)
        assert item_loaded["foo"] == 42
        assert item_loaded["_post_load"] == 24

        item_dumped = schema.dump(datum)

        assert item_dumped["foo"] == 42
        assert item_dumped["_post_dump"] == 24

    def test_pass_original_many(self):
        class MySchema(Schema):
            foo = fields.Field()

            @post_load(pass_many=True, pass_original=True)
            def post_load(self, data, original, many, **kwargs):
                if many:
                    ret = []
                    for item, orig_item in zip(data, original):
                        item["_post_load"] = orig_item["sentinel"]
                        ret.append(item)
                else:
                    ret = data.copy()
                    ret["_post_load"] = original["sentinel"]
                return ret

            @post_dump(pass_many=True, pass_original=True)
            def post_dump(self, data, original, many, **kwargs):
                if many:
                    ret = []
                    for item, orig_item in zip(data, original):
                        item["_post_dump"] = orig_item["sentinel"]
                        ret.append(item)
                else:
                    ret = data.copy()
                    ret["_post_dump"] = original["sentinel"]
                return ret

        schema = MySchema(unknown=EXCLUDE)
        data = [{"foo": 42, "sentinel": 24}, {"foo": 424, "sentinel": 242}]
        items_loaded = schema.load(data, many=True)
        assert items_loaded == [
            {"foo": 42, "_post_load": 24},
            {"foo": 424, "_post_load": 242},
        ]
        test_values = [e["_post_load"] for e in items_loaded]
        assert test_values == [24, 242]

        items_dumped = schema.dump(data, many=True)
        assert items_dumped == [
            {"foo": 42, "_post_dump": 24},
            {"foo": 424, "_post_dump": 242},
        ]

        # Also check load/dump of single item

        datum = {"foo": 42, "sentinel": 24}
        item_loaded = schema.load(datum, many=False)
        assert item_loaded == {"foo": 42, "_post_load": 24}

        item_dumped = schema.dump(datum, many=False)
        assert item_dumped == {"foo": 42, "_post_dump": 24}


def test_decorated_processor_inheritance():
    class ParentSchema(Schema):
        @post_dump
        def inherited(self, item, **kwargs):
            item["inherited"] = "inherited"
            return item

        @post_dump
        def overridden(self, item, **kwargs):
            item["overridden"] = "base"
            return item

        @post_dump
        def deleted(self, item, **kwargs):
            item["deleted"] = "retained"
            return item

    class ChildSchema(ParentSchema):
        @post_dump
        def overridden(self, item, **kwargs):
            item["overridden"] = "overridden"
            return item

        deleted = None

    parent_dumped = ParentSchema().dump({})
    assert parent_dumped == {
        "inherited": "inherited",
        "overridden": "base",
        "deleted": "retained",
    }

    child_dumped = ChildSchema().dump({})
    assert child_dumped == {"inherited": "inherited", "overridden": "overridden"}


# https://github.com/marshmallow-code/marshmallow/issues/229#issuecomment-138949436
def test_pre_dump_is_invoked_before_implicit_field_generation():
    class Foo(Schema):
        field = fields.Integer()

        @pre_dump
        def hook(self, data, **kwargs):
            data["generated_field"] = 7
            return data

        class Meta:
            # Removing generated_field from here drops it from the output
            fields = ("field", "generated_field")

    assert Foo().dump({"field": 5}) == {"field": 5, "generated_field": 7}


class ValidatesSchema(Schema):
    foo = fields.Int()

    @validates("foo")
    def validate_foo(self, value):
        if value != 42:
            raise ValidationError("The answer to life the universe and everything.")


class TestValidatesDecorator:
    def test_validates(self):
        class VSchema(Schema):
            s = fields.String()

            @validates("s")
            def validate_string(self, data):
                raise ValidationError("nope")

        with pytest.raises(ValidationError) as excinfo:
            VSchema().load({"s": "bar"})

        assert excinfo.value.messages == {"s": ["nope"]}

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/350
    def test_validates_with_attribute(self):
        class S1(Schema):
            s = fields.String(attribute="string_name")

            @validates("s")
            def validate_string(self, data):
                raise ValidationError("nope")

        with pytest.raises(ValidationError) as excinfo:
            S1().load({"s": "foo"})
        assert excinfo.value.messages == {"s": ["nope"]}

        with pytest.raises(ValidationError):
            S1(many=True).load([{"s": "foo"}])

    def test_validates_decorator(self):
        schema = ValidatesSchema()

        errors = schema.validate({"foo": 41})
        assert "foo" in errors
        assert errors["foo"][0] == "The answer to life the universe and everything."

        errors = schema.validate({"foo": 42})
        assert errors == {}

        errors = schema.validate([{"foo": 42}, {"foo": 43}], many=True)
        assert "foo" in errors[1]
        assert len(errors[1]["foo"]) == 1
        assert errors[1]["foo"][0] == "The answer to life the universe and everything."

        errors = schema.validate([{"foo": 42}, {"foo": 42}], many=True)
        assert errors == {}

        errors = schema.validate({})
        assert errors == {}

        with pytest.raises(ValidationError) as excinfo:
            schema.load({"foo": 41})
        errors = excinfo.value.messages
        result = excinfo.value.valid_data
        assert errors
        assert result == {}

        with pytest.raises(ValidationError) as excinfo:
            schema.load([{"foo": 42}, {"foo": 43}], many=True)
        errors = excinfo.value.messages
        result = excinfo.value.valid_data
        assert len(result) == 2
        assert result[0] == {"foo": 42}
        assert result[1] == {}
        assert 1 in errors
        assert "foo" in errors[1]
        assert errors[1]["foo"] == ["The answer to life the universe and everything."]

    def test_field_not_present(self):
        class BadSchema(ValidatesSchema):
            @validates("bar")
            def validate_bar(self, value):
                raise ValidationError("Never raised.")

        schema = BadSchema()

        with pytest.raises(ValueError, match='"bar" field does not exist.'):
            schema.validate({"foo": 42})

    def test_precedence(self):
        class Schema2(ValidatesSchema):
            foo = fields.Int(validate=lambda n: n != 42)
            bar = fields.Int(validate=lambda n: n == 1)

            @validates("bar")
            def validate_bar(self, value):
                if value != 2:
                    raise ValidationError("Must be 2")

        schema = Schema2()

        errors = schema.validate({"foo": 42})
        assert "foo" in errors
        assert len(errors["foo"]) == 1
        assert "Invalid value." in errors["foo"][0]

        errors = schema.validate({"bar": 3})
        assert "bar" in errors
        assert len(errors["bar"]) == 1
        assert "Invalid value." in errors["bar"][0]

        errors = schema.validate({"bar": 1})
        assert "bar" in errors
        assert len(errors["bar"]) == 1
        assert errors["bar"][0] == "Must be 2"

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/748
    def test_validates_with_data_key(self):
        class BadSchema(Schema):
            foo = fields.String(data_key="foo-name")

            @validates("foo")
            def validate_string(self, data):
                raise ValidationError("nope")

        schema = BadSchema()
        errors = schema.validate({"foo-name": "data"})
        assert "foo-name" in errors
        assert errors["foo-name"] == ["nope"]

        schema = BadSchema()
        errors = schema.validate(
            [{"foo-name": "data"}, {"foo-name": "data2"}], many=True
        )
        assert errors == {0: {"foo-name": ["nope"]}, 1: {"foo-name": ["nope"]}}


class TestValidatesSchemaDecorator:
    def test_validator_nested_many_invalid_data(self):
        class NestedSchema(Schema):
            foo = fields.Int(required=True)

        class MySchema(Schema):
            nested = fields.Nested(NestedSchema, required=True, many=True)

        schema = MySchema()
        errors = schema.validate({"nested": [1]})
        assert errors
        assert "nested" in errors
        assert 0 in errors["nested"]
        assert errors["nested"][0] == {"_schema": ["Invalid input type."]}

    def test_validator_nested_many_schema_error(self):
        class NestedSchema(Schema):
            foo = fields.Int(required=True)

            @validates_schema
            def validate_schema(self, data, **kwargs):
                raise ValidationError("This will never work.")

        class MySchema(Schema):
            nested = fields.Nested(NestedSchema, required=True, many=True)

        schema = MySchema()
        errors = schema.validate({"nested": [{"foo": 1}]})
        assert errors
        assert "nested" in errors
        assert 0 in errors["nested"]
        assert errors["nested"][0] == {"_schema": ["This will never work."]}

    def test_validator_nested_many_field_error(self):
        class NestedSchema(Schema):
            foo = fields.Int(required=True)

            @validates_schema
            def validate_schema(self, data, **kwargs):
                raise ValidationError("This will never work.", "foo")

        class MySchema(Schema):
            nested = fields.Nested(NestedSchema, required=True, many=True)

        schema = MySchema()
        errors = schema.validate({"nested": [{"foo": 1}]})
        assert errors
        assert "nested" in errors
        assert 0 in errors["nested"]
        assert errors["nested"][0] == {"foo": ["This will never work."]}

    @pytest.mark.parametrize("data", ([{"foo": 1, "bar": 2}],))
    @pytest.mark.parametrize(
        "pass_many,expected_data,expected_original_data",
        (
            [True, [{"foo": 1}], [{"foo": 1, "bar": 2}]],
            [False, {"foo": 1}, {"foo": 1, "bar": 2}],
        ),
    )
    def test_validator_nested_many_pass_original_and_pass_many(
        self, pass_many, data, expected_data, expected_original_data
    ):
        class NestedSchema(Schema):
            foo = fields.Int(required=True)

            @validates_schema(pass_many=pass_many, pass_original=True)
            def validate_schema(self, data, original_data, many, **kwargs):
                assert data == expected_data
                assert original_data == expected_original_data
                assert many is True
                raise ValidationError("Method called")

        class MySchema(Schema):
            nested = fields.Nested(
                NestedSchema, required=True, many=True, unknown=EXCLUDE
            )

        schema = MySchema()
        errors = schema.validate({"nested": data})
        error = errors["nested"] if pass_many else errors["nested"][0]
        assert error["_schema"][0] == "Method called"

    def test_decorated_validators(self):
        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema
            def validate_schema(self, data, **kwargs):
                if data["foo"] <= 3:
                    raise ValidationError("Must be greater than 3")

            @validates_schema(pass_many=True)
            def validate_raw(self, data, many, **kwargs):
                if many:
                    assert type(data) is list
                    if len(data) < 2:
                        raise ValidationError("Must provide at least 2 items")

            @validates_schema
            def validate_bar(self, data, **kwargs):
                if "bar" in data and data["bar"] < 0:
                    raise ValidationError("bar must not be negative", "bar")

        schema = MySchema()
        errors = schema.validate({"foo": 3})
        assert "_schema" in errors
        assert errors["_schema"][0] == "Must be greater than 3"

        errors = schema.validate([{"foo": 4}], many=True)
        assert "_schema" in errors
        assert len(errors["_schema"]) == 1
        assert errors["_schema"][0] == "Must provide at least 2 items"

        errors = schema.validate({"foo": 4, "bar": -1})
        assert "bar" in errors
        assert len(errors["bar"]) == 1
        assert errors["bar"][0] == "bar must not be negative"

    def test_multiple_validators(self):
        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema
            def validate_schema(self, data, **kwargs):
                if data["foo"] <= 3:
                    raise ValidationError("Must be greater than 3")

            @validates_schema
            def validate_bar(self, data, **kwargs):
                if "bar" in data and data["bar"] < 0:
                    raise ValidationError("bar must not be negative")

        schema = MySchema()
        errors = schema.validate({"foo": 3, "bar": -1})
        assert type(errors) is dict
        assert "_schema" in errors
        assert len(errors["_schema"]) == 2
        assert "Must be greater than 3" in errors["_schema"]
        assert "bar must not be negative" in errors["_schema"]

        errors = schema.validate([{"foo": 3, "bar": -1}, {"foo": 3}], many=True)
        assert type(errors) is dict
        assert "_schema" in errors[0]
        assert len(errors[0]["_schema"]) == 2
        assert "Must be greater than 3" in errors[0]["_schema"]
        assert "bar must not be negative" in errors[0]["_schema"]
        assert len(errors[1]["_schema"]) == 1
        assert "Must be greater than 3" in errors[0]["_schema"]

    def test_multiple_validators_merge_dict_errors(self):
        class NestedSchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

        class MySchema(Schema):
            nested = fields.Nested(NestedSchema)

            @validates_schema
            def validate_nested_foo(self, data, **kwargs):
                raise ValidationError({"nested": {"foo": ["Invalid foo"]}})

            @validates_schema
            def validate_nested_bar_1(self, data, **kwargs):
                raise ValidationError({"nested": {"bar": ["Invalid bar 1"]}})

            @validates_schema
            def validate_nested_bar_2(self, data, **kwargs):
                raise ValidationError({"nested": {"bar": ["Invalid bar 2"]}})

        with pytest.raises(ValidationError) as excinfo:
            MySchema().load({"nested": {"foo": 1, "bar": 2}})

        assert excinfo.value.messages == {
            "nested": {
                "foo": ["Invalid foo"],
                "bar": ["Invalid bar 1", "Invalid bar 2"],
            }
        }

    def test_passing_original_data(self):
        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema(pass_original=True)
            def validate_original(self, data, original_data, partial, **kwargs):
                if isinstance(original_data, dict) and isinstance(
                    original_data["foo"], str
                ):
                    raise ValidationError("foo cannot be a string")

            @validates_schema(pass_many=True, pass_original=True)
            def validate_original_bar(self, data, original_data, many, **kwargs):
                def check(datum):
                    if isinstance(datum, dict) and isinstance(datum["bar"], str):
                        raise ValidationError("bar cannot be a string")

                if many:
                    for each in original_data:
                        check(each)
                else:
                    check(original_data)

        schema = MySchema()

        errors = schema.validate({"foo": "4", "bar": 12})
        assert errors["_schema"] == ["foo cannot be a string"]

        errors = schema.validate({"foo": 4, "bar": "42"})
        assert errors["_schema"] == ["bar cannot be a string"]

        errors = schema.validate([{"foo": 4, "bar": "42"}], many=True)
        assert errors["_schema"] == ["bar cannot be a string"]

    def test_allow_reporting_field_errors_in_schema_validator(self):
        class NestedSchema(Schema):
            baz = fields.Int(required=True)

        class MySchema(Schema):
            foo = fields.Int(required=True)
            bar = fields.Nested(NestedSchema, required=True)
            bam = fields.Int(required=True)

            @validates_schema(skip_on_field_errors=True)
            def consistency_validation(self, data, **kwargs):
                errors = {}
                if data["bar"]["baz"] != data["foo"]:
                    errors["bar"] = {"baz": "Non-matching value"}
                if data["bam"] > data["foo"]:
                    errors["bam"] = "Value should be less than foo"
                if errors:
                    raise ValidationError(errors)

        schema = MySchema()
        errors = schema.validate({"foo": 2, "bar": {"baz": 5}, "bam": 6})
        assert errors["bar"]["baz"] == "Non-matching value"
        assert errors["bam"] == "Value should be less than foo"

    # https://github.com/marshmallow-code/marshmallow/issues/273
    def test_allow_arbitrary_field_names_in_error(self):
        class MySchema(Schema):
            @validates_schema
            def validator(self, data, **kwargs):
                raise ValidationError("Error message", "arbitrary_key")

        errors = MySchema().validate({})
        assert errors["arbitrary_key"] == ["Error message"]

    def test_skip_on_field_errors(self):
        class MySchema(Schema):
            foo = fields.Int(required=True, validate=lambda n: n == 3)
            bar = fields.Int(required=True)

            @validates_schema(skip_on_field_errors=True)
            def validate_schema(self, data, **kwargs):
                if data["foo"] != data["bar"]:
                    raise ValidationError("Foo and bar must be equal.")

            @validates_schema(skip_on_field_errors=True, pass_many=True)
            def validate_many(self, data, many, **kwargs):
                if many:
                    assert type(data) is list
                    if len(data) < 2:
                        raise ValidationError("Must provide at least 2 items")

        schema = MySchema()
        # check that schema errors still occur with no field errors
        errors = schema.validate({"foo": 3, "bar": 4})
        assert "_schema" in errors
        assert errors["_schema"][0] == "Foo and bar must be equal."

        errors = schema.validate([{"foo": 3, "bar": 3}], many=True)
        assert "_schema" in errors
        assert errors["_schema"][0] == "Must provide at least 2 items"

        # check that schema errors don't occur when field errors do
        errors = schema.validate({"foo": 3, "bar": "not an int"})
        assert "bar" in errors
        assert "_schema" not in errors

        errors = schema.validate({"foo": 2, "bar": 2})
        assert "foo" in errors
        assert "_schema" not in errors

        errors = schema.validate([{"foo": 3, "bar": "not an int"}], many=True)
        assert "bar" in errors[0]
        assert "_schema" not in errors


def test_decorator_error_handling():  # noqa: C901
    class ExampleSchema(Schema):
        foo = fields.Int()
        bar = fields.Int()

        @pre_load()
        def pre_load_error1(self, item, **kwargs):
            if item["foo"] != 0:
                return item
            errors = {"foo": ["preloadmsg1"], "bar": ["preloadmsg2", "preloadmsg3"]}
            raise ValidationError(errors)

        @pre_load()
        def pre_load_error2(self, item, **kwargs):
            if item["foo"] != 4:
                return item
            raise ValidationError("preloadmsg1", "foo")

        @pre_load()
        def pre_load_error3(self, item, **kwargs):
            if item["foo"] != 8:
                return item
            raise ValidationError("preloadmsg1")

        @post_load()
        def post_load_error1(self, item, **kwargs):
            if item["foo"] != 1:
                return item
            errors = {"foo": ["postloadmsg1"], "bar": ["postloadmsg2", "postloadmsg3"]}
            raise ValidationError(errors)

        @post_load()
        def post_load_error2(self, item, **kwargs):
            if item["foo"] != 5:
                return item
            raise ValidationError("postloadmsg1", "foo")

        @pre_dump()
        def pre_dump_error1(self, item, **kwargs):
            if item["foo"] != 2:
                return item
            errors = {"foo": ["predumpmsg1"], "bar": ["predumpmsg2", "predumpmsg3"]}
            raise ValidationError(errors)

        @pre_dump()
        def pre_dump_error2(self, item, **kwargs):
            if item["foo"] != 6:
                return item
            raise ValidationError("predumpmsg1", "foo")

        @post_dump()
        def post_dump_error1(self, item, **kwargs):
            if item["foo"] != 3:
                return item
            errors = {"foo": ["postdumpmsg1"], "bar": ["postdumpmsg2", "postdumpmsg3"]}
            raise ValidationError(errors)

        @post_dump()
        def post_dump_error2(self, item, **kwargs):
            if item["foo"] != 7:
                return item
            raise ValidationError("postdumpmsg1", "foo")

    def make_item(foo, bar):
        data = schema.load({"foo": foo, "bar": bar})
        assert data is not None
        return data

    schema = ExampleSchema()
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"foo": 0, "bar": 1})
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "preloadmsg1"
    assert "bar" in errors
    assert len(errors["bar"]) == 2
    assert "preloadmsg2" in errors["bar"]
    assert "preloadmsg3" in errors["bar"]
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"foo": 1, "bar": 1})
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "postloadmsg1"
    assert "bar" in errors
    assert len(errors["bar"]) == 2
    assert "postloadmsg2" in errors["bar"]
    assert "postloadmsg3" in errors["bar"]
    with pytest.raises(ValidationError) as excinfo:
        schema.dump(make_item(2, 1))
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "predumpmsg1"
    assert "bar" in errors
    assert len(errors["bar"]) == 2
    assert "predumpmsg2" in errors["bar"]
    assert "predumpmsg3" in errors["bar"]
    with pytest.raises(ValidationError) as excinfo:
        schema.dump(make_item(3, 1))
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "postdumpmsg1"
    assert "bar" in errors
    assert len(errors["bar"]) == 2
    assert "postdumpmsg2" in errors["bar"]
    assert "postdumpmsg3" in errors["bar"]
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"foo": 4, "bar": 1})
    errors = excinfo.value.messages
    assert len(errors) == 1
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "preloadmsg1"
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"foo": 5, "bar": 1})
    errors = excinfo.value.messages
    assert len(errors) == 1
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "postloadmsg1"
    with pytest.raises(ValidationError) as excinfo:
        schema.dump(make_item(6, 1))
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "predumpmsg1"
    with pytest.raises(ValidationError) as excinfo:
        schema.dump(make_item(7, 1))
    errors = excinfo.value.messages
    assert "foo" in errors
    assert len(errors["foo"]) == 1
    assert errors["foo"][0] == "postdumpmsg1"
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"foo": 8, "bar": 1})
    errors = excinfo.value.messages
    assert len(errors) == 1
    assert "_schema" in errors
    assert len(errors["_schema"]) == 1
    assert errors["_schema"][0] == "preloadmsg1"


@pytest.mark.parametrize("decorator", [pre_load, post_load])
def test_decorator_error_handling_with_load(decorator):
    class ExampleSchema(Schema):
        @decorator
        def raise_value_error(self, item, **kwargs):
            raise ValidationError({"foo": "error"})

    schema = ExampleSchema()
    with pytest.raises(ValidationError) as exc:
        schema.load({})
    assert exc.value.messages == {"foo": "error"}
    schema.dump(object())


@pytest.mark.parametrize("decorator", [pre_load, post_load])
def test_decorator_error_handling_with_load_dict_error(decorator):
    class ExampleSchema(Schema):
        @decorator
        def raise_value_error(self, item, **kwargs):
            raise ValidationError({"foo": "error"}, "nested_field")

    schema = ExampleSchema()
    with pytest.raises(ValidationError) as exc:
        schema.load({})
    assert exc.value.messages == {"nested_field": {"foo": "error"}}
    schema.dump(object())


@pytest.mark.parametrize("decorator", [pre_dump, post_dump])
def test_decorator_error_handling_with_dump(decorator):
    class ExampleSchema(Schema):
        @decorator
        def raise_value_error(self, item, **kwargs):
            raise ValidationError({"foo": "error"})

    schema = ExampleSchema()
    with pytest.raises(ValidationError) as exc:
        schema.dump(object())
    assert exc.value.messages == {"foo": "error"}
    schema.load({})


@pytest.mark.parametrize("decorator", [pre_dump, post_dump])
def test_decorator_error_handling_with_dump_dict_error(decorator):
    class ExampleSchema(Schema):
        @decorator
        def raise_value_error(self, item, **kwargs):
            raise ValidationError({"foo": "error"}, "nested")

    schema = ExampleSchema()
    with pytest.raises(ValidationError) as exc:
        schema.dump(object())
    assert exc.value.messages == {"nested": {"foo": "error"}}
    schema.load({})


class Nested:
    def __init__(self, foo):
        self.foo = foo


class Example:
    def __init__(self, nested):
        self.nested = nested


example = Example(nested=[Nested(x) for x in range(1)])


@pytest.mark.parametrize(
    "data,expected_data,expected_original_data",
    ([example, {"foo": 0}, example.nested[0]],),
)
def test_decorator_post_dump_with_nested_original_and_pass_many(
    data, expected_data, expected_original_data
):
    class NestedSchema(Schema):
        foo = fields.Int(required=True)

        @post_dump(pass_many=False, pass_original=True)
        def check_pass_original_when_pass_many_false(
            self, data, original_data, **kwargs
        ):
            assert data == expected_data
            assert original_data == expected_original_data
            return data

        @post_dump(pass_many=True, pass_original=True)
        def check_pass_original_when_pass_many_true(
            self, data, original_data, many, **kwargs
        ):
            assert many is True
            assert data == [expected_data]
            assert original_data == [expected_original_data]
            return data

    class ExampleSchema(Schema):
        nested = fields.Nested(NestedSchema, required=True, many=True)

    schema = ExampleSchema()
    assert schema.dump(data) == {"nested": [{"foo": 0}]}


@pytest.mark.parametrize(
    "data,expected_data,expected_original_data",
    ([{"nested": [{"foo": 0}]}, {"foo": 0}, {"foo": 0}],),
)
def test_decorator_post_load_with_nested_original_and_pass_many(
    data, expected_data, expected_original_data
):
    class NestedSchema(Schema):
        foo = fields.Int(required=True)

        @post_load(pass_many=False, pass_original=True)
        def check_pass_original_when_pass_many_false(
            self, data, original_data, **kwargs
        ):
            assert data == expected_data
            assert original_data == expected_original_data
            return data

        @post_load(pass_many=True, pass_original=True)
        def check_pass_original_when_pass_many_true(
            self, data, original_data, many, **kwargs
        ):
            assert many is True
            assert data == [expected_data]
            assert original_data == [expected_original_data]
            return data

    class ExampleSchema(Schema):
        nested = fields.Nested(NestedSchema, required=True, many=True)

    schema = ExampleSchema()
    assert schema.load(data) == data
