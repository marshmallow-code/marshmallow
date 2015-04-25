# -*- coding: utf-8 -*-

import pytest

from marshmallow import Schema, fields, class_registry
from marshmallow.exceptions import RegistryError


def test_serializer_has_class_registry():
    class MySchema(Schema):
        pass

    class MySubSchema(Schema):
        pass

    assert 'MySchema' in class_registry._registry
    assert 'MySubSchema' in class_registry._registry


class A:

    def __init__(self, _id, b=None):
        self.id = _id
        self.b = b

class B:

    def __init__(self, _id, a=None):
        self.id = _id
        self.a = a


class C:

    def __init__(self, _id, bs=None):
        self.id = _id
        self.bs = bs or []

class ASchema(Schema):
    id = fields.Integer()
    b = fields.Nested('BSchema', exclude=('a', ))

class BSchema(Schema):
    id = fields.Integer()
    a = fields.Nested('ASchema')

class CSchema(Schema):
    id = fields.Integer()
    bs = fields.Nested('BSchema', many=True)

def test_two_way_nesting():
    a_obj = A(1)
    b_obj = B(2, a=a_obj)
    a_obj.b = b_obj

    a_serialized = ASchema().dump(a_obj)
    b_serialized = BSchema().dump(b_obj)
    assert a_serialized.data['b']['id'] == b_obj.id
    assert b_serialized.data['a']['id'] == a_obj.id

def test_nesting_with_class_name_many():
    c_obj = C(1, bs=[B(2), B(3), B(4)])

    c_serialized = CSchema().dump(c_obj)

    assert len(c_serialized.data['bs']) == len(c_obj.bs)
    assert c_serialized.data['bs'][0]['id'] == c_obj.bs[0].id

def test_invalid_class_name_in_nested_field_raises_error(user):

    class MySchema(Schema):
        nf = fields.Nested('notfound')
    sch = MySchema()
    with pytest.raises(RegistryError) as excinfo:
        sch.dump({'nf': None})
    assert 'Class with name {0!r} was not found'.format('notfound') in str(excinfo)

class FooSerializer(Schema):
    _id = fields.Integer()


def test_multiple_classes_with_same_name_raises_error():
    # Import a class with the same name
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    class MySchema(Schema):
        foo = fields.Nested('FooSerializer')

    # Using a nested field with the class name fails because there are
    # two defined classes with the same name
    sch = MySchema()
    with pytest.raises(RegistryError) as excinfo:
        sch.dump({'foo': {'_id': 1}})
    msg = 'Multiple classes with name {0!r} were found.'\
            .format('FooSerializer')
    assert msg in str(excinfo)

def test_multiple_classes_with_all():
    # Import a class with the same name
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    classes = class_registry.get_class('FooSerializer', all=True)
    assert len(classes) == 2


def test_can_use_full_module_path_to_class():
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa
    # Using full paths is ok

    class Schema1(Schema):
        foo = fields.Nested('tests.foo_serializer.FooSerializer')

    sch = Schema1()

    # Note: The arguments here don't matter. What matters is that no
    # error is raised
    assert sch.dump({'foo': {'_id': 42}}).data

    class Schema2(Schema):
        foo = fields.Nested('tests.test_registry.FooSerializer')
    sch = Schema2()
    assert sch.dump({'foo': {'_id': 42}}).data
