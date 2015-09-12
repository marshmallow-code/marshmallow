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
        @staticmethod
        def increment_value(item):
            item['value'] += 1
            return item

        # Implicit default raw, post dump, class method, modify in place.
        @post_dump
        @classmethod
        def add_tag(cls, item):
            item['value'] = cls.TAG + item['value']

        # Explicitly raw, post dump, instance method, return modified item.
        @post_dump(raw=True)
        def add_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return {key: data}

        # Explicitly raw, pre load, instance method, return modified item.
        @pre_load(raw=True)
        def remove_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return data[key]

        @staticmethod
        def get_envelope_key(many):
            return 'data' if many else 'datum'

        # Explicitly not raw, pre load, instance method, modify in place.
        @pre_load(raw=False)
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


def test_decorated_processor_inheritance():
    class ParentSchema(Schema):
        @post_dump
        @staticmethod
        def inherited(item):
            item['inherited'] = 'inherited'
            return item

        @post_dump
        @staticmethod
        def overridden(item):
            item['overridden'] = 'base'
            return item

        @post_dump
        @staticmethod
        def deleted(item):
            item['deleted'] = 'retained'
            return item

    class ChildSchema(ParentSchema):
        @post_dump
        @staticmethod
        def overridden(item):
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


class TestValidatesDecorator:

    class MySchema(Schema):
        foo = fields.Int()

        @validates('foo')
        def validate_foo(self, value):
            if value != 42:
                raise ValidationError('The answer to life the universe and everything.')

    def test_decorator(self):
        schema = self.MySchema()

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
        class BadSchema(self.MySchema):
            @validates('bar')
            def validate_bar(self, value):
                raise ValidationError('Never raised.')

        schema = BadSchema()

        with pytest.raises(ValueError) as excinfo:
            errors = schema.validate({'foo': 42})
        assert '"bar" field does not exist.' in str(excinfo)

    def test_precedence(self):
        class Schema2(self.MySchema):
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

            @validates_schema(raw=True)
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

    def test_passing_original_data(self):

        class MySchema(Schema):
            foo = fields.Int()
            bar = fields.Int()

            @validates_schema(pass_original=True)
            def validate_original(self, data, original_data):
                if isinstance(original_data, dict) and isinstance(original_data['foo'], str):
                    raise ValidationError('foo cannot be a string')

            # See https://github.com/marshmallow-code/marshmallow/issues/127
            @validates_schema(raw=True, pass_original=True)
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
