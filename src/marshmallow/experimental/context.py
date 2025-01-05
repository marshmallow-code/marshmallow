"""Helper API for setting serialization/deserialization context.

Example usage:

.. code-block:: python

    import typing

    from marshmallow import Schema, fields
    from marshmallow.experimental.context import Context


    class UserContext(typing.TypedDict):
        suffix: str


    class UserSchema(Schema):
        name_suffixed = fields.Function(
            lambda user: user["name"] + Context[UserContext].get()["suffix"]
        )


    with Context[UserContext]({"suffix": "bar"}):
        print(UserSchema().dump({"name": "foo"}))
        # {'name_suffixed': 'foobar'}
"""

import contextlib
import contextvars
import typing

_T = typing.TypeVar("_T")
_CURRENT_CONTEXT: contextvars.ContextVar = contextvars.ContextVar("context")


class Context(contextlib.AbstractContextManager, typing.Generic[_T]):
    """Context manager for setting and retrieving context."""

    def __init__(self, context: _T) -> None:
        self.context = context
        self.token: contextvars.Token | None = None

    def __enter__(self) -> None:
        self.token = _CURRENT_CONTEXT.set(self.context)

    def __exit__(self, *args, **kwargs) -> None:
        _CURRENT_CONTEXT.reset(typing.cast(contextvars.Token, self.token))

    @classmethod
    def get(cls, default=...) -> _T:
        """Get the current context.

        :param default: Default value to return if no context is set.
            If not provided and no context is set, a :exc:`LookupError` is raised.
        """
        if default is not ...:
            return _CURRENT_CONTEXT.get(default)
        return _CURRENT_CONTEXT.get()
