# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, pre_dump, post_dump, pre_load, post_load

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
