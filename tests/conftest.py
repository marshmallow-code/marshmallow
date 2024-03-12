"""Pytest fixtures that are available in all test modules."""

import pytest

from tests.base import Blog, User, UserSchema


@pytest.fixture
def user():
    return User(name="Monty", age=42.3, homepage="http://monty.python.org/")


@pytest.fixture
def blog(user):
    col1 = User(name="Mick", age=123)
    col2 = User(name="Keith", age=456)
    return Blog(
        "Monty's blog",
        user=user,
        categories=["humor", "violence"],
        collaborators=[col1, col2],
    )


@pytest.fixture
def serialized_user(user):
    return UserSchema().dump(user)
