# -*- coding: utf-8 -*-


from marshmallow import Serializer, Schema
from tests.base import UserSchema

def test_serializer_alias():
    assert Serializer is Schema

def test_serializing_through_contructor(user):
    s = UserSchema(user)
    assert s.data['name'] == user.name

def test_errors_property(user):
    user.age = 'invalid age'
    s = UserSchema(user)
    assert 'age' in s.errors
