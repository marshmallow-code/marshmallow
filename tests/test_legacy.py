# -*- coding: utf-8 -*-

import pytest

from marshmallow import Serializer, Schema
from tests.base import UserSchema, User, UserMetaSchema

def test_serializer_alias():
    assert Serializer is Schema

def test_serializing_through_contructor(user):
    s = UserSchema(user)
    assert s.data['name'] == user.name

def test_validate(recwarn):
    valid = User("Joe", email="joe@foo.com")
    invalid = User("John", email="johnexample.com")
    assert UserSchema(valid).is_valid()
    assert UserSchema(invalid).is_valid() is False
    warning = recwarn.pop()
    assert issubclass(warning.category, DeprecationWarning)

@pytest.mark.parametrize('SerializerClass',
    [UserSchema, UserMetaSchema])
def test_validate_field(SerializerClass):
    invalid = User("John", email="johnexample.com")
    assert SerializerClass(invalid).is_valid(["name"]) is True
    assert SerializerClass(invalid).is_valid(["email"]) is False

def test_validating_nonexistent_field_raises_error(user):
    ser_user = UserSchema(user)
    with pytest.raises(KeyError):
        ser_user.is_valid(["foobar"])
