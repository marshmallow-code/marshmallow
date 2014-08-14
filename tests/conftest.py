# -*- coding: utf-8 -*-
"""Pytest fixtures that are available in all test modules."""
import pytest

from tests.base import User, UserSerializer

@pytest.fixture
def user():
    return User(name="Monty", age=42.3, homepage="http://monty.python.org/")

@pytest.fixture
def serialized_user(user):
    return UserSerializer().dump(user)
