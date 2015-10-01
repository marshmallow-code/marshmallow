# -*- coding: utf-8 -*-
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
)


def test_decorated_processors():
    class ExampleSchema(Schema):
        """Includes different ways to invoke decorators and set up methods"""

        TAG = 'TAG'

        value = fields.Integer(as_string=True)

        # Implicit default raw, pre dump, static method, return modified item.
        @pre_dump
        def increment_value(self, item):
            item['value'] += 1
            return item

        # Implicit default raw, post dump, class method, modify in place.
        @post_dump
        def add_tag(self, item):
            item['value'] = self.TAG + item['value']

        # Explicitly raw, post dump, instance method, return modified item.
        @post_dump(pass_many=True)
        def add_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return {key: data}

        # Explicitly raw, pre load, instance method, return modified item.
        @pre_load(pass_many=True)
        def remove_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return data[key]

        @staticmethod
        def get_envelope_key(many):
            return 'data' if many else 'datum'

        # Explicitly not raw, pre load, instance method, modify in place.
        @pre_load(pass_many=False)
        def remove_tag(self, item):
            item['value'] = item['value'][len(self.TAG):]

        # Explicit default raw, post load, instance method, modify in place.
        @post_load()
        def decrement_value(self, item):
            item['value'] -= 1

    schema = ExampleSchema()

    # Need to re-create these because the processors will modify in place.
    make_item = lambda: {'value': 3}
    make_items = lambda: [make_item(), {'value': 5}]

    item_dumped = schema.dump(make_item()).data
    assert item_dumped == {'datum': {'value': 'TAG4'}}
    item_loaded = schema.load(item_dumped).data
    assert item_loaded == make_item()

    items_dumped = schema.dump(make_items(), many=True).data
    assert items_dumped == {'data': [{'value': 'TAG4'}, {'value': 'TAG6'}]}
    items_loaded = schema.load(items_dumped, many=True).data
    assert items_loaded == make_items()

class TestPassOriginal:

    def test_pass_original_single_no_mutation(self):
        class MySchema(Schema):
            foo = fields.Field()

            @post_load(pass_original=True)
            def post_load(self, data, input_data):
                ret = data.copy()
                ret['_post_load'] = input_data['sentinel']
                return ret

            @post_dump(pass_original=True)
            def post_dump(self, data, obj):
                ret = data.copy()
                ret['_post_dump'] = obj['sentinel']
                return ret

        schema = MySchema()
        datum = {'foo': 42, 'sentinel': 24}
        item_loaded = schema.load(datum).data
        assert item_loaded['foo'] == 42
        assert item_loaded['_post_load'] == 24

        item_dumped = schema.dump(datum).data

        assert item_dumped['foo'] == 42
        assert item_dumped['_post_dump'] == 24

    def test_pass_original_single_with_mutation(self):
        class MySchema(Schema):
            foo = fields.Field()

            @post_load(pass_original=True)
            def post_load(self, data, input_data):
                data['_post_load'] = input_data['post_load']

        schema = MySchema()
        item_loaded = schema.load({'foo': 42, 'post_load': 24}).data
        assert item_loaded['foo'] == 42
        assert item_loaded['_post_load'] == 24

    def test_pass_original_many(self):
        class MySchema(Schema):
            foo = fields.Field()

            @post_load(pass_many=True, pass_original=True)
            def post_load(self, data, many, original):
                if many:
                    ret = []
                    for item, orig_item in zip(data, original):
                        item['_post_load'] = orig_item['sentinel']
                        ret.append(item)
                else:
                    ret = data.copy()
                    ret['_post_load'] = original['sentinel']
                return ret

            @post_dump(pass_many=True, pass_original=True)
            def post_dump(self, data, many, original):
                if many:
                    ret = []
                    for item, orig_item in zip(data, original):
                        item['_post_dump'] = orig_item['sentinel']
                        ret.append(item)
                else:
                    ret = data.copy()
                    ret['_post_dump'] = original['sentinel']
                return ret

        schema = MySchema()
        data = [{'foo': 42, 'sentinel': 24}, {'foo': 424, 'sentinel': 242}]
        items_loaded = schema.load(data, many=True).data
        assert items_loaded == [
            {'foo': 42, '_post_load': 24},
            {'foo': 424, '_post_load': 242},
        ]
        test_values = [e['_post_load'] for e in items_loaded]
        assert test_values == [24, 242]

        items_dumped = schema.dump(data, many=True).data
        assert items_dumped == [
            {'foo': 42, '_post_dump': 24},
            {'foo': 424, '_post_dump': 242},
        ]

        # Also check load/dump of single item

        datum = {'foo': 42, 'sentinel': 24}
        item_loaded = schema.load(datum, many=False).data
        assert item_loaded == {'foo': 42, '_post_load': 24}

        item_dumped = schema.dump(datum, many=False).data
        assert item_dumped == {'foo': 42, '_post_dump': 24}

