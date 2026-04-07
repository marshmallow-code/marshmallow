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
_CONTEXT_CLASSES: dict[typing.Any, type] = {}


class Context(contextlib.AbstractContextManager, typing.Generic[_ContextT]):
    """Context manager for setting and retrieving context.

    :param context: The context to use within the context manager scope.
    """

    _context_var: typing.ClassVar[contextvars.ContextVar] = _CURRENT_CONTEXT

    def __class_getitem__(cls, item):
        if isinstance(item, typing.TypeVar):
            return super().__class_getitem__(item)
        if item not in _CONTEXT_CLASSES:
            ctx_var = contextvars.ContextVar(
                f"context_{getattr(item, '__name__', repr(item))}"
            )
            _CONTEXT_CLASSES[item] = type(
                f"{cls.__name__}[{getattr(item, '__name__', repr(item))}]",
                (cls,),
                {"_context_var": ctx_var},
            )
        return _CONTEXT_CLASSES[item]

    def __init__(self, context: _ContextT) -> None:
        self.context = context
        self.token: contextvars.Token | None = None

    def __enter__(self) -> Context[_ContextT]:
        self.token = self._context_var.set(self.context)
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self._context_var.reset(typing.cast("contextvars.Token", self.token))

    @classmethod
    def get(cls, default: _DefaultT | EllipsisType = ...) -> _ContextT | _DefaultT:
        """Get the current context.

        :param default: Default value to return if no context is set.
            If not provided and no context is set, a :exc:`LookupError` is raised.
        """
        if default is not ...:
            return cls._context_var.get(default)
        return cls._context_var.get()
