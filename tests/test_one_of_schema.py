import marshmallow as m
import marshmallow.fields as f
import unittest


REQUIRED_ERROR = u'Missing data for required field.'


class Foo(object):
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return '<Foo value=%s>' % self.value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value


class FooSchema(m.Schema):
    value = f.String(required=True)

    @m.post_load
    def make_foo(self, data):
        return Foo(**data)


class Bar(object):
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return '<Bar value=%s>' % self.value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value


class BarSchema(m.Schema):
    value = f.Integer(required=True)

    @m.post_load
    def make_bar(self, data):
        return Bar(**data)


class MySchema(m.OneOfSchema):
    type_schemas = {
        'Foo': FooSchema,
        'Bar': BarSchema,
    }


class TestOneOfSchema:
    def test_dump(self):
        foo_result = MySchema().dump(Foo('hello'))
        assert {'type': 'Foo', 'value': 'hello'} == foo_result.data
        assert {} == foo_result.errors

        bar_result = MySchema().dump(Bar(123))
        assert {'type': 'Bar', 'value': 123} == bar_result.data
        assert {} == bar_result.errors

    def test_dump_many(self):
        result = MySchema().dump([Foo('hello'), Bar(123)], many=True)
        assert [{'type': 'Foo', 'value': 'hello'},
                {'type': 'Bar', 'value': 123}] == result.data
        assert {} == result.errors

    def test_load(self):
        foo_result = MySchema().load({'type': 'Foo', 'value': 'world'})
        assert Foo('world') == foo_result.data
        assert {} == foo_result.errors

        bar_result = MySchema().load({'type': 'Bar', 'value': 456})
        assert Bar(456) == bar_result.data
        assert {} == bar_result.errors

    def test_load_many(self):
        result = MySchema().load([
            {'type': 'Foo', 'value': 'hello world!'},
            {'type': 'Bar', 'value': 123},
        ], many=True)
        assert [Foo('hello world!'), Bar(123)] == result.data
        assert {} == result.errors

    def test_load_errors_no_type(self):
        result = MySchema().load({'value': 'Foo'})
        assert {'type': [REQUIRED_ERROR]} == result.errors

    def test_load_errors_field_error(self):
        result = MySchema().load({'type': 'Foo'})
        assert {'value': [REQUIRED_ERROR]} == result.errors

    def test_load_many_errors_are_indexed_by_object_position(self):
        result = MySchema().load([
            {'type': 'Foo'},
            {'type': 'Bar', 'value': 123},
        ], many=True)
        assert {0: {'value': [REQUIRED_ERROR]}} == result.errors

    def test_validate(self):
        assert {} == MySchema().validate({'type': 'Foo', 'value': '123'})
        assert {'value': [REQUIRED_ERROR]} == MySchema().validate({'type': 'Bar'})

    def test_validate_many(self):
        errors = MySchema().validate([
            {'type': 'Foo', 'value': '123'},
            {'type': 'Bar', 'value': 123},
        ], many=True)
        assert {} == errors

        errors = MySchema().validate([
            {'value': '123'},
            {'type': 'Bar'},
        ], many=True)
        assert {0: {'type': [REQUIRED_ERROR]},
                1: {'value': [REQUIRED_ERROR]}} == errors

    def test_using_as_nested_schema(self):
        class SchemaWithList(m.Schema):
            items = f.List(f.Nested(MySchema))

        schema = SchemaWithList()
        result = schema.load({'items': [
            {'type': 'Foo', 'value': 'hello world!'},
            {'type': 'Bar', 'value': 123},
        ]})
        assert {'items': [Foo('hello world!'), Bar(123)]} == result.data
        assert {} == result.errors

        result = schema.load({'items': [
            {'type': 'Foo', 'value': 'hello world!'},
            {'value': 123},
        ]})
        assert {'items': {1: {'type': [REQUIRED_ERROR]}}} == result.errors

    def test_using_custom_type_names(self):
        class MyCustomTypeNameSchema(m.OneOfSchema):
            type_schemas = {
                'baz': FooSchema,
                'bam': BarSchema,
            }

            def get_obj_type(self, obj):
                return {'Foo': 'baz', 'Bar': 'bam'}.get(obj.__class__.__name__)

        schema = MyCustomTypeNameSchema()
        data = [Foo('hello'), Bar(111)]
        marshalled = schema.dump(data, many=True)
        assert [{'type': 'baz', 'value': 'hello'},
                {'type': 'bam', 'value': 111}] == marshalled.data
        assert {} == marshalled.errors

        unmarshalled = schema.load(marshalled.data, many=True)
        assert data == unmarshalled.data
        assert {} == unmarshalled.errors

    def test_using_custom_type_field(self):
        class MyCustomTypeFieldSchema(MySchema):
            type_field = 'object_type'

        schema = MyCustomTypeFieldSchema()
        data = [Foo('hello'), Bar(111)]
        marshalled = schema.dump(data, many=True)
        assert [{'object_type': 'Foo', 'value': 'hello'},
                {'object_type': 'Bar', 'value': 111}] == marshalled.data
        assert {} == marshalled.errors

        unmarshalled = schema.load(marshalled.data, many=True)
        assert data == unmarshalled.data
        assert {} == unmarshalled.errors