def test_decorated_processor_inheritance():
    class ParentSchema(Schema):

        @post_dump
        def inherited(self, item):
            item['inherited'] = 'inherited'
            return item

        @post_dump
        def overridden(self, item):
            item['overridden'] = 'base'
            return item

        @post_dump
        def deleted(self, item):
            item['deleted'] = 'retained'
            return item

    class ChildSchema(ParentSchema):

        @post_dump
        def overridden(self, item):
            item['overridden'] = 'overridden'
            return item

        deleted = None

    parent_dumped = ParentSchema().dump({}).data
    assert parent_dumped == {
        'inherited': 'inherited',
        'overridden': 'base',
        'deleted': 'retained'
    }

    child_dumped = ChildSchema().dump({}).data
    assert child_dumped == {
        'inherited': 'inherited',
        'overridden': 'overridden'
    }

# https://github.com/marshmallow-code/marshmallow/issues/229#issuecomment-138949436
def test_pre_dump_is_invoked_before_implicit_field_generation():
    class Foo(Schema):
        field = fields.Integer()

        @pre_dump
        def hook(s, data):
            data['generated_field'] = 7

        class Meta:
            # Removing generated_field from here drops it from the output
            fields = ('field', 'generated_field')

    assert Foo().dump({"field": 5}).data == {'field': 5, 'generated_field': 7}


class ValidatesSchema(Schema):
    foo = fields.Int()

    @validates('foo')
    def validate_foo(self, value):
        if value != 42:
            raise ValidationError('The answer to life the universe and everything.')

class TestValidatesDecorator:

    def test_validates_decorator(self):
        schema = ValidatesSchema()

        errors = schema.validate({'foo': 41})
        assert 'foo' in errors
        assert errors['foo'][0] == 'The answer to life the universe and everything.'

        errors = schema.validate({'foo': 42})
        assert errors == {}

        errors = schema.validate([{'foo': 42}, {'foo': 43}], many=True)
        assert 'foo' in errors[1]
        assert len(errors[1]['foo']) == 1
        assert errors[1]['foo'][0] == 'The answer to life the universe and everything.'

        errors = schema.validate([{'foo': 42}, {'foo': 42}], many=True)
        assert errors == {}

        errors = schema.validate({})
        assert errors == {}

    def test_field_not_present(self):
        class BadSchema(ValidatesSchema):
            @validates('bar')
            def validate_bar(self, value):
                raise ValidationError('Never raised.')

        schema = BadSchema()

        with pytest.raises(ValueError) as excinfo:
            schema.validate({'foo': 42})
        assert '"bar" field does not exist.' in str(excinfo)

    def test_precedence(self):
        class Schema2(ValidatesSchema):
            foo = fields.Int(validate=lambda n: n != 42)
            bar = fields.Int(validate=lambda n: n == 1)

            @validates('bar')
            def validate_bar(self, value):
                if value != 2:
                    raise ValidationError('Must be 2')

        schema = Schema2()

        errors = schema.validate({'foo': 42})
        assert 'foo' in errors
        assert len(errors['foo']) == 1
        assert 'Invalid value.' in errors['foo'][0]

        errors = schema.validate({'bar': 3})
        assert 'bar' in errors
        assert len(errors['bar']) == 1
        assert 'Invalid value.' in errors['bar'][0]

        errors = schema.validate({'bar': 1})
        assert 'bar' in errors
        assert len(errors['bar']) == 1
        assert errors['bar'][0] == 'Must be 2'


