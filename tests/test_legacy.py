# -*- coding: utf-8 -*-

import pytest

from tests.base import UserSerializer, User, UserMetaSerializer


def test_serializing_through_contructor(user):
    s = UserSerializer(user)
    assert s.data['name'] == user.name

def test_validate():
    valid = User("Joe", email="joe@foo.com")
    invalid = User("John", email="johnexample.com")
    assert UserSerializer(valid).is_valid()
    assert UserSerializer(invalid).is_valid() is False

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_validate_field(SerializerClass):
    invalid = User("John", email="johnexample.com")
    assert SerializerClass(invalid).is_valid(["name"]) is True
    assert SerializerClass(invalid).is_valid(["email"]) is False

def test_validating_nonexistent_field_raises_error(user):
    ser_user = UserSerializer(user)
    with pytest.raises(KeyError):
        ser_user.is_valid(["foobar"])
