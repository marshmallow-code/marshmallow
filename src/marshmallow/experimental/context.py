"""Helper API for setting serialization/deserialization context."""

import contextlib
import contextvars
import typing

_T = typing.TypeVar("_T")
_CURRENT_CONTEXT: contextvars.ContextVar = contextvars.ContextVar("context")


class Context(contextlib.AbstractContextManager, typing.Generic[_T]):
    def __init__(self, context: _T) -> None:
        self.context = context

    def __enter__(self) -> None:
        self.token = _CURRENT_CONTEXT.set(self.context)

    def __exit__(self, *args, **kwargs) -> None:
        _CURRENT_CONTEXT.reset(self.token)

    @classmethod
    def get(cls, default=...) -> _T:
        if default is not ...:
            return _CURRENT_CONTEXT.get(default)
        return _CURRENT_CONTEXT.get()
