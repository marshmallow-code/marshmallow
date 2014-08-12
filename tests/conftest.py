# -*- coding: utf-8 -*-
import pytest

from tests.base import User, UserSerializer

@pytest.fixture
def user():
    return User(name="Monty", age=42.3, homepage="http://monty.python.org/")

@pytest.fixture
def serialized_user(user):
    return UserSerializer(user)
