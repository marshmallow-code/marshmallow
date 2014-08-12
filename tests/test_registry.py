# -*- coding: utf-8 -*-

import pytest

from marshmallow import Serializer, fields, class_registry
from marshmallow.exceptions import RegistryError


def test_serializer_has_class_registry():
    class MySerializer(Serializer):
        pass

    class MySubSerializer(Serializer):
        pass

    assert 'MySerializer' in class_registry._registry
    assert 'MySubSerializer' in class_registry._registry


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

class ASerializer(Serializer):
    id = fields.Integer()
    b = fields.Nested('BSerializer', exclude=('a', ))

class BSerializer(Serializer):
    id = fields.Integer()
    a = fields.Nested('ASerializer')

class CSerializer(Serializer):
    id = fields.Integer()
    bs = fields.Nested('BSerializer', many=True)

def test_two_way_nesting():
    a_obj = A(1)
    b_obj = B(2, a=a_obj)
    a_obj.b = b_obj

    a_serialized = ASerializer(a_obj)
    b_serialized = BSerializer(b_obj)

    assert a_serialized.data['b']['id'] == b_obj.id
    assert b_serialized.data['a']['id'] == a_obj.id

def test_nesting_with_class_name_many():
    c_obj = C(1, bs=[B(2), B(3), B(4)])

    c_serialized = CSerializer(c_obj)

    assert len(c_serialized.data['bs']) == len(c_obj.bs)
    assert c_serialized.data['bs'][0]['id'] == c_obj.bs[0].id

def test_invalid_class_name_in_nested_field_raises_error(user):
    with pytest.raises(RegistryError) as excinfo:
        fields.Nested('notfound').serialize('foo', user)

    assert 'Class with name {0!r} was not found'.format('notfound') in str(excinfo)

class FooSerializer(Serializer):
    _id = fields.Integer()


def test_multiple_classes_with_same_name_raises_error():
    # Import a class with the same name
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    # Using a nested field with the class name fails because there are
    # two defined classes with the same name
    with pytest.raises(RegistryError) as excinfo:
        field = fields.Nested('FooSerializer')
        field.serialize('bar', {})
    msg = 'Multiple classes with name {0!r} were found.'\
            .format('FooSerializer')
    assert msg in str(excinfo)


def test_can_use_full_module_path_to_class():
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa
    # Using full paths is ok
    field = fields.Nested('tests.foo_serializer.FooSerializer')

    # Note: The arguments here don't matter. What matters is that no
    # error is raised
    assert field.serialize('bar', {'foo': {'_id': 42}})

    field2 = fields.Nested('tests.test_registry.FooSerializer')

    assert field2.serialize('bar', {'foo': {'_id': 42}})