class TestValidatesSchemaDecorator:

    def test_decorated_validators(self):

        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema
            def validate_schema(self, data):
                if data['foo'] <= 3:
                    raise ValidationError('Must be greater than 3')

            @validates_schema(pass_many=True)
            def validate_raw(self, data, many):
                if many:
                    if len(data) < 2:
                        raise ValidationError('Must provide at least 2 items')

            @validates_schema
            def validate_bar(self, data):
                if 'bar' in data and data['bar'] < 0:
                    raise ValidationError('bar must not be negative', 'bar')

        schema = MySchema()
        errors = schema.validate({'foo': 3})
        assert '_schema' in errors
        assert errors['_schema'][0] == 'Must be greater than 3'

        errors = schema.validate([{'foo': 4}], many=True)
        assert '_schema' in errors[0]
        assert len(errors[0]['_schema']) == 1
        assert errors[0]['_schema'][0] == 'Must provide at least 2 items'

        errors = schema.validate({'foo': 4, 'bar': -1})
        assert 'bar' in errors
        assert len(errors['bar']) == 1
        assert errors['bar'][0] == 'bar must not be negative'

    def test_multiple_validators(self):

        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema
            def validate_schema(self, data):
                if data['foo'] <= 3:
                    raise ValidationError('Must be greater than 3')

            @validates_schema
            def validate_bar(self, data):
                if 'bar' in data and data['bar'] < 0:
                    raise ValidationError('bar must not be negative')

        schema = MySchema()
        errors = schema.validate({'foo': 3, 'bar': -1})
        assert len(errors) == 1
        assert '_schema' in errors
        assert len(errors['_schema']) == 2
        assert 'Must be greater than 3' in errors['_schema']
        assert 'bar must not be negative' in errors['_schema']

        errors = schema.validate([{'foo': 3, 'bar': -1}, {'foo': 3}], many=True)
        assert len(errors) == 2
        assert '_schema' in errors[0]
        assert len(errors[0]['_schema']) == 2
        assert 'Must be greater than 3' in errors[0]['_schema']
        assert 'bar must not be negative' in errors[0]['_schema']
        assert len(errors[1]['_schema']) == 1
        assert 'Must be greater than 3' in errors[0]['_schema']

    def test_passing_original_data(self):

        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema(pass_original=True)
            def validate_original(self, data, original_data):
                if isinstance(original_data, dict) and isinstance(original_data['foo'], str):
                    raise ValidationError('foo cannot be a string')

            # See https://github.com/marshmallow-code/marshmallow/issues/127
            @validates_schema(pass_many=True, pass_original=True)
            def check_unknown_fields(self, data, original_data, many):
                def check(datum):
                    for key, val in datum.items():
                        if key not in self.fields:
                            raise ValidationError({'code': 'invalid_field'})
                if many:
                    for each in original_data:
                        check(each)
                else:
                    check(original_data)

        schema = MySchema()
        errors = schema.validate({'foo': 4, 'baz': 42})
        assert '_schema' in errors
        assert len(errors['_schema']) == 1
        assert errors['_schema'][0] == {'code': 'invalid_field'}

        errors = schema.validate({'foo': '4'})
        assert '_schema' in errors
        assert len(errors['_schema']) == 1
        assert errors['_schema'][0] == 'foo cannot be a string'

        schema = MySchema()
        errors = schema.validate([{'foo': 4, 'baz': 42}], many=True)
        assert 0 in errors
        assert '_schema' in errors[0]
        assert len(errors[0]['_schema']) == 1
        assert errors[0]['_schema'][0] == {'code': 'invalid_field'}

    # https://github.com/marshmallow-code/marshmallow/issues/273
    def test_allow_arbitrary_field_names_in_error(self):

        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema(pass_original=True)
            def strict_fields(self, data, original_data):
                for key in original_data:
                    if key not in self.fields:
                        raise ValidationError('Unknown field name', key)

        schema = MySchema()
        errors = schema.validate({'foo': 2, 'baz': 42})
        assert 'baz' in errors
        assert len(errors['baz']) == 1
        assert errors['baz'][0] == 'Unknown field name'
