"""Helper API for setting serialization/deserialization context.

Example usage:

.. code-block:: python

    import typing

    from marshmallow import Schema, fields
    from marshmallow.experimental.context import Context


    class UserContext(typing.TypedDict):
        suffix: str


    UserSchemaContext = Context[UserContext]


    class UserSchema(Schema):
        name_suffixed = fields.Function(
            lambda user: user["name"] + UserSchemaContext.get()["suffix"]
        )


    with UserSchemaContext({"suffix": "bar"}):
        print(UserSchema().dump({"name": "foo"}))
        # {'name_suffixed': 'foobar'}
"""

from __future__ import annotations

import contextlib
import contextvars
import typing

try:
    from types import EllipsisType
except ImportError:  # Python<3.10
    EllipsisType = type(Ellipsis)  # type: ignore[misc]

_ContextT = typing.TypeVar("_ContextT")
_DefaultT = typing.TypeVar("_DefaultT")
_CURRENT_CONTEXT: contextvars.ContextVar = contextvars.ContextVar("context")


class Context(contextlib.AbstractContextManager, typing.Generic[_ContextT]):
    """Context manager for setting and retrieving context.

    :param context: The context to use within the context manager scope.
    """

    def __init__(self, context: _ContextT) -> None:
        self.context = context
        self.token: contextvars.Token | None = None

    def __enter__(self) -> Context[_ContextT]:
        self.token = _CURRENT_CONTEXT.set(self.context)
        return self

    def __exit__(self, *args, **kwargs) -> None:
        _CURRENT_CONTEXT.reset(typing.cast("contextvars.Token", self.token))

    @classmethod
    def get(cls, default: _DefaultT | EllipsisType = ...) -> _ContextT | _DefaultT:
        """Get the current context.

        :param default: Default value to return if no context is set.
            If not provided and no context is set, a :exc:`LookupError` is raised.
        """
        if default is not ...:
            return _CURRENT_CONTEXT.get(default)
        return _CURRENT_CONTEXT.get()
